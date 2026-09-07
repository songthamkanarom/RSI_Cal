from flask import Flask, request, jsonify
import yfinance as yf
import ta

app = Flask(__name__)

@app.route('/calculate-indicators', methods=['POST'])
def calculate_indicators():
    data = request.json
    symbols = data.get("symbols", [])
    
    results = {}
    for symbol in symbols:
        try:
            clean_symbol = symbol.split(":")[-1] 
            df = yf.download(clean_symbol, period="60d", interval="1d", progress=False)
            
            if df.empty or len(df) < 15:
                results[symbol] = {"rsi": "-", "stoch": "-"}
                continue
                
            # คำนวณ RSI (14)
            rsi_series = ta.rsi(df['Close'], length=14)
            current_rsi = round(float(rsi_series.iloc[-1]), 2) if not rsi_series.empty else "-"
            
            # คำนวณ Stochastic %K (14)
            stoch_df = ta.stoch(df['High'], df['Low'], df['Close'], k=14, d=3, smooth_k=3)
            k_col = [c for c in stoch_df.columns if c.startswith('STOCHk')][0]
            current_stoch = round(float(stoch_df[k_col].iloc[-1]), 2) if not stoch_df.empty else "-"
            
            results[symbol] = {
                "rsi": current_rsi,
                "stoch": current_stoch
            }
        except Exception as e:
            results[symbol] = {"rsi": "-", "stoch": "-"}
            
    return jsonify({"status": "success", "data": results})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
