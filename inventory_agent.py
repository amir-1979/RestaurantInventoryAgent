# inventory_agent.py
# -------------------------------------------------------------------
# Restaurant inventory analyzer:
# - Custom boto3 Session (env or profile)
# - Strands + Amazon Bedrock (text-only prompt for widest model support)
# - Reads local CSV, finds expirations, writes Markdown report + CSV slices
# -------------------------------------------------------------------

import os
import io
import uuid
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

import boto3
from botocore.config import Config

# Strands (LLM agent) imports
from strands import Agent
from strands.models import BedrockModel


# =========================
# Configuration & Defaults
# =========================
load_dotenv()  # loads .env if present

# Choose ONE: env vars or profile.
AWS_PROFILE = os.getenv("AWS_PROFILE")  # optional, e.g., "default" or "kiro"
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# If you have static or temporary creds in env, these will be used first:
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_SESSION_TOKEN = os.getenv("AWS_SESSION_TOKEN")  # optional (for temp creds)

# Pick a Bedrock model you have access to; override via env if needed.
# Example commonly available ID: "anthropic.claude-3-5-sonnet-20240620-v1:0"
BEDROCK_MODEL_ID = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-5-sonnet-20240620-v1:0")

# File paths (override via env if desired)
INVENTORY_CSV_PATH = os.getenv("INVENTORY_CSV_PATH", "inventory.csv")
OUTPUT_REPORT_PATH = os.getenv("OUTPUT_REPORT_PATH", "inventory_analysis_report.md")

# Your analysis instruction for the model
USER_PROMPT = os.getenv(
    "USER_PROMPT",
    (
        "You are a restaurant inventory analyst. Using the data below, "
        "1) list items already expired, 2) items expiring within 7 days, "
        "3) items with sufficient shelf life, 4) actionable recommendations "
        "(e.g., discounting, menu specials, reorder timing, storage tips). "
        "Return a concise, well-structured Markdown report with clear tables."
    ),
)

# =========================
# Helpers
# =========================
def build_session() -> boto3.Session:
    """
    Build an explicit boto3 Session to avoid falling back to a broken default profile.
    Priority:
      1) Explicit env vars (AK/SK[/ST])
      2) AWS_PROFILE (if provided)
      3) Otherwise raise a friendly error
    """
    if AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY:
        return boto3.Session(
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            aws_session_token=AWS_SESSION_TOKEN,
            region_name=AWS_REGION,
        )

    if AWS_PROFILE:
        return boto3.Session(profile_name=AWS_PROFILE, region_name=AWS_REGION)

    # Last resort: let default provider chain resolve (may hit a broken default profile).
    # Safer to fail fast with a clear message:
    raise RuntimeError(
        "No complete AWS credentials found. Either set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY "
        "in your environment/.env, or set AWS_PROFILE to a valid profile."
    )


def load_inventory(csv_path: str) -> tuple[pd.DataFrame, str]:
    """Load CSV and detect expiration column."""
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV not found at: {csv_path}")

    df = pd.read_csv(csv_path)
    if df.empty:
        raise ValueError(f"CSV is empty: {csv_path}")

    # detect expiration column
    possible_cols = ["expiration_date", "expiry_date", "expires", "best_before"]
    date_col = next((c for c in df.columns if c.lower() in possible_cols), None)
    if not date_col:
        raise ValueError(
            f"Could not find an expiration date column in {csv_path}. "
            f"Add one named one of: {possible_cols}"
        )

    # normalize date column
    df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
    if df[date_col].isna().any():
        bad = df[df[date_col].isna()]
        raise ValueError(
            "Some expiration dates failed to parse. Ensure ISO dates (YYYY-MM-DD) or clean formats.\n"
            f"Bad rows (showing up to 5):\n{bad.head(5)}"
        )
    return df, date_col


def slice_inventory(df: pd.DataFrame, date_col: str):
    """Return expired, expiring (<=7 days), and fresh slices."""
    today = pd.Timestamp(datetime.now().date())
    soon = today + pd.Timedelta(days=7)

    expired = df[df[date_col] < today].copy()
    expiring_7d = df[(df[date_col] >= today) & (df[date_col] <= soon)].copy()
    fresh = df[df[date_col] > soon].copy()
    return expired, expiring_7d, fresh


def df_to_markdown(df: pd.DataFrame, title: str, limit: int | None = None) -> str:
    """Render a DataFrame as a compact Markdown table with selected columns."""
    header = f"### {title}\n"
    if df.empty:
        return header + "\n_No items._\n"

    # prioritize common columns for readability
    pref = {"item", "product", "name", "quantity", "category", "expiration_date", "expiry_date"}
    cols = [c for c in df.columns if c.lower() in pref]
    if not cols:
        cols = list(df.columns)[:6]

    view = df[cols]
    if limit and len(view) > limit:
        view = view.head(limit)
        header = f"### {title} (showing first {limit} rows of {len(df)})\n"

    return header + "\n" + view.to_markdown(index=False) + "\n"


def head_markdown(df: pd.DataFrame, title: str, limit: int = 25) -> str:
    """Small wrapper to show only the first N rows in Markdown."""
    return df_to_markdown(df, title, limit=limit)


# =========================
# Main
# =========================
def main():
    # ---- Credentials / Session ----
    session = build_session()

    # ---- Client config (timeouts/retries) ----
    client_cfg = Config(
        retries={"max_attempts": 3, "mode": "standard"},
        connect_timeout=10,
        read_timeout=90,
    )

    # ---- Strands model using our custom boto3.Session ----
    # IMPORTANT: do NOT pass region_name here if you pass boto_session (Strands will raise).
    bedrock_model = BedrockModel(
        model_id=BEDROCK_MODEL_ID,
        boto_session=session,
        boto_client_config=client_cfg,
        temperature=0.2,
        streaming=True,  # you can set to False if you prefer
    )
    agent = Agent(model=bedrock_model)

    # ---- Load & analyze CSV locally ----
    df, date_col = load_inventory(INVENTORY_CSV_PATH)
    expired, expiring_7d, fresh = slice_inventory(df, date_col)

    summary_lines = [
        f"Today: {datetime.now().date()}",
        f"Date column: {date_col}",
        f"Counts → expired: {len(expired)}, expiring ≤7 days: {len(expiring_7d)}, fresh: {len(fresh)}",
    ]
    local_summary = "\n".join(summary_lines)

    # Build a text-only context for maximum model compatibility
    text_context = [
        USER_PROMPT,
        "",
        "## Context (computed locally; treat as ground truth)",
        local_summary,
        "",
        "## Data slices",
        head_markdown(expired, "Expired Items", limit=50),
        head_markdown(expiring_7d, "Expiring Within 7 Days", limit=50),
        head_markdown(fresh, "Sufficient Shelf Life", limit=50),
    ]
    messages = [{"text": "\n".join(text_context)}]

    # ---- Call the model via Strands ----
    response = agent(messages)  # returns a string-like object

    # ---- Compose final Markdown report ----
    report_parts = [
        "# Restaurant Inventory Expiration Analysis",
        f"_Generated: {datetime.now().isoformat(timespec='seconds')}_",
        "",
        "## Local Data Summary (computed by Python)",
        df_to_markdown(expired, "Expired Items"),
        df_to_markdown(expiring_7d, "Expiring Within 7 Days"),
        df_to_markdown(fresh, "Sufficient Shelf Life"),
        "## LLM Recommendations & Analysis",
        str(response),
    ]
    report_md = "\n".join(report_parts)

    with open(OUTPUT_REPORT_PATH, "w", encoding="utf-8") as f:
        f.write(report_md)

    # Also save the slices as CSVs for operational follow-up
    expired.to_csv("expired_items.csv", index=False)
    expiring_7d.to_csv("expiring_7d_items.csv", index=False)
    fresh.to_csv("fresh_items.csv", index=False)

    print(f"✅ Analysis complete.\n- Report: {OUTPUT_REPORT_PATH}\n- CSVs: expired_items.csv, expiring_7d_items.csv, fresh_items.csv")


# =========================
# Optional: Bedrock Agent (managed Agents API) helper
# (Not used in main flow, but handy if you have an Agent ID/Alias)
# =========================
def invoke_bedrock_agent_via_runtime(session: boto3.Session, agent_id: str, agent_alias_id: str, input_text: str, enable_trace: bool = False) -> str:
    """
    Calls a managed Agents for Amazon Bedrock Agent using bedrock-agent-runtime.
    Returns the combined text output.
    """
    client = session.client("bedrock-agent-runtime", region_name=AWS_REGION)
    resp = client.invoke_agent(
        agentId=agent_id,
        agentAliasId=agent_alias_id,
        sessionId=str(uuid.uuid4()),
        inputText=input_text,
        enableTrace=enable_trace,
    )

    out = b""
    for event in resp.get("completion", []):
        if "chunk" in event and "bytes" in event["chunk"]:
            out += event["chunk"]["bytes"]
    return out.decode("utf-8", errors="replace") if out else ""


if __name__ == "__main__":
    main()
