from flask import Flask, request, jsonify
import yfinance as yf
import ta
import pandas as pd

app = Flask(__name__)

@app.route('/calculate-indicators', methods=['POST'])
def calculate_indicators():
    data = request.json
    symbols = data.get("symbols", [])
    
    results = {}
    for symbol in symbols:
        try:
            # ตัด prefix เช่น NASDAQ:, NYSE: ออก เหลือแค่ชื่อย่อหลัก
            clean_symbol = symbol.split(":")[-1].strip()
            
            # ดึงข้อมูลย้อนหลัง 60 วันด้วย Ticker history
            ticker = yf.Ticker(clean_symbol)
            df = ticker.history(period="60d")
            
            if df.empty or len(df) < 15:
                results[symbol] = {"rsi": "-", "stoch": "-"}
                continue
                
            close_prices = df['Close']
            high_prices = df['High']
            low_prices = df['Low']
            
            # คำนวณ RSI (14)
            rsi_series = ta.momentum.rsi(close_prices, window=14)
            rsi_val = rsi_series.iloc[-1]
            current_rsi = round(float(rsi_val), 2) if not pd.isna(rsi_val) else "-"
            
            # คำนวณ Stochastic %K (14, 3)
            stoch_series = ta.momentum.stoch(high_prices, low_prices, close_prices, window=14, smooth_window=3)
            stoch_val = stoch_series.iloc[-1]
            current_stoch = round(float(stoch_val), 2) if not pd.isna(stoch_val) else "-"
            
            results[symbol] = {
                "rsi": current_rsi,
                "stoch": current_stoch
            }
        except Exception as e:
            results[symbol] = {"rsi": "-", "stoch": "-"}
            
    return jsonify({"status": "success", "data": results})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
