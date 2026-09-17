# pricing-inventory
# Used-Car Pricing & Inventory Turnover Analysis
**Role target:** Business Analyst, Spinny (Gurugram)

## Business Problem
Spinny operates a full-stack used-car marketplace where every unsold car ties up
capital and depreciates the longer it sits in inventory. Two failure modes hurt
the business simultaneously:
- **Overpriced cars** sit unsold for longer, tying up capital and inflating
  holding costs.
- **Underpriced cars** sell fast but leave margin on the table.

This project builds a data pipeline that estimates a fair market value for every
listing, flags mispriced inventory, and quantifies the turnover impact of
correcting those prices.

## Approach
1. **Data generation** (`01_generate_data.py`) — Since real Spinny data isn't
   public, this simulates a realistic 8,000-listing inventory: brand, model,
   year, mileage, condition grade, city, listing price, and (for sold units)
   actual sale price and days-in-inventory. Depreciation, condition, and city
   demand are all modeled so the relationships in the data resemble a real
   used-car market.
2. **SQL analysis** (`02_analysis_queries.sql`) — Run against a SQLite database
   built from the same data. Answers: average days-to-sell by brand/city,
   inventory aging buckets, mispricing checks, and a brand-x-city turnover
   matrix.
3. **Pricing model** (`03_pricing_model.py`) — An XGBoost regression model is
   trained on sold listings (features: brand, model, car age, mileage,
   condition, city) to predict true sale price. The model is then used to
   score every listing (including unsold ones) and flag units priced more
   than 10% away from their model-estimated fair value.
4. **Excel dashboard** (`Project1_Pricing_Inventory_Dashboard.xlsx`) — A
   5-tab, formula-driven workbook (no hardcoded results) built for a
   non-technical stakeholder audience:
   - **Summary** — headline KPIs (total listings, avg days-to-sell,
     capital tied up, count of overpriced/underpriced units)
   - **Turnover_By_Brand** — SUMIFS/AVERAGEIFS pivot with a bar chart,
     conditional formatting on slow-turnover brands
   - **Aging_Inventory** — unsold stock broken into 0-15 / 16-30 / 31-60 /
     60+ day buckets with capital-tied-up totals and a color scale
   - **Reprice_Candidates** — every flagged listing with its model fair
     value, % deviation, and a recommended price
   - **Raw_Data** — the full scored dataset all formulas reference

## Key Results
- Pricing model accuracy: **R² = 0.965**, MAE ≈ ₹37,500 on holdout sold listings
- **591 unsold units (31%)** are priced more than 10% above model fair value
- **104 units (5.5%)** are underpriced, representing a margin-capture opportunity
- Each 1 percentage point of overpricing adds ~0.64 days to time-to-sell
- Reprising overpriced units by ~10pp is projected to cut fleet-wide average
  days-to-sell by **~12.5%**
- ~₹97 crore in capital currently tied up in unsold inventory (aging analysis)

## Tech Stack
Python (pandas, numpy, scikit-learn, xgboost) · SQL (SQLite) · Excel (openpyxl,
formula-driven, charts, conditional formatting)

## Files
| File | Purpose |
|---|---|
| `01_generate_data.py` | Generates the synthetic 8,000-listing dataset and loads it into SQLite |
| `used_cars.csv` | The generated raw dataset |
| `02_analysis_queries.sql` | SQL queries for turnover, aging, and mispricing analysis |
| `03_pricing_model.py` | Trains the XGBoost fair-value model and scores all listings |
| `Project1_Pricing_Inventory_Dashboard.xlsx` | Final stakeholder-facing Excel dashboard |

## How to Run
```bash
pip install pandas numpy scikit-learn xgboost openpyxl
python 01_generate_data.py      # creates used_cars.csv + spinny_inventory.db
python 03_pricing_model.py      # trains model, creates used_cars_scored.csv
# (Excel workbook is built from used_cars_scored.csv via a separate build script)
```

## Note on Data
All data in this project is **synthetically generated** to statistically
resemble a used-car marketplace. It does not contain or reference any real
Spinny data. This is disclosed here for transparency — mention this plainly
if asked in an interview.
