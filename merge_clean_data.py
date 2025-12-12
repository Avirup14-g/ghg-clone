import pandas as pd
from helpers import load_db_table
# Clean and merge duplicate timestamps
df = load_db_table()

df["timestamp"] = pd.to_datetime(df["timestamp"])
df = df.drop_duplicates(subset=["timestamp"])
df = df.sort_values("timestamp")

df.to_csv("cleaned_data.csv", index=False)

print("Cleaned data exported to cleaned_data.csv")
