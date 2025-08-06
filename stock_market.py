import requests
import json
import pandas as pd
import matplotlib.pyplot as plt
import mplfinance as mpf
from datetime import datetime, timezone
import os 
from dotenv import load_dotenv

# ---------- For Line Graph ----------
load_dotenv()
TICKERS = ["VOO", "QQQ", "SPY", "QLD"]
API_KEY = os.getenv("FMP_API_KEY")
HIST_FILE = "market_history.json"
IMG_FILE = "market_chart.png"
README_FILE = "README.md"
# ---------- For CandleStick Chart ----------
TICKER = "QLD"
IMG_FILE_Q = "qld_candlestick.png"

# --------- 실시간 시세 데이터 요청 함수 ----------
def fetch_quotes():
    URL = f"https://financialmodelingprep.com/api/v3/quote/{','.join(TICKERS)}?apikey={API_KEY}"
    resp = requests.get(URL)
    data = resp.json()
    result = {}
    for d in data:
        result[d["symbol"]] = d["price"]
    return result

# ---------- json 파일 생성, 이후 불러오기 ----------
def load_history():
    if os.path.exists(HIST_FILE):
        with open(HIST_FILE) as f:
            return json.load(f)
    else:
        return []

# --------- json 에 저장 (기록 저장) ----------
def save_history(history):
    # history에 json 파일 
    with open(HIST_FILE, 'w') as f:
        json.dump(history, f)

# ---------- 새로 받아온 시세 기록에 추가 ----------
def update_history(prices):
    history = load_history() # 기존 데이터 history에 저장
    time_str = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')
    history.append({
        'time': time_str, **prices
    }) # prices는 내가 받아온 여러 주식의 가격 키:값 형태
    history = history[-30:]
    save_history(history)
    return history

def make_chart(history):
    df = pd.DataFrame(history)
    df.set_index('time', inplace=True)
    plt.figure(figsize=(24, 4))
    for ticker in TICKERS:
        plt.plot(df.index, df[ticker], marker='o', label=ticker) # 각 종목 라인
    plt.legend()
    plt.grid(True)
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.title('최근 30회 장시작, 마감 시세 변화')
    plt.ylabel('가격(USD)')
    plt.savefig('market_chart.png')
    plt.close()

def get_candle():
    URL = f"https://financialmodelingprep.com/api/v3/historical-chart/1hour/{TICKER}?apikey={API_KEY}"
    
    # REST GET 리퀘스트를 보내고 응답(adict형태 json) 반환
    response = requests.get(url)
    data = response.json()    # 각 봉에 대해 (시가, 고가, 저가, 종가, 날짜)가 포함된 리스트
    
    # 데이터를 판다스 DataFrame(엑셀 비슷한 구조) 으로 변환
    df = pd.DataFrame(data)

    # 데이터 정렬: FMP는 최신순(내림차순)으로 온다, 봉차트는 과거→미래(오름차순)가 필요함
    df = df.iloc[::-1]                  # row 순서 뒤집기
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)

    mpf.plot(
        df[['open', 'high', 'low', 'close']],   # 캔들 입력 데이터
        type='candle',                          # 봉차트(candle) 타입
        style='yahoo',                          # 차트 스타일, 'charles', 'yahoo' 등 다양
        title=f"{TICKER} 최근 Hourly Candlestick",   # 그래프 제목
        ylabel='Price (USD)',                   # y축 단위
        savefig=IMG_FILE                        # 파일로 저장하고, 화면에 띄우지 않음
    )


def update_readme(history):
    with open(README_FILE, 'w') as f:
        f.write("## 미국 ETF 최근 30회 시세\n\n")
        f.write("![최근 시세변화](./market_chart.png)\n\n")
        f.write("| 시각(UTC) | " + " | ".join(TICKERS) + " |\n")
        f.write("| --- " * (len(TICKERS)+1) + "|\n")
        for row in history:
            nums = [f"{row.get(ticker, ''):,.2f}" for ticker in TICKERS]
            f.write(f"| {row['time']} | {' | '.join(nums)} |\n")
        f.write("## QLD CANDLESTICK CHART")
        f.write("![QLD](./qld_candlestick.png)\n\n")



if __name__ == "__main__":
    prices = fetch_quotes()        # 1. 최신 시세 수집
    history = update_history(prices)   # 2. 기록 갱신 (최근 10개로)
    make_chart(history)            # 3. 라인 그래프 그림
    get_candle()
    update_readme(history)         # 4. README.md 새로 생성/덮어쓰기
