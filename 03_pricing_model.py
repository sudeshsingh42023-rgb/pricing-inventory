"""
Project 1: Used-Car Pricing & Inventory Turnover Analysis
Trains a fair-value prediction model, flags mispriced inventory, and
quantifies the projected reduction in days-to-sell from reprising.
"""
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import xgboost as xgb

df = pd.read_csv("/home/claude/spinny_project1/used_cars.csv")
df["car_age"] = 2026 - df["year"]

# We predict SALE PRICE (proxy for true market value) from car attributes,
# using only sold listings to train (ground truth), then score ALL listings.
sold = df[df["sold_flag"] == 1].copy()

features = ["brand", "model", "car_age", "mileage_km", "condition_grade", "city"]
target = "sale_price"

X = sold[features]
y = sold[target]

categorical = ["brand", "model", "condition_grade", "city"]
numeric = ["car_age", "mileage_km"]

preprocessor = ColumnTransformer([
    ("cat", OneHotEncoder(handle_unknown="ignore"), categorical),
], remainder="passthrough")

model = Pipeline([
    ("prep", preprocessor),
    ("xgb", xgb.XGBRegressor(
        n_estimators=300, max_depth=5, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, random_state=42
    )),
])

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
model.fit(X_train, y_train)
preds = model.predict(X_test)

mae = mean_absolute_error(y_test, preds)
r2 = r2_score(y_test, preds)
print(f"Model performance on holdout set: MAE = Rs.{mae:,.0f}, R2 = {r2:.3f}")

# Score ALL listings (including currently unsold) to get a model fair value
df["model_fair_value"] = model.predict(df[features])
df["pct_vs_model_value"] = (df["listing_price"] - df["model_fair_value"]) / df["model_fair_value"] * 100

# Flag mispriced UNSOLD inventory
unsold = df[df["sold_flag"] == 0].copy()
overpriced = unsold[unsold["pct_vs_model_value"] > 10]
underpriced = unsold[unsold["pct_vs_model_value"] < -10]

print(f"\nUnsold inventory: {len(unsold)}")
print(f"Overpriced (>10% above model value): {len(overpriced)} ({len(overpriced)/len(unsold)*100:.1f}%)")
print(f"Underpriced (>10% below model value): {len(underpriced)} ({len(underpriced)/len(unsold)*100:.1f}%)")

# Estimate turnover impact: using the observed relationship between overpricing % 
# and days_in_inventory from sold data (simple linear fit) to project days saved
# if overpriced units were repriced to fair value.
from numpy.polynomial import polynomial as P
sold["overpricing_pct"] = (sold["listing_price"] - sold["fair_value_est"]) / sold["fair_value_est"] * 100
coeffs = np.polyfit(sold["overpricing_pct"], sold["days_in_inventory"], 1)
slope, intercept = coeffs[0], coeffs[1]

current_avg_days = unsold["days_in_inventory"].mean()
projected_days_saved_per_overpriced_unit = slope * (overpricing_pct_reduction := 10)  # reprice down by ~10pp on average
total_days_saved = abs(projected_days_saved_per_overpriced_unit) * len(overpriced)

print(f"\nEstimated relationship: each 1pp of overpricing adds ~{slope:.2f} days to time-to-sell")
print(f"Reprising {len(overpriced)} overpriced units by ~10 percentage points")
print(f"-> projected ~{abs(projected_days_saved_per_overpriced_unit):.1f} fewer days-to-sell per unit")
print(f"-> fleet-wide reduction in average days-to-sell: "
      f"~{(abs(projected_days_saved_per_overpriced_unit) * len(overpriced) / len(unsold)):.1f} days "
      f"({(abs(projected_days_saved_per_overpriced_unit) * len(overpriced) / len(unsold)) / current_avg_days * 100:.1f}% of current average)")

# Save outputs for the Excel dashboard
def flag_row(row):
    if row["sold_flag"] == 1:
        return "N/A (sold)"
    if row["pct_vs_model_value"] > 10:
        return "Overpriced - reprice down"
    if row["pct_vs_model_value"] < -10:
        return "Underpriced - opportunity"
    return "Fairly priced"

df["reprice_flag"] = df.apply(flag_row, axis=1)
df["recommended_price"] = np.where(
    (df["sold_flag"] == 0) & (df["pct_vs_model_value"].abs() > 10),
    df["model_fair_value"].round(-2),
    df["listing_price"],
)

df.to_csv("/home/claude/spinny_project1/used_cars_scored.csv", index=False)
print("\nSaved scored dataset -> used_cars_scored.csv")
