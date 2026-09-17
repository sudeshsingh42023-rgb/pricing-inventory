"""
Project 1: Used-Car Pricing & Inventory Turnover Analysis
Generates a realistic synthetic dataset of used-car listings, mimicking
what Spinny's internal inventory/sales data would look like.
"""
import numpy as np
import pandas as pd
import sqlite3
from datetime import datetime, timedelta

np.random.seed(42)

N = 8000

brands_models = {
    "Maruti Suzuki": ["Swift", "Baleno", "Dzire", "WagonR", "Ertiga"],
    "Hyundai": ["i20", "Creta", "Venue", "Grand i10", "Verna"],
    "Tata": ["Nexon", "Punch", "Altroz", "Tiago", "Harrier"],
    "Honda": ["City", "Amaze", "Jazz", "WR-V"],
    "Toyota": ["Innova", "Fortuner", "Glanza"],
    "Mahindra": ["XUV300", "Scorpio", "Bolero", "XUV700"],
    "Kia": ["Seltos", "Sonet", "Carens"],
}

cities = ["Delhi NCR", "Bengaluru", "Mumbai", "Hyderabad", "Pune", "Chennai", "Ahmedabad", "Kolkata"]
city_demand_factor = {  # relative demand strength -> affects days-to-sell
    "Delhi NCR": 1.15, "Bengaluru": 1.20, "Mumbai": 1.05, "Hyderabad": 1.00,
    "Pune": 0.95, "Chennai": 0.90, "Ahmedabad": 0.85, "Kolkata": 0.80,
}

base_price = {
    "Swift": 550000, "Baleno": 600000, "Dzire": 580000, "WagonR": 450000, "Ertiga": 750000,
    "i20": 620000, "Creta": 1150000, "Venue": 750000, "Grand i10": 480000, "Verna": 950000,
    "Nexon": 850000, "Punch": 600000, "Altroz": 620000, "Tiago": 480000, "Harrier": 1450000,
    "City": 900000, "Amaze": 600000, "Jazz": 620000, "WR-V": 780000,
    "Innova": 1600000, "Fortuner": 2900000, "Glanza": 650000,
    "XUV300": 800000, "Scorpio": 1250000, "Bolero": 700000, "XUV700": 1650000,
    "Seltos": 1150000, "Sonet": 800000, "Carens": 1050000,
}

condition_grades = ["A (Excellent)", "B (Good)", "C (Fair)"]
condition_multiplier = {"A (Excellent)": 1.08, "B (Good)": 1.00, "C (Fair)": 0.90}

rows = []
listing_id_start = 100000
today = datetime(2026, 9, 1)

for i in range(N):
    brand = np.random.choice(list(brands_models.keys()), p=[0.24, 0.20, 0.16, 0.11, 0.08, 0.13, 0.08])
    model = np.random.choice(brands_models[brand])
    year = np.random.choice(range(2016, 2025), p=[0.05,0.06,0.08,0.10,0.12,0.14,0.15,0.16,0.14])
    age_years = 2026 - year
    mileage_km = int(max(2000, np.random.normal(loc=age_years * 12000, scale=8000)))
    condition = np.random.choice(condition_grades, p=[0.30, 0.50, 0.20])
    city = np.random.choice(cities)

    bp = base_price[model]
    # depreciation ~ 12% first year, then ~9%/yr, floor at 20% of base
    dep_factor = max(0.20, (0.88) * (0.91 ** max(0, age_years - 1)))
    fair_value = bp * dep_factor * condition_multiplier[condition]
    fair_value *= (1 - min(mileage_km, 150000) / 150000 * 0.15)  # mileage penalty up to 15%

    # Listing price: analysts don't always price at fair value -> some noise/bias
    pricing_error = np.random.normal(loc=0, scale=0.09)  # +/-9% typical mispricing
    listing_price = fair_value * (1 + pricing_error)

    # Days to sell depends on how overpriced vs fair value, plus city demand
    overpricing_pct = (listing_price - fair_value) / fair_value
    demand = city_demand_factor[city]
    base_days = 28 / demand
    days_to_sell = max(3, base_days * (1 + overpricing_pct * 2.2) + np.random.normal(0, 6))

    listed_date = today - timedelta(days=int(np.random.uniform(1, 120)))
    sold = days_to_sell <= (today - listed_date).days
    sold_date = listed_date + timedelta(days=int(days_to_sell)) if sold else None
    sale_price = None
    if sold:
        # actual sale usually closes a bit below final listing price (negotiation)
        sale_price = round(listing_price * np.random.uniform(0.94, 0.99), -2)

    days_in_inventory = (sold_date - listed_date).days if sold else (today - listed_date).days

    rows.append({
        "listing_id": listing_id_start + i,
        "brand": brand,
        "model": model,
        "year": year,
        "mileage_km": mileage_km,
        "condition_grade": condition,
        "city": city,
        "fair_value_est": round(fair_value, -2),
        "listing_price": round(listing_price, -2),
        "listed_date": listed_date.strftime("%Y-%m-%d"),
        "sold_flag": int(sold),
        "sold_date": sold_date.strftime("%Y-%m-%d") if sold else None,
        "sale_price": sale_price,
        "days_in_inventory": days_in_inventory,
    })

df = pd.DataFrame(rows)
df.to_csv("/home/claude/spinny_project1/used_cars.csv", index=False)

# Load into SQLite so SQL queries can run against it (mirrors a real DB workflow)
conn = sqlite3.connect("/home/claude/spinny_project1/spinny_inventory.db")
df.to_sql("used_cars", conn, if_exists="replace", index=False)
conn.close()

print(f"Generated {len(df)} listings. Sold: {df['sold_flag'].sum()}, Unsold/active: {(df['sold_flag']==0).sum()}")
print(df.head())
