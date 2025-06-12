import pandas as pd
from sklearn.ensemble import RandomForestClassifier
import joblib

# Eksempeldata
data = pd.DataFrame({
    'ma_20_50_signal': [1, -1, 1, 0, -1],
    'ma_50_200_signal': [1, 1, -1, 0, -1],
    'rsi_signal': [0, 1, -1, 0, 1],
    'macd_signal': [1, -1, 0, 1, -1],
    'label': ['BUY', 'SELL', 'HOLD', 'BUY', 'SELL']
})

X = data[['ma_20_50_signal', 'ma_50_200_signal', 'rsi_signal', 'macd_signal']]
y = data['label']

model = RandomForestClassifier()
model.fit(X, y)
joblib.dump(model, 'stock_tip_model.pkl')