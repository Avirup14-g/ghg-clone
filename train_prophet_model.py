import pickle
from prophet import Prophet
from helpers import load_db_table
from config import PROPHET_MODEL_PATH

df = load_db_table()
df_prophet = df[["timestamp", "co"]]
df_prophet.columns = ["ds", "y"]

model = Prophet()
model.fit(df_prophet)

with open(PROPHET_MODEL_PATH, 'wb') as f:
    pickle.dump(model, f)
print("Prophet model trained and saved!")
