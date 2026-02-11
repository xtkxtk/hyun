import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
from streamlit_gsheets import GSheetsConnection

# --- 1. 환경 설정 ---
KST_OFFSET = timedelta(hours=9)
VOLATILITY = 0.1  # 10% 변동폭
price = None
# 종목별 초기 설정 (종목명: [초기값, 고정시드])
STOCKS = {
    "hyungi": {"base": 100, "seed": 777},
    "kkong": {"base": 100, "seed": 888}
}
conn = st.connection("gsheets", type=GSheetsConnection)
df = conn.read(worksheet="data", ttl=0)
st.success("데이터 로드 성공!")
st.error("한우가 만든 거래소입니다. 현기는 내꺼입니다. 😵😻")
st.warning("계좌 생성, 오류 신고는 디스코드에서 해주세요.")
st.write("---")
#st.dataframe(df)

# --- 2. 핵심 로직 함수화 ---

def get_kst_now():
    """현재 한국 시간을 반환"""
    return datetime.utcnow() + KST_OFFSET

def get_popularity(stock_name):
    filtered_df = df.loc[df["NAME"] == stock_name, "WON"]
    return int(filtered_df.values[0])

@st.cache_data(ttl=60) # 1분간 결과 캐싱 (성능 최적화)
def generate_stock_data(stock_name, days=7):
    """특정 종목의 일주일치 시세를 생성"""
    config = STOCKS[stock_name]
    now = get_kst_now()
    # 시작 시간 설정 (정각 기준)
    start_time = (now - timedelta(days=days)).replace(minute=0, second=0, microsecond=0)
    
    prices = []
    times = []
    current_p = config["base"]
    
    step_time = start_time
    while step_time <= now:
        # 시간 + 종목 고정 시드로 유일한 시드 생성
        seed_id = int(step_time.strftime('%Y%m%d%H')) + config["seed"]
        random.seed(seed_id)
        
        # 변동폭 계산 (±10%)
        change_pct = random.uniform(-VOLATILITY, VOLATILITY)
        current_p = current_p * (1 + change_pct)
        
        prices.append(round(current_p))
        times.append(step_time.strftime('%m/%d %H:%M'))
        step_time += timedelta(hours=1)
        
    return pd.DataFrame({"시세": prices}, index=times)

def exchange(stock_name, amount, action, user_id, user_pw):
    """종목 매수/매도 처리"""
    global df, price
    if action not in ["buy", "sell"]:
        raise ValueError("action은 'buy' 또는 'sell'이어야 합니다.")
    
    current = df.loc[df["NAME"] == user_id]
    
    if current[stock_name].values[0] - amount < 0 and action == "sell":
        raise ValueError("보유 주식 수가 부족합니다.")
    if current["WON"].values[0] < amount * price and action == "buy":
        raise ValueError("보유 현금이 부족합니다.")
    
    df.loc[df["NAME"] == user_id, "WON"] -= amount * price if action == "buy" else -amount * price
    df.loc[df["NAME"] == user_id, stock_name] += amount if action == "buy" else -amount
    conn.update(data=df)

# --- 3. UI 렌더링 함수 ---

def exchange_ui(stock_name):
    """종목별 거래 기능"""
    st.subheader("종목 거래")
    st.write("로그인이 필요합니다.")
    id = st.text_input("이름 입력 (예: 하음)", key=f"id_{stock_name}")
    pw = st.text_input("비밀번호 입력 (예: 123456)", type="password", key=f"pw_{stock_name}")

    if not id or not pw:
        st.info("아이디와 비밀번호를 입력해주세요.")
    elif str(int(df.loc[df["NAME"] == id, "PW"].values[0])) != str(pw):
        st.error("아이디 또는 비밀번호가 잘못되었습니다.")
    else:
        st.success("로그인 성공!")
        amount = st.number_input("거래 수량 입력", min_value=1, step=1, key=f"amount_{stock_name}")
        col1, col2 = st.columns(2)
        with col1:
            if st.button(f"💰 {stock_name.upper()} 매수", key=f"buy_{stock_name}"):
                try:
                    exchange(stock_name, amount, "buy", id, pw)
                    st.success(f"{amount}주 매수 완료!")
                except Exception as e:
                    st.error(f"매수 실패: {e}")
        with col2:
            if st.button(f"💸 {stock_name.upper()} 매도", key=f"sell_{stock_name}"):
                try:
                    exchange(stock_name, amount, "sell", id, pw)
                    st.success(f"{amount}주 매도 완료!")
                except Exception as e:
                    st.error(f"매도 실패: {e}")

def display_stock_info(stock_name):
    global price
    """종목별 대시보드 표시"""
    df = generate_stock_data(stock_name)
    popular=get_popularity(stock_name)
    current_price1 = df["시세"].iloc[-1]
    current_price2 = max(df["시세"].iloc[-1]+popular*5,0)
    prev_price = df["시세"].iloc[-2] if len(df) > 1 else current_price1
    delta = current_price2 - prev_price
    
    # 상단 지표
    st.metric(label=f"{stock_name.upper()} 현재가", 
              value=f"{current_price1:,}원 + 평가지수 {popular*5:,}원 = {current_price2:,}원", 
              delta=f"{delta:,}원 (전시간 대비)")
    
    price = current_price2

    
    # 차트
    st.line_chart(df)

# --- 4. 메인 화면 ---

st.set_page_config(page_title="현기 거래소")
st.title("📈 현기거래소 v2")

# 탭을 사용하여 종목 분리
tab1, tab2 = st.tabs(["😵 HYUNGI", "😻 KKONG"])

with tab1:
    display_stock_info("hyungi")
    exchange_ui("hyungi")

with tab2:
    display_stock_info("kkong")
    exchange_ui("kkong")

st.caption(f"최종 업데이트 (KST): {get_kst_now().strftime('%Y-%m-%d %H:%M:%S')}")