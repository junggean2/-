import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection
from google.oauth2.service_account import Credentials

# 1. 웹 페이지 기본 설정 및 고가시성 테마 정의 (다크모드 완벽 대응)
st.set_page_config(page_title="설비 정비 이력 관리 시스템", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0f172a !important; }
    h1, h2, h3, p, span, label { color: #f8fafc !important; font-family: 'Malgun Gothic', sans-serif; }
    .stButton>button { background-color: #38bdf8 !important; color: #0f172a !important; font-weight: bold; border-radius: 6px; width: 100%; }
    .stDataFrame { border: 1px solid #334155; border-radius: 8px; }
    div[data-testid="stMetricValue"] { color: #38bdf8 !important; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

# =========================================================================
# [🔑 필수 입력 구역] 다운로드받은 구글 JSON 메모장 파일의 내용을 아래에 정확히 기입하세요.
# =========================================================================
service_account_dict = {
  "type": "service_account",
  "project_id": "carbide-ratio-500307-h9",
  "private_key_id": "2e2d65a5f566e2fa658311a93076d5e14fc1463f",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC4OHAzbW1aQW/u\nTBBxVCjcPicZUr4h/f8epBz1xWBWi4S5VLj/obnNWwjwQWWBltGzPy8J7DAihhSk\nBnnPcrIr8ovvqoCtGywCCHUzjQCl2CjDpoJNQtkS0KmXRYoUpDnXgeRcYR+M4Ckz\nE0gcN4NIht3+eiT76IfBxatUyIHOLCi0ikZiqTJJkRFG0kaCjSGoLnxUbwsLdBeD\nDpZa7AWavsxWc69Y767yDblwTz426XBaUl/z9BmhKKr169yrUqwshxMNsgMT1MSA\nvC+jq0TyMAUeF+eGXzXyXAH/iqlIy+Y613mRjnXMvZLHHavwRXcZ8enCUrNpah5w\nziKqAWNbAgMBAAECggEACltd73488iCQruiG2iA9pdg2sYVF3Dpf7/SRDj45AtSY\nMyUwu2p3vDRchclfcBAvHPE170xgjmhUW75jdcbAfpkFxgUjc9f9uuWH1UydlzVW\nYV2IoNhbxOOHTVJjB3MOL3AFiy4IrI5jspPob3Gth1PRwj9SufjiPQIkdkFJjvIz\nBvoL0qmp7Gkd+wu90kAyOWWtrrPLBczU0dpp8yEAKMLToYya/krX5aOqljZK2Ou3\nTJ74P9WVl7/hPFlOQD63YdcQMo3IP9nJO1E/65FIVGFvNRi+2r66jg8E+XFyuE9J\nKlXgp8inGckwMcaCz3tOenF0SeSY6zKxpwfsf4E7GQKBgQD0XDXMwC/xsRh/yMc2\nVRj4KWr8hixuzPzxhf+1IUBJKY7EDQH/d0LbEdG7Xa4AHmh3NT8d6yyL/a/qzCHy\nRNcCzD/Bm1HgQgqS3Ez46OpvZhlDWu9JzODud8dTfx7OKKqfkUYtaGrfVy3Ajr0y\n5X0Ua+eE4rf/W07UWEg4y70NmQKBgQDA/t56El9dbLr22kws6H5O1ZYE1XzjfVIJ\noLPf1SvNjQP0Y7DyI1hlXmf1MBAp5Zrop5M/5N6pGEUX1NijdRxlNkgUb1rD1Ku4\nmbxa6Bwah5+yRB4GFacup4eDSZtVme2wTHYG8nisoLBfwQe9lbwxyHuGylntE+9j\nZ90/itcJEwKBgQDnN4lAoGm9TFFeOGEnrAXga3BsWZkZjqWY864tebUWhVgtchF9\n5R9Bou7NV6sZOaynf56ldK3GGNmoVleYokLAxvtc+tbSWCshI4tBy0Jo/jbRYO4i\n6tW7T2MwQoynjhtEuXWp6a+WfSsxlN65liRwelmrh8uKuJ8ylgZgl4ffoQKBgGcE\nJHD4eZr+vNWjNGIMP8+IxqkR47XyYOXut9TUjqsLiH7c78hwAXEqcUc5Pod+na9u\nM3U5j3inEcpkvLaTfnKwBM2TmtlJHdhNh3LmzomCt0WKgpQw3qpSlk0H7zhED9G5\nHo8awjszErIp8R3LXUcdgoIyZMndiDyBZmHSlHGtAoGAR25u0meuNYfIoV1eW+nO\nnffVdHu+3TxtYdwONe3B9K8kkyytFNyO6Q2NlT/2nvIdUN8CbWylmnmHLje+7aQk\nnbJyyUbDknQqYB8KXEqVUasu8v1BxoqRld+yk94lpj4GStaCOQsCTsO6sxS82OAW\nQSIBwXtu/aICnPgC/SQa/rs=\n-----END PRIVATE KEY-----\n",
  "client_email": "streamlit-db@carbide-ratio-500307-h9.iam.gserviceaccount.com",
  "client_id": "109317306139225964001",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/streamlit-db%40carbide-ratio-500307-h9.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
# =========================================================================

# 2. 캐시 오류 해결을 위한 독립형 구글 크레덴셜 및 엔진 다이렉트 구성
try:
    scopes = ["https://www.googleapis.com/auth/spreadsheets"]
    creds = Credentials.from_service_account_info(service_account_dict, scopes=scopes)
    
    # [핵심 변경] 별도의 커넥션 캐싱 함수를 거치지 않고 직접 기동하여 'Cannot hash argument' 버그를 우회합니다.
    conn = GSheetsConnection(connection_name="gsheets", credentials=creds)
    spreadsheet_url = "https://docs.google.com/spreadsheets/d/1HekCxNYxt05v2V-sldwXcdBJHwNGzzwJddpPfvSa_Mk/edit?usp=sharing"
    df = conn.read(spreadsheet=spreadsheet_url, ttl=0)
except Exception as e:
    st.error(f"클라우드 데이터베이스 안전 인증 연결 실패: {e}")
    st.stop()

if df.empty:
    st.warning("데이터베이스에 표시할 데이터가 없습니다.")
    st.stop()

# 데이터 타입 무결성 정제 및 가공
df["부동시간[Hr]"] = pd.to_numeric(df["부동시간[Hr]"], errors='coerce').fillna(0.0)
df["소요비용[천원]"] = pd.to_numeric(df["소요비용[천원]"], errors='coerce').fillna(0)
df["설비명"] = df["설비명"].fillna("미지정 설비").astype(str).str.strip()
df["공정"] = df["공정"].fillna("기타").astype(str).str.strip()

if "정비일자" in df.columns:
    df["정비일자"] = pd.to_datetime(df["정비일자"], errors="coerce").dt.strftime("%Y-%m-%d")
    df["정비일자"] = df["정비일자"].fillna(pd.Timestamp.now().strftime("%Y-%m-%d"))

# 3. 사이드바 권한 제어 및 필터 설정
st.sidebar.title("🔒 권한 및 필터 제어")
password = st.sidebar.text_input("관리자 인증 비밀번호", type="password")
is_admin = (password == "kcc")

if is_admin:
    st.sidebar.success("⚡ 관리자 권한이 인증되었습니다. (추가/수정/삭제 가능)")
else:
    st.sidebar.info("👀 [조회 전용] 모드입니다. (관리자 비밀번호 필요)")

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 데이터 필터링")

process_list = sorted(list(df["공정"].unique()))
all_processes = ["전체"] + process_list
selected_process = st.sidebar.selectbox("공정 선택", all_processes, index=0)

max_hours = float(df["부동시간[Hr]"].max()) if len(df) > 0 else 100.0
selected_hours = st.sidebar.slider("최저 부동시간(Hr) 기준 설정", 0.0, max_hours + 5.0, 0.0)

# 필터 스크리닝 데이터 가공
filtered_df = df.copy()
if selected_process != "전체":
    filtered_df = filtered_df[filtered_df["공정"] == selected_process]
filtered_df = filtered_df[filtered_df["부동시간[Hr]"] >= selected_hours]

# 4. 상단 스코어보드 지표 출력
st.title("🏭 설비 정비 이력 클라우드 대시보드")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("총 정비 건수", f"{len(filtered_df)} 건")
with col2:
    st.metric("총 부동시간 합계", f"{filtered_df['부동시간[Hr]'].sum():.1f} Hr")
with col3:
    st.metric("총 소요비용 합계", f"{filtered_df['소요비용[천원]'].sum():,.0f} 천원")

st.markdown("---")

# 5. 📊 특수문자 버그를 완전히 해결한 대조 차트 빌드
st.subheader("📊 필터 기준 설비별 부동시간 분석 (비교분석 모드)")

if not filtered_df.empty:
    chart_data = filtered_df.sort_values(by="부동시간[Hr]", ascending=False).head(20)
    chart_pivot = chart_data[chart_data["부동시간[Hr]"] > 0]
    
    if not chart_pivot.empty:
        fig = px.bar(
            chart_pivot, 
            x="설비명", 
            y="부동시간[Hr]",
            template="plotly_dark",
            text="부동시간[Hr]"
        )
        fig.update_traces(
            marker_color="#38bdf8", 
            texttemplate='%{text}Hr', 
            textposition='outside'
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,
