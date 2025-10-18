# Restaurant Inventory Expiration Analysis
_Generated: 2025-10-18T11:48:46_

## Local Data Summary (computed by Python)
### Expired Items

| item            |   quantity | expiration_date     | category   |
|:----------------|-----------:|:--------------------|:-----------|
| Milk            |          8 | 2025-10-15 00:00:00 | Dairy      |
| Romaine Lettuce |         12 | 2025-10-13 00:00:00 | Produce    |
| Spinach         |         10 | 2025-10-11 00:00:00 | Produce    |
| Salmon Fillet   |         12 | 2025-10-10 00:00:00 | Seafood    |
| Yogurt          |         24 | 2025-10-14 00:00:00 | Dairy      |
| Tomatoes        |         18 | 2025-10-16 00:00:00 | Produce    |
| Mushrooms       |         10 | 2025-10-12 00:00:00 | Produce    |
| Bread Loaves    |         16 | 2025-10-13 00:00:00 | Bakery     |
| Cream           |          8 | 2025-10-17 00:00:00 | Dairy      |
| Lettuce Iceberg |         10 | 2025-10-09 00:00:00 | Produce    |
| Strawberries    |         20 | 2025-10-12 00:00:00 | Produce    |
| Shrimp          |         18 | 2025-10-15 00:00:00 | Seafood    |
| Tofu            |         16 | 2025-10-13 00:00:00 | Protein    |

### Expiring Within 7 Days

| item           |   quantity | expiration_date     | category   |
|:---------------|-----------:|:--------------------|:-----------|
| Eggs           |         30 | 2025-10-20 00:00:00 | Protein    |
| Chicken Breast |         20 | 2025-10-18 00:00:00 | Protein    |
| Ground Beef    |         15 | 2025-10-22 00:00:00 | Protein    |
| Avocados       |         14 | 2025-10-19 00:00:00 | Produce    |
| Buns           |         24 | 2025-10-21 00:00:00 | Bakery     |
| Blueberries    |         12 | 2025-10-23 00:00:00 | Produce    |
| Bacon          |         12 | 2025-10-25 00:00:00 | Protein    |

### Sufficient Shelf Life

| item           |   quantity | expiration_date     | category   |
|:---------------|-----------:|:--------------------|:-----------|
| Cheddar Cheese |          5 | 2025-11-05 00:00:00 | Dairy      |
| Onions         |         25 | 2025-12-01 00:00:00 | Produce    |
| Potatoes       |         50 | 2025-11-20 00:00:00 | Produce    |
| Butter         |          6 | 2026-01-15 00:00:00 | Dairy      |
| Olive Oil      |          4 | 2027-06-01 00:00:00 | Dry Goods  |
| Pasta          |         40 | 2026-03-01 00:00:00 | Dry Goods  |
| Rice           |         60 | 2027-12-31 00:00:00 | Dry Goods  |
| Soda           |         48 | 2026-08-01 00:00:00 | Beverage   |
| Ice Cream      |         10 | 2025-11-10 00:00:00 | Frozen     |
| Frozen Peas    |         30 | 2026-02-10 00:00:00 | Frozen     |

## LLM Recommendations & Analysis
# Inventory Analysis Report

## Context
- **Today:** 2025-10-18
- **Expired Items Count:** 13
- **Expiring ≤7 Days Count:** 7
- **Fresh Items Count:** 10

## Expired Items

| Item            | Quantity | Expiration Date | Category   |
|:----------------|---------:|:---------------|:-----------|
| Milk            | 8        | 2025-10-15     | Dairy      |
| Romaine Lettuce | 12       | 2025-10-13     | Produce    |
| Spinach         | 10       | 2025-10-11     | Produce    |
| Salmon Fillet   | 12       | 2025-10-10     | Seafood    |
| Yogurt          | 24       | 2025-10-14     | Dairy      |
| Tomatoes        | 18       | 2025-10-16     | Produce    |
| Mushrooms       | 10       | 2025-10-12     | Produce    |
| Bread Loaves    | 16       | 2025-10-13     | Bakery     |
| Cream           | 8        | 2025-10-17     | Dairy      |
| Lettuce Iceberg | 10       | 2025-10-09     | Produce    |
| Strawberries    | 20       | 2025-10-12     | Produce    |
| Shrimp          | 18       | 2025-10-15     | Seafood    |
| Tofu            | 16       | 2025-10-13     | Protein    |

## Items Expiring Within 7 Days

| Item            | Quantity | Expiration Date | Category   |
|:----------------|---------:|:---------------|:-----------|
| Eggs            | 30       | 2025-10-20     | Protein    |
| Chicken Breast  | 20       | 2025-10-18     | Protein    |
| Ground Beef     | 15       | 2025-10-22     | Protein    |
| Avocados        | 14       | 2025-10-19     | Produce    |
| Buns             | 24       | 2025-10-21     | Bakery     |
| Blueberries     | 12       | 2025-10-23     | Produce    |
| Bacon           | 12       | 2025-10-25     | Protein    |

## Items with Sufficient Shelf Life

| Item            | Quantity | Expiration Date | Category   |
|:----------------|---------:|:---------------|:-----------|
| Cheddar Cheese  | 5        | 2025-11-05     | Dairy      |
| Onions          | 25       | 2025-12-01     | Produce    |
| Potatoes        | 50       | 2025-11-20     | Produce    |
| Butter          | 6        | 2026-01-15     | Dairy      |
| Olive Oil       | 4        | 2027-06-01     | Dry Goods  |
| Pasta           | 40       | 2026-03-01     | Dry Goods  |
| Rice            | 60       | 2027-12-31     | Dry Goods  |
| Soda            | 48       | 2026-08-01     | Beverage   |
| Ice Cream       | 10       | 2025-11-10     | Frozen     |
| Frozen Peas     | 30       | 2026-02-10     | Frozen     |

## Actionable Recommendations

1. **Discounting and Menu Specials:**
   - Consider offering discounts on perishable items like **Spinach, Tomatoes, Mushrooms, Lettuce Iceberg, Strawberries, Shrimp, and Tofu** to reduce inventory before they expire.
   - Create a special menu featuring **Avocados, Blueberries, and Bacon** which are expiring soon.

2. **Reorder Timing:**
   - **Eggs, Chicken Breast, Ground Beef, Avocados, Buns** are expiring within the next 7 days. Plan reordering soon to avoid stockouts.
   
3. **Storage Tips:**
   - Ensure proper storage for items like **Salmon Fillet, Yogurt, and Cream** to extend their shelf life.
   - Monitor storage conditions for **perishable items** to minimize spoilage.

4. **Inventory Management:**
   - Regularly review inventory levels and expiration dates to maintain optimal stock levels.
   - Implement a first-in, first-out (FIFO) system to ensure older stock is used before newer stock.

By following these recommendations, the restaurant can minimize waste, optimize inventory, and maintain high customer satisfaction.
