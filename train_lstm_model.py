import numpy as np
import tensorflow as tf
from sklearn.preprocessing import MinMaxScaler
from helpers import load_db_table
from config import LSTM_MODEL_PATH

def create_dataset(series, window=24):
    X, y = [], []
    for i in range(len(series) - window):
        X.append(series[i:i+window])
        y.append(series[i+window])
    return np.array(X), np.array(y)

df = load_db_table()
series = df["co"].dropna().values.reshape(-1, 1)

scaler = MinMaxScaler()
series_scaled = scaler.fit_transform(series)

X, y = create_dataset(series_scaled, 24)
X = X.reshape((X.shape[0], X.shape[1], 1))

model = tf.keras.Sequential([
    tf.keras.layers.LSTM(64, return_sequences=True),
    tf.keras.layers.LSTM(32),
    tf.keras.layers.Dense(1)
])

model.compile(optimizer="adam", loss="mse")
model.fit(X, y, epochs=10, batch_size=32)

model.save(LSTM_MODEL_PATH)
print("LSTM model trained and saved!")
