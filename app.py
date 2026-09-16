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
            clean_symbol = symbol.split(":")[-1].strip()
            ticker = yf.Ticker(clean_symbol)
            df = ticker.history(period="60d")
            
            if df.empty or len(df) < 15:
                results[symbol] = {"rsi": "-", "stoch": "-", "news": "-"}
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
            
            # สร้างฟังก์ชัน HYPERLINK สำหรับ Google Sheets
            hyperlinks = []
            try:
                raw_news = ticker.news
                if raw_news and isinstance(raw_news, list):
                    for item in raw_news[:3]:
                        content = item.get('content', {})
                        title = content.get('title') or item.get('title')
                        
                        click_through = content.get('clickThroughUrl', {})
                        link = click_through.get('url') if isinstance(click_through, dict) else None
                        if not link:
                            link = item.get('link')
                            
                        if title and link:
                            # ตัดเครื่องหมายคำพูดออกทั้งหมด เพื่อป้องกันสูตร Google Sheets พัง
                            safe_title = str(title).replace('"', '').replace("'", "").strip()
                            hyperlinks.append(f'HYPERLINK("{link}", "{safe_title}")')
            except Exception:
                pass
            
            # ถ้าไม่มีข่าว ให้ใช้ลิงก์สำรองหลักของ Yahoo Finance
            if not hyperlinks:
                fallback_link = f"https://finance.yahoo.com/quote/{clean_symbol}"
                hyperlinks.append(f'HYPERLINK("{fallback_link}", "ภาพรวมและข้อมูลล่าสุดของ {clean_symbol}")')
                hyperlinks.append(f'HYPERLINK("{fallback_link}/key-statistics/", "งบการเงินและสถิติสำคัญ")')
                hyperlinks.append(f'HYPERLINK("{fallback_link}/chart/", "กราฟวิเคราะห์แนวโน้มราคา")')
            
            # ใช้การต่อสูตรด้วยโครงสร้าง Array หรือเครื่องหมายบรรทัดใหม่ของ Google Sheets
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
