import requests
import re
from datetime import datetime, timedelta, timezone

BOT_TOKEN = "8564601689:AAGdTnXwjMtgTZi_S6OFZl_F91G4nQUzJLY"
CHAT_ID = "6701843052"

def safe_get(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://m.stock.naver.com/'
    }
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            return res.json()
        return {}
    except:
        return {}

def parse_num(val):
    if val is None:
        return 0.0
    try:
        s = str(val).replace(',', '').strip()
        if not s or s == '-':
            return 0.0
        return float(s)
    except:
        return 0.0

def get_yahoo_price(symbol, is_rate=False):
    url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        res = requests.get(url, headers=headers, timeout=10).json()
        price = res['chart']['result'][0]['meta']['regularMarketPrice']
        if is_rate:
            return f"{price:,.1f}"
        return f"{price:,.2f}"
    except:
        return "-"

def format_money_krw(val):
    v = parse_num(val)
    if v == 0:
        return "0억"
    if abs(v) >= 10000:
        return f"{v / 10000:+.1f}조"
    else:
        return f"{v:+.0f}억"

def get_active_trend(trend_res):
    if isinstance(trend_res, list) and len(trend_res) > 0:
        for item in trend_res:
            if not isinstance(item, dict):
                continue
            f = parse_num(item.get('foreignerPureBuyQuant'))
            i = parse_num(item.get('organPureBuyQuant'))
            p = parse_num(item.get('personalPureBuyQuant'))
            if f != 0 or i != 0 or p != 0:
                return item
        if len(trend_res) > 1 and isinstance(trend_res[1], dict):
            return trend_res[1]
        return trend_res[0] if isinstance(trend_res[0], dict) else {}
    return {}

def get_deposit_and_credit():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        url = "https://finance.naver.com/sise/sise_deposit.naver"
        res = requests.get(url, headers=headers, timeout=10)
        text = res.text
        
        dep_match = re.search(r'고객예탁금.*?<td class="number">([\d,]+)</td>', text, re.DOTALL)
        cred_match = re.search(r'신용공여.*?<td class="number">([\d,]+)</td>', text, re.DOTALL)
        if not cred_match:
            cred_match = re.search(r'신용잔고.*?<td class="number">([\d,]+)</td>', text, re.DOTALL)
            
        cd_val = parse_num(dep_match.group(1)) if dep_match else 0
        cb_val = parse_num(cred_match.group(1)) if cred_match else 0
        
        cd_str = f"{cd_val / 1000000:.1f}조" if cd_val > 10000000 else "-"
        cb_str = f"{cb_val / 1000000:.1f}조" if cb_val > 10000000 else "-"
        
        return cd_str, cb_str
    except:
        return "-", "-"

def get_market_data():
    kospi_res = safe_get("https://m.stock.naver.com/api/index/KOSPI/basic")
    kospi_price = kospi_res.get('closePrice', '-')
    
    k_trend = safe_get("https://m.stock.naver.com/api/index/KOSPI/trend")
    k_data = get_active_trend(k_trend)
    k_foreign = format_money_krw(k_data.get('foreignerPureBuyQuant'))
    k_inst = format_money_krw(k_data.get('organPureBuyQuant'))
    k_personal = format_money_krw(k_data.get('personalPureBuyQuant'))

    kosdaq_res = safe_get("https://m.stock.naver.com/api/index/KOSDAQ/basic")
    kosdaq_price = kosdaq_res.get('closePrice', '-')

    kq_trend = safe_get("https://m.stock.naver.com/api/index/KOSDAQ/trend")
    kq_data = get_active_trend(kq_trend)
    kq_foreign = format_money_krw(kq_data.get('foreignerPureBuyQuant'))
    kq_inst = format_money_krw(kq_data.get('organPureBuyQuant'))
    kq_personal = format_money_krw(kq_data.get('personalPureBuyQuant'))

    samjon_res = safe_get("https://m.stock.naver.com/api/stock/005930/basic")
    hynix_res = safe_get("https://m.stock.naver.com/api/stock/000660/basic")
    samjon_price = samjon_res.get('closePrice', '-')
    hynix_price = hynix_res.get('closePrice', '-')

    usd_krw = get_yahoo_price("KRW=X", is_rate=True)
    us10y = get_yahoo_price("^TNX")
    kr3y_res = safe_get("https://m.stock.naver.com/api/marketindex/price/IRR_GOV3Y/interest/basic")
    kr3y = kr3y_res.get('closePrice', '3.18')

    kr_rate_res = safe_get("https://m.stock.naver.com/api/marketindex/price/INT_BOK/interest/basic")
    us_rate_res = safe_get("https://m.stock.naver.com/api/marketindex/price/INT_USFED/interest/basic")
    kr_rate = kr_rate_res.get('closePrice', '3.50')
    us_rate = us_rate_res.get('closePrice', '5.50')

    wti = get_yahoo_price("CL=F")
    gold = get_yahoo_price("GC=F")

    btc = get_yahoo_price("BTC-USD")
    eth = get_yahoo_price("ETH-USD")
    xrp = get_yahoo_price("XRP-USD")

    cust_deposit, credit_balance = get_deposit_and_credit()

    now_str = (datetime.now(timezone.utc) + timedelta(hours=9)).strftime("%y/%m/%d %H:%M")

    msg = f"📊 [{now_str} 증시 브리핑]\n\n"
    msg += f"🔹 [코스피] {kospi_price}\n"
    msg += f"   └ 수급: 외인{k_foreign}, 기관{k_inst}, 개인{k_personal}\n"
    msg += f"🔹 [코스닥] {kosdaq_price}\n"
    msg += f"   └ 수급: 외인{kq_foreign}, 기관{kq_inst}, 개인{kq_personal}\n\n"
    msg += f"🔹 [주요종목] 삼전 {samjon_price}원 / 하닉 {hynix_price}원\n"
    msg += f"🔹 [환율] 원/달러 {usd_krw}원\n\n"
    msg += f"🔹 [채권 금리] 美10년 {us10y}% / 韓3년 {kr3y}%\n"
    msg += f"🔹 [기준 금리] 美 {us_rate}% / 韓 {kr_rate}%\n"
    msg += f"🔹 [원자재] WTI ${wti} / 금 ${gold}\n\n"
    msg += f"🔹 [가상자산] BTC ${btc} / ETH ${eth} / XRP ${xrp}\n"
    msg += f"🔹 [증시자금] 예탁금 {cust_deposit} / 신용잔고 {credit_balance}"
    
    return msg

def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {'chat_id': CHAT_ID, 'text': text}
    requests.post(url, data=payload)

if __name__ == "__main__":
    briefing = get_market_data()
    send_telegram(briefing)
