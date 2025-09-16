# prepare_for_powerbi.py
import os
import pandas as pd
import numpy as np

# Settings

RAW_CSV = "amazon.csv"   # your input dataset
OUT_DIR = "data"
TOP_N_PRODUCTS = 25

os.makedirs(OUT_DIR, exist_ok=True)


# Load data

df = pd.read_csv(RAW_CSV, dtype=str)
print("Raw rows:", df.shape[0])

# Normalize column names
df.columns = [c.strip().lower() for c in df.columns]


# Select useful columns

expected_cols = [
    'product_id','product_name','category',
    'discounted_price','actual_price','discount_percentage',
    'rating','rating_count',
    'about_product','user_id','user_name',
    'review_id','review_title','review_content',
    'img_link','product_link'
]

df = df[[c for c in expected_cols if c in df.columns]].copy()


# Clean & convert data


# Remove currency symbols etc.
for col in ['discounted_price','actual_price','discount_percentage']:
    if col in df.columns:
        df[col] = df[col].astype(str).str.replace(r'[^0-9.\-]', '', regex=True)

# Convert numerics
df['discounted_price'] = pd.to_numeric(df.get('discounted_price', 0), errors='coerce').fillna(0.0)
df['actual_price'] = pd.to_numeric(df.get('actual_price', 0), errors='coerce').fillna(0.0)
df['discount_percentage'] = pd.to_numeric(df.get('discount_percentage', 0), errors='coerce').fillna(0.0)
df['rating'] = pd.to_numeric(df.get('rating', 0), errors='coerce').fillna(0.0)
df['rating_count'] = pd.to_numeric(df.get('rating_count', 0), errors='coerce').fillna(0).astype(int)

# Add derived metrics
df['discount_value'] = df['actual_price'] - df['discounted_price']
df['has_discount'] = (df['discount_value'] > 0).astype(int)


# Save cleaned data

cleaned_path = os.path.join(OUT_DIR, "cleaned_products.csv")
df.to_csv(cleaned_path, index=False)
print("Successfully Saved cleaned data to:", cleaned_path)


# Aggregations


# 1) Category summary
cat_summary = df.groupby('category', as_index=False).agg(
    num_products=('product_id','nunique'),
    avg_actual_price=('actual_price','mean'),
    avg_discounted_price=('discounted_price','mean'),
    avg_discount_percentage=('discount_percentage','mean'),
    avg_rating=('rating','mean'),
    total_reviews=('rating_count','sum')
)
cat_summary.to_csv(os.path.join(OUT_DIR, "category_summary.csv"), index=False)
print(" Successfully Saved category summary")

# 2) Top products by rating_count (popularity)
top_products = df.groupby(['product_id','product_name'], as_index=False).agg(
    category=('category','first'),
    discounted_price=('discounted_price','mean'),
    actual_price=('actual_price','mean'),
    avg_rating=('rating','mean'),
    total_reviews=('rating_count','sum')
).sort_values('total_reviews', ascending=False).head(TOP_N_PRODUCTS)
top_products.to_csv(os.path.join(OUT_DIR, "top_products.csv"), index=False)
print("Successfully Saved top products")

# 3) Discount analysis
discount_summary = df.groupby('category', as_index=False).agg(
    avg_discount_percentage=('discount_percentage','mean'),
    max_discount=('discount_percentage','max'),
    min_discount=('discount_percentage','min')
)
discount_summary.to_csv(os.path.join(OUT_DIR, "discount_summary.csv"), index=False)
print("Successfully Saved discount summary")

# 4) Review data (for text analysis in Power BI or Python NLP later)
reviews = df[['product_id','product_name','review_id','review_title','review_content','rating']].dropna()
reviews.to_csv(os.path.join(OUT_DIR, "reviews_data.csv"), index=False)
print("Successfully Saved reviews dataset")

# 5) KPIs summary
kpis = pd.DataFrame([{
    'total_products': df['product_id'].nunique(),
    'total_reviews': df['review_id'].nunique() if 'review_id' in df.columns else df['rating_count'].sum(),
    'avg_rating': df['rating'].mean(),
    'avg_discount_percentage': df['discount_percentage'].mean(),
    'avg_actual_price': df['actual_price'].mean(),
    'avg_discounted_price': df['discounted_price'].mean()
}])
kpis.to_csv(os.path.join(OUT_DIR, "kpis_summary.csv"), index=False)
print("Successfully Saved KPIs summary")

print("All exports completed. Files Successfully saved in:", OUT_DIR)
