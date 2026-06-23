import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

# 1. 웹 페이지 기본 설정 및 고가시성 테마 적용
st.set_page_config(page_title="설비 정비 이력 관리 시스템", layout="wide")

# 가시성 확보를 위해 눈이 피로한 알록달록한 색상을 배제하고 차분한 네이비/그레이 톤 적용
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    h1 { color: #0f172a; font-family: 'Malgun Gothic', sans-serif; font-weight: 700; }
    .stButton>button { background-color: #0f172a; color: white; border-radius: 6px; width: 100%; }
    .stDataFrame { border: 1px solid #e2e8f0; border-radius: 8px; }
    </style>
""", unsafe_allow_html=True)

# 2. 클라우드 구글 스프레드시트 실시간 동기화 연동
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
    # 방금 생성된 구글 스프레드시트의 주소입니다.
    spreadsheet_url = "https://docs.google.com/spreadsheets/d/1HekCxNYxt05v2V-sldwXcdBJHwNGzzwJddpPfvSa_Mk/edit?usp=sharing"
    df = conn.read(spreadsheet=spreadsheet_url, ttl="0")
except Exception as e:
    st.error(f"클라우드 데이터베이스 연결 실패: {e}")
    st.stop()

# 3. 사이드바: 관리자 권한 분리 및 필터 구성
st.sidebar.title("🔒 권한 및 필터 제어")

# 비밀번호 'kcc' 입력 시에만 관리자 기능 활성화
password = st.sidebar.text_input("관리자 인증 비밀번호", type="password", help="추가 및 삭제를 하려면 비밀번호를 입력하세요.")
is_admin = (password == "kcc")

if is_admin:
    st.sidebar.success("⚡ 관리자 권한이 인증되었습니다. (수정/삭제 가능)")
else:
    st.sidebar.info("👀 [조회 전용] 모드입니다. (관리자 비밀번호 필요)")

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 데이터 필터링")

# 공정 필터
all_processes = ["전체"] + list(df["공정"].dropna().unique())
selected_process = st.sidebar.selectbox("공정 선택", all_processes)

# 데이터 타입 정제 (에러 방지)
df["부동시간[Hr]"] = pd.to_numeric(df["부동시간[Hr]"], errors='coerce').fillna(0)
df["소요비용[천원]"] = pd.to_numeric(df["소요비용[천원]"], errors='coerce').fillna(0)

# 부동시간 필터
max_hours = float(df["부동시간[Hr]"].max()) if len(df) > 0 else 100.0
selected_hours = st.sidebar.slider("최저 부동시간(Hr) 기준 설정", 0.0, max_hours + 5.0, 0.0)

# 필터링 조건 적용
filtered_df = df.copy()
if selected_process != "전체":
    filtered_df = filtered_df[filtered_df["공정"] == selected_process]
filtered_df = filtered_df[filtered_df["부동시간[Hr]"] >= selected_hours]

# 4. 메인 대시보드 화면 구성
st.title("🏭 설비 정비 이력 클라우드 대시보드")
st.markdown("인터넷이 연결된 환경이라면 누구나 동일한 정비 현황 데이터를 실시간으로 조회합니다.")

# 한눈에 들어오는 핵심 요약 지표 (KPI)
col1, col2, col3 = st.columns(3)
with col1:
    st.metric("총 정비 건수", f"{len(filtered_df)} 건")
with col2:
    st.metric("총 부동시간 합계", f"{filtered_df['부동시간[Hr]'].sum():.1f} Hr")
with col3:
    st.metric("총 소요비용 합계", f"{filtered_df['소요비용[천원]'].sum():,.0f} 천원")

st.markdown("---")

# 5. 그래프 시각화 (커서를 가져다 대면 상세 수치 팝업)
st.subheader("📊 필터 기준 설비별 부동시간 분석")
if not filtered_df.empty:
    fig = px.bar(
        filtered_df, 
        x="설비명", 
        y="부동시간[Hr]", 
        color="공정",
        title="설비별 부동시간 현황 (마우스를 올리면 상세 고장현상 및 조치내역이 나타납니다)",
        text="부동시간[Hr]",
        hover_data=["세부공정", "고장현상", "정비자", "조치내역"],
        color_discrete_sequence=["#1e293b", "#475569", "#64748b", "#94a3b8"] # 무채색 톤 디자인
    )
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#0f172a"),
        margin=dict(l=20, r=20, t=40, b=20)
    )
    fig.update_traces(texttemplate='%{text}Hr', textposition='outside')
    st.plotly_chart(fig, use_container_width=True)
else:
    st.warning("선택하신 필터 조건에 부합하는 정비 데이터가 없습니다.")

st.markdown("---")

# 6. 실시간 정비 이력 데이터 테이블
st.subheader("📋 실시간 정비 데이터 테이블")
st.dataframe(filtered_df, use_container_width=True)

# 7. 관리자 전용 제어 기능 (구글 스프레드시트 쓰기/삭제 기능)
if is_admin:
    st.markdown("---")
    st.subheader("🛠️ 데이터 관리 커맨드 센터 (관리자 인증 완료)")
    
    tab1, tab2 = st.tabs(["➕ 새 정비 이력 추가", "❌ 기존 기록 삭제"])
    
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
                    "부동시간[Hr]": add_부동, "소요비용[천원]": add_비용, "정비자": add_정비자, "비고": add_비고
                }])
                updated_df = pd.concat([df, new_row], ignore_index=True)
                conn.update(spreadsheet=spreadsheet_url, data=updated_df)
                st.success("구글 스프레드시트에 실시간 저장이 완료되었습니다!")
                st.rerun()
                
    with tab2:
        if not df.empty:
            delete_index = st.selectbox("삭제할 이력 선택", df.index, format_func=lambda x: f"[{x}] {df.iloc[x]['설비명']} ({df.iloc[x]['정비일자']})")
            if st.button("🗑️ 선택한 정비 이력 영구 삭제"):
                updated_df = df.drop(delete_index).reset_index(drop=True)
                conn.update(spreadsheet=spreadsheet_url, data=updated_df)
                st.success("구글 클라우드에서 데이터가 성공적으로 제거되었습니다.")
                st.rerun()
