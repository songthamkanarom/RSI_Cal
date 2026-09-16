import base64
import requests
import pandas as pd
import ta
from flask import Flask, request, jsonify

app = Flask(__name__)

FMP_API_KEY = "HJ3KIwe122MzRTlZf954ukkEMsXe5XHR"  # Key ของคุณจาก Apps Script[cite: 1]

@app.route('/calculate-indicators', methods=['POST'])
def calculate_indicators():
    data = request.json
    symbols = data.get("symbols", [])
    
    results = {}
    for symbol in symbols:
        try:
            clean_symbol = symbol.split(":")[-1].strip().upper()
            
            # 📌 1. ดึงข้อมูล Daily Historical Prices จาก FMP API
            url = f"https://financialmodelingprep.com/api/v3/historical-price-full/{clean_symbol}?timeseries=60&apikey={FMP_API_KEY}"
            response = requests.get(url, timeout=10)
            
            if response.status_code != 200:
                results[symbol] = {"rsi": "-", "stoch": "-", "news": "-"}
                continue
                
            json_data = response.json()
            historical = json_data.get("historical", [])
            
            if not historical or len(historical) < 15:
                results[symbol] = {"rsi": "-", "stoch": "-", "news": "-"}
                continue
                
            # แปลงข้อมูลเป็น DataFrame (เรียงจากวันที่เก่าไปใหม่อัตโนมัติ)
            df = pd.DataFrame(historical)
            df = df.iloc[::-1].reset_index(drop=True)  # สลับลำดับให้วันเก่าขึ้นก่อน
            
            close_prices = df['close']
            high_prices = df['high']
            low_prices = df['low']
            
            # 📌 2. คำนวณ RSI (14)
            rsi_series = ta.momentum.rsi(close_prices, window=14)
            rsi_val = rsi_series.iloc[-1]
            current_rsi = round(float(rsi_val), 2) if not pd.isna(rsi_val) else "-"
            
            # 📌 3. คำนวณ Stochastic %K (14, 3)
            stoch_series = ta.momentum.stoch(high_prices, low_prices, close_prices, window=14, smooth_window=3)
            stoch_val = stoch_series.iloc[-1]
            current_stoch = round(float(stoch_val), 2) if not pd.isna(stoch_val) else "-"
            
            # 📌 4. ลิงก์ข่าวสำรอง / สรุป
            fallback_link = f"https://financialmodelingprep.com/financial-summary/{clean_symbol}"
            hyperlinks = [
                f'HYPERLINK("{fallback_link}", "ภาพรวมและงบการเงินของ {clean_symbol}")'
            ]
            news_formula = "=" + " & CHAR(10) & ".join(hyperlinks)
            
            results[symbol] = {
                "rsi": current_rsi,
                "stoch": current_stoch,
                "news": news_formula
            }
        except Exception as e:
            results[symbol] = {"rsi": "-", "stoch": "-", "news": "-"}
            
    return jsonify({"status": "success", "data": results})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
