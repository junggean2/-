import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 1. 웹 페이지 기본 설정 및 고가시성 테마 강제 정의 (다크모드 완벽 대응)
st.set_page_config(page_title="설비 정비 이력 관리 시스템", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0f172a !important; }
    h1, h2, h3, p, span { color: #f8fafc !important; font-family: 'Malgun Gothic', sans-serif; }
    .stButton>button { background-color: #38bdf8 !important; color: #0f172a !important; font-weight: bold; border-radius: 6px; width: 100%; }
    .stDataFrame { border: 1px solid #334155; border-radius: 8px; }
    div[data-testid="stMetricValue"] { color: #38bdf8 !important; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# 2. 클라우드 구글 스프레드시트 실시간 동기화 연동
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    spreadsheet_url = "https://docs.google.com/spreadsheets/d/1HekCxNYxt05v2V-sldwXcdBJHwNGzzwJddpPfvSa_Mk/edit?usp=sharing"
    df = conn.read(spreadsheet=spreadsheet_url, ttl="0")
except Exception as e:
    st.error(f"클라우드 데이터베이스 연결 실패: {e}")
    st.stop()

if df.empty:
    st.warning("데이터베이스에 표시할 데이터가 없습니다.")
    st.stop()

# 데이터 타입 강제 정제 및 누락값 제거
df["부동시간[Hr]"] = pd.to_numeric(df["부동시간[Hr]"], errors='coerce').fillna(0.0)
df["소요비용[천원]"] = pd.to_numeric(df["소요비용[천원]"], errors='coerce').fillna(0)
df["설비명"] = df["설비명"].fillna("미지정 설비").astype(str)
df["공정"] = df["공정"].fillna("기타").astype(str)

# 3. 사이드바 권한 분리 및 필터 설정
st.sidebar.title("🔒 권한 및 필터 제어")
password = st.sidebar.text_input("관리자 인증 비밀번호", type="password")
is_admin = (password == "kcc")

if is_admin:
    st.sidebar.success("⚡ 관리자 권한이 인증되었습니다. (추가/수정/삭제 가능)")
else:
    st.sidebar.info("👀 [조회 전용] 모드입니다. (관리자 비밀번호 필요)")

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 데이터 필터링")

all_processes = ["전체"] + list(df["공정"].dropna().unique())
selected_process = st.sidebar.selectbox("공정 선택", all_processes)

max_hours = float(df["부동시간[Hr]"].max()) if len(df) > 0 else 100.0
selected_hours = st.sidebar.slider("최저 부동시간(Hr) 기준 설정", 0.0, max_hours + 5.0, 0.0)

# 필터링 조건 스크리닝
filtered_df = df.copy()
if selected_process != "전체":
    filtered_df = filtered_df[filtered_df["공정"] == selected_process]
filtered_df = filtered_df[filtered_df["부동시간[Hr]"] >= selected_hours]

# 4. 메인 대시보드 요약 지표 (KPI)
st.title("🏭 설비 정비 이력 클라우드 대시보드")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("총 정비 건수", f"{len(filtered_df)} 건")
with col2:
    st.metric("총 부동시간 합계", f"{filtered_df['부동시간[Hr]'].sum():.1f} Hr")
with col3:
    st.metric("총 소요비용 합계", f"{filtered_df['소요비용[천원]'].sum():,.0f} 천원")

st.markdown("---")

# 5. 📊 야간/다크모드에서도 뚜렷하게 튀어나오는 비교분석용 차트 빌드
st.subheader("📊 필터 기준 설비별 부동시간 분석 (비교분석 모드)")

if not filtered_df.empty:
    # 가시성을 위해 부동시간이 높은 설비 순서대로 데이터셋 정렬
    chart_data = filtered_df.sort_values(by="부동시간[Hr]", ascending=False).head(20)
    
    # 엑셀 시트 안에서 0이 아닌 유의미한 부동시간을 가진 설비들만 그래프에 표현
    chart_pivot = chart_data[chart_data["부동시간[Hr]"] > 0].pivot_table(index="설비명", values="부동시간[Hr]", aggfunc="sum")
    
    if not chart_pivot.empty:
        # 다크 테마에서 시인성이 보장되는 밝은 하늘색(#38bdf8)으로 그래프 기둥 지정
        st.bar_chart(chart_pivot, y="부동시간[Hr]", color="#38bdf8", height=400)
        st.caption("💡 그래프 기둥에 마우스를 올리면 실시간으로 해당 설비의 정확한 수치 팝업이 작동합니다.")
    else:
        st.info("현재 선택된 공정의 설비들은 모두 부동시간이 0 Hr 이므로 차트를 표시하지 않습니다.")
else:
    st.warning("선택하신 필터 조건에 부합하는 데이터가 없습니다.")

st.markdown("---")

# 6. 실시간 정비 이력 데이터 테이블 (최신 규격 반영)
st.subheader("📋 실시간 정비 데이터 테이블")
st.dataframe(filtered_df, width="stretch")

# 7. 관리자 전용 제어 센터 (비밀번호 입력 여부와 상관없이 위치 고정 배치)
st.markdown("---")
st.subheader("🛠️ 데이터 관리 커맨드 센터")

if is_admin:
    tab1, tab2, tab3 = st.tabs(["➕ 새 정비 이력 추가", "✏️ 기존 기록 수정", "❌ 기존 기록 삭제"])
    
    # [추가]
    with tab1:
        with st.form("add_form", clear_on_submit=True):
            c1, c2, c3, c4 = st.columns(4)
            add_공정 = c1.selectbox("공정", ["파쇄", "선광", "채광", "제련"])
            add_세부 = c2.text_input("세부공정")
            add_일자 = c3.date_input("정비일자")
            add_분류 = c4.selectbox("설비분류", ["대", "중", "소"])
            
            c5, c6, c7, c8 = st.columns(4)
            add_설비명 = c5.text_input("설비명")
            add_마력 = c6.number_input("마력(HP)", min_value=0, value=50)
            add_기동 = c7.text_input("기동방식")
            add_고장 = c8.text_input("고장현상")
            
            c9, c10, c11, c12 = st.columns(4)
            add_조치 = c9.text_area("조치내역")
            add_부동 = c10.number_input("부동시간[Hr]", min_value=0.0, step=0.1)
            add_비용 = c11.number_input("소요비용[천원]", min_value=0)
            add_정비자 = c12.text_input("정비자")
            add_비고 = st.text_input("비고")
            
            if st.form_submit_button("💾 구글 클라우드 데이터베이스에 즉시 추가 저장"):
                new_row = pd.DataFrame([{
                    "공정": add_공정, "세부공정": add_세부, "정비일자": str(add_일자), 
                    "설비분류": add_분류, "설비명": add_설비명, "마력": add_마력, 
                    "기동방식": add_기동, "고장현상": add_고장, "조치내역": add_조치, 
                    "부동시간[Hr]": add_부동,
