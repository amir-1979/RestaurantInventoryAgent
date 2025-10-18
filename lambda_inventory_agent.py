import json
import boto3
import pandas as pd
from datetime import datetime
import os
import io
from botocore.config import Config

def lambda_handler(event, context):
    """
    AWS Lambda handler for inventory analysis
    """
    try:
        # Get S3 bucket and key from event
        bucket_name = event.get('bucket_name', os.environ.get('INVENTORY_BUCKET'))
        csv_key = event.get('csv_key', 'inventory.csv')
        
        if not bucket_name:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'No bucket specified'})
            }
        
        # Initialize S3 client
        s3_client = boto3.client('s3')
        
        # Download CSV from S3
        try:
            response = s3_client.get_object(Bucket=bucket_name, Key=csv_key)
            csv_content = response['Body'].read().decode('utf-8')
            
            # Load into pandas
            df = pd.read_csv(io.StringIO(csv_content))
            
        except Exception as e:
            return {
                'statusCode': 404,
                'body': json.dumps({'error': f'Could not load CSV: {str(e)}'})
            }
        
        # Analyze inventory
        analysis_result = analyze_inventory(df)
        
        # Save results back to S3
        output_key = f"analysis_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        s3_client.put_object(
            Bucket=bucket_name,
            Key=output_key,
            Body=json.dumps(analysis_result, indent=2, default=str),
            ContentType='application/json'
        )
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
            },
            'body': json.dumps({
                'message': 'Analysis completed successfully',
                'result': analysis_result,
                'output_file': output_key
            }, default=str)
        }
        
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Internal error: {str(e)}'})
        }

def analyze_inventory(df):
    """
    Analyze inventory data and return results
    """
    try:
        # Find expiration date column
        date_col = None
        possible_cols = ["expiration_date", "expiry_date", "expires", "best_before"]
        
        for col in df.columns:
            if col.lower() in [c.lower() for c in possible_cols]:
                date_col = col
                break
        
        if not date_col:
            return {'error': 'No expiration date column found'}
        
        # Convert dates
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        df = df.dropna(subset=[date_col])
        
        # Analyze
        today = pd.Timestamp(datetime.now().date())
        soon = today + pd.Timedelta(days=7)
        
        expired = df[df[date_col] < today]
        expiring_7d = df[(df[date_col] >= today) & (df[date_col] <= soon)]
        fresh = df[df[date_col] > soon]
        
        # Create summary
        summary = {
            'analysis_date': datetime.now().isoformat(),
            'total_items': len(df),
            'expired_count': len(expired),
            'expiring_soon_count': len(expiring_7d),
            'fresh_count': len(fresh),
            'expired_items': expired.to_dict('records') if not expired.empty else [],
            'expiring_soon_items': expiring_7d.to_dict('records') if not expiring_7d.empty else [],
            'recommendations': generate_recommendations(expired, expiring_7d, fresh)
        }
        
        return summary
        
    except Exception as e:
        return {'error': f'Analysis failed: {str(e)}'}

def generate_recommendations(expired, expiring_7d, fresh):
    """
    Generate actionable recommendations
    """
    recommendations = []
    
    if not expired.empty:
        recommendations.append({
            'priority': 'HIGH',
            'category': 'Expired Items',
            'action': f'Remove {len(expired)} expired items immediately',
            'items': expired['item'].tolist()[:5] if 'item' in expired.columns else []
        })
    
    if not expiring_7d.empty:
        recommendations.append({
            'priority': 'MEDIUM',
            'category': 'Expiring Soon',
            'action': f'Create specials for {len(expiring_7d)} items expiring within 7 days',
            'items': expiring_7d['item'].tolist()[:5] if 'item' in expiring_7d.columns else []
        })
    
    recommendations.append({
        'priority': 'LOW',
        'category': 'Best Practices',
        'action': 'Implement FIFO rotation and monitor storage conditions',
        'items': []
    })
    
    return recommendations