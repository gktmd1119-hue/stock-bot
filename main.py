import requests
import re
from datetime import datetime, timedelta, timezone

BOT_TOKEN = "8564601689:AAGdTnXwjMtgTZi_S6OFZl_F91G4nQUzJLY"
CHAT_ID = "6701843052"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'application/json, text/plain, */*',
    'Accept-Language': 'ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7',
    'Referer': 'https://m.stock.naver.com/'
}

def parse_num(val):
    if val is None:
        return 0.0
    try:
        s = str(val).replace(',', '').strip()
        if not s or s == '-':
            return 0.0
        return float(s)
    except:
        return 0.0

def safe_get(url):
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        if res.status_code == 200:
            return res.json()
        return {}
    except:
        return {}

def get_yahoo_price(symbol, is_rate=False):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10).json()
        price = res['chart']['result'][0]['meta']['regularMarketPrice']
        if is_rate:
            return f"{price:,.1f}"
        return f"{price:,.2f}"
    except:
        return "-"

def format_money_krw(val):
    v = parse_num(val)
    if v == 0:
        return "0억"
    if abs(v) >= 10000:
        return f"{v / 10000:+.1f}조"
    else:
        return f"{v:+.0f}억"

# 새로운 trend API 응답 처리 (단순 객체)
def get_active_trend(trend_res):
    if not isinstance(trend_res, dict):
        return 0.0, 0.0, 0.0

    f = parse_num(trend_res.get('foreignValue'))
    i = parse_num(trend_res.get('institutionalValue'))
    p = parse_num(trend_res.get('personalValue'))
    return f, i, p

def get_deposit_and_credit():
    try:
        url = "https://finance.naver.com/sise/sise_deposit.naver"
        res = requests.get(url, headers=HEADERS, timeout=10)
        text = res.content.decode('euc-kr', 'ignore')

        # 실제 HTML 테이블에서 최신 행 추출
        # 예: <td>26.07.28</td><td>1,071,994</td><td>19,680</td>...
        match = re.search(
            r'(\d{2}\.\d{2}\.\d{2})</td>\s*<td[^>]*>\s*([\d,]+)</td>\s*<td[^>]*>\s*([\d,]+)',
            text
        )

        if not match:
            # 백업 패턴 (공백/줄바꿈 더 유연하게)
            match = re.search(
                r'(\d{2}\.\d{2}\.\d{2})\D+([\d,]+)\D+([\d,]+)',
                text
            )

        if match:
            cd_val = parse_num(match.group(2))  # 고객예탁금 (억원)
            cb_val = parse_num(match.group(3))  # 신용잔고 (억원)

            cd_str = f"{cd_val / 10000:.1f}조" if cd_val > 0 else "-"
            cb_str = f"{cb_val / 10000:.1f}조" if cb_val > 0 else "-"
            return cd_str, cb_str

        return "-", "-"
    except Exception as e:
        print("예탁금 파싱 에러:", e)  # 디버깅용
        return "-", "-"

def get_kr_stock_price(code):
    """KRX 종가 + NXT(오버마켓) 가격 반영"""
    res = safe_get(f"https://m.stock.naver.com/api/stock/{code}/basic")
    close = res.get('closePrice', '-')
    
    # NXT / After Market 가격이 있으면 우선 사용
    over_info = res.get('overMarketPriceInfo', {})
    over_price = over_info.get('overPrice')
    
    if over_price:
        return f"{over_price} (NXT)"
    return close

def get_market_data():
    # ===== 한국 지수 =====
    kospi_res = safe_get("https://m.stock.naver.com/api/index/KOSPI/basic")
    kospi_price = kospi_res.get('closePrice', '-')
    
    k_trend = safe_get("https://m.stock.naver.com/api/index/KOSPI/trend")
    kf, ki, kp = get_active_trend(k_trend)
    k_foreign = format_money_krw(kf)
    k_inst = format_money_krw(ki)
    k_personal = format_money_krw(kp)

    kosdaq_res = safe_get("https://m.stock.naver.com/api/index/KOSDAQ/basic")
    kosdaq_price = kosdaq_res.get('closePrice', '-')

    kq_trend = safe_get("https://m.stock.naver.com/api/index/KOSDAQ/trend")
    kqf, kqi, kqp = get_active_trend(kq_trend)
    kq_foreign = format_money_krw(kqf)
    kq_inst = format_money_krw(kqi)
    kq_personal = format_money_krw(kqp)

    # ===== 미국 지수 =====
    nasdaq = get_yahoo_price("^IXIC")
    sp500 = get_yahoo_price("^GSPC")
    dow = get_yahoo_price("^DJI")

    # ===== 한국 주요종목 (NXT 반영) =====
    samjon = get_kr_stock_price("005930")
    hynix = get_kr_stock_price("000660")

    # ===== 미국 주요종목 =====
    aapl = get_yahoo_price("AAPL")
    googl = get_yahoo_price("GOOGL")
    nvda = get_yahoo_price("NVDA")
    tsla = get_yahoo_price("TSLA")
    mu = get_yahoo_price("MU")

    # ===== 기타 =====
    usd_krw = get_yahoo_price("KRW=X", is_rate=True)
    us10y = get_yahoo_price("^TNX")
    kr3y_res = safe_get("https://m.stock.naver.com/api/marketindex/price/IRR_GOV3Y/interest/basic")
    kr3y = kr3y_res.get('closePrice', '3.18')

    kr_rate_res = safe_get("https://m.stock.naver.com/api/marketindex/price/INT_BOK/interest/basic")
    us_rate_res = safe_get("https://m.stock.naver.com/api/marketindex/price/INT_USFED/interest/basic")
    kr_rate = kr_rate_res.get('closePrice', '3.50')
    us_rate = us_rate_res.get('closePrice', '5.50')

    wti = get_yahoo_price("CL=F")
    gold = get_yahoo_price("GC=F")

    cust_deposit, credit_balance = get_deposit_and_credit()

    now_str = (datetime.now(timezone.utc) + timedelta(hours=9)).strftime("%y/%m/%d %H:%M")

    msg = f"📊 [{now_str} 증시 브리핑]\n\n"
    
    msg += f"🔹 [코스피] {kospi_price}\n"
    msg += f"   └ 수급: 외인{k_foreign}, 기관{k_inst}, 개인{k_personal}\n"
    msg += f"🔹 [코스닥] {kosdaq_price}\n"
    msg += f"   └ 수급: 외인{kq_foreign}, 기관{kq_inst}, 개인{kq_personal}\n\n"
    
    msg += f"🔹 [미국지수] 나스닥 {nasdaq} / S&P500 {sp500} / 다우 {dow}\n\n"
    
    msg += f"🔹 [한국 주요종목]\n"
    msg += f"   삼전 {samjon}원 / 하닉 {hynix}원\n"
    
    msg += f"🔹 [미국 주요종목]\n"
    msg += f"   애플 ${aapl} / 구글 ${googl}\n"
    msg += f"   엔비디아 ${nvda} / 테슬라 ${tsla} / 마이크론 ${mu}\n\n"
    
    msg += f"🔹 [환율] 원/달러 {usd_krw}원\n"
    msg += f"🔹 [채권 금리] 美10년 {us10y}% / 韓3년 {kr3y}%\n"
    msg += f"🔹 [기준 금리] 美 {us_rate}% / 韓 {kr_rate}%\n"
    msg += f"🔹 [원자재] WTI ${wti} / 금 ${gold}\n\n"
    msg += f"🔹 [증시자금] 예탁금 {cust_deposit} / 신용잔고 {credit_balance}"
    
    return msg

def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': text}
    requests.post(url, data=payload)

if __name__ == "__main__":
    briefing = get_market_data()
    send_telegram(briefing)
