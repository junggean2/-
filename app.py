import streamlit as st
import pandas as pd
import plotly.express as px
import gspread
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

# 2. 버그가 많은 st.connection 대신 gspread 공식 라이브러리로 다이렉트 보안 연결 채널 구축
try:
    st.cache_data.clear()
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(service_account_dict, scopes=scopes)
    client = gspread.authorize(creds)
    
    # 구글 스프레드시트 고유 ID를 사용하여 직접 시트 열기
    spreadsheet_id = "1HekCxNYxt05v2V-sldwXcdBJHwNGzzwJddpPfvSa_Mk"
    sheet = client.open_by_key(spreadsheet_id).sheet1
    
    # 실시간 데이터 전체 로드 및 판다스 변환
    records = sheet.get_all_records()
    df = pd.DataFrame(records)
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

# 5. 📊 특수문자 버그를 완전히 해결한 고해상도 Plotly 비교분석 차트
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
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=10, r=10, t=30, b=10)
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption("💡 그래프 기둥에 마우스 커서를 올리면 해당 설비의 정확한 수치 데이터가 즉시 팝업됩니다.")
    else:
        st.info("선택된 필터 조건 내에 부동시간(Hr)이 발생한 설비가 없어 차트를 비워둡니다.")
else:
    st.warning("선택하신 필터 조건에 부합하는 데이터가 존재하지 않습니다.")

st.markdown("---")

# 6. 데이터 테이블 화면 출력
st.subheader("📋 실시간 정비 데이터 테이블")
st.dataframe(filtered_df, width="stretch")

# 7. 데이터 제어 커맨드 센터 (추가 / 수정 / 삭제)
st.markdown("---")
st.subheader("🛠️ 데이터 관리 커맨드 센터")

if is_admin:
    tab1, tab2, tab3 = st.tabs(["➕ 새 정비 이력 추가", "✏️ 기존 기록 수정", "❌ 기존 기록 삭제"])
    
    # [추가 기능]
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
                new_row = [
                    add_공정, add_세부, str(add_일자), add_분류, add_설비명, 
                    add_마력, add_기동, add_고장, add_조치, add_부동, add_비용, add_정비자, add_비고
                ]
                # gspread 전용 행 추가 명령 실행
                sheet.append_row(new_row)
                st.success("데이터가 구글 시트에 성공적으로 추가되었습니다!")
                st.rerun()
                
    # [수정 기능]
    with tab2:
        if not df.empty:
            edit_index = st.selectbox("수정할 기록 선택", df.index, format_func=lambda x: f"[{x}] {df.iloc[x]['설비명']} ({df.iloc[x]['정비일자']})")
            row_to_edit = df.iloc[edit_index]
            
            with st.form("edit_form"):
                st.info(f"선택한 번호 [{edit_index}]의 데이터가 로드되었습니다.")
                
                val_공정 = row_to_edit["공정"] if row_to_edit["공정"] in ["파쇄", "선광", "채광", "제련"] else "파쇄"
                val_세부 = str(row_to_edit["세부공정"]) if pd.notna(row_to_edit["세부공정"]) else ""
                val_설비명 = str(row_to_edit["설비명"])
                val_마력 = int(row_to_edit["마력"]) if pd.notna(row_to_edit["마력"]) else 0
                val_기동 = str(row_to_edit["기동방식"]) if pd.notna(row_to_edit["기동방식"]) else ""
                val_고장 = str(row_to_edit["고장현상"]) if pd.notna(row_to_edit["고장현상"]) else ""
                val_조치 = str(row_to_edit["조치내역"]) if pd.notna(row_to_edit["조치내역"]) else ""
                val_부동 = float(row_to_edit["부동시간[Hr]"])
                val_비용 = int(row_to_edit["소요비용[천원]"])
                val_정비자 = str(row_to_edit["정비자"]) if pd.notna(row_to_edit["정비자"]) else ""
                val_비고 = str(row_to_edit["비고"]) if pd.notna(row_to_edit["비고"]) else ""
                
                try: val_일자 = pd.to_datetime(row_to_edit["정비일자"]).date()
                except: val_일자 = pd.Timestamp.now().date()
                
                ec1, ec2, ec3, ec4 = st.columns(4)
                edit_공정 = ec1.selectbox("공정", ["파쇄", "선광", "채광", "제련"], index=["파쇄", "선광", "채광", "제련"].index(val_공정))
                edit_세부 = ec2.text_input("세부공정", value=val_세부)
                edit_일자 = ec3.date_input("정비일자", value=val_일자)
                
                val_분류 = row_to_edit["설비분류"] if row_to_edit["설비분류"] in ["대", "중", "소"] else "대"
                edit_분류 = ec4.selectbox("설비분류", ["대", "중", "소"], index=["대", "중", "소"].index(val_분류))
                
                ec5, ec6, ec7, ec8 = st.columns(4)
                edit_설비명 = ec5.text_input("설비명", value=val_설비명)
                edit_마력 = ec6.number_input("마력(HP)", min_value=0, value=val_마력)
                edit_기동 = ec7.text_input("기동방식", value=val_기동)
                edit_고장 = ec8.text_input("고장현상", value=val_고장)
                
                ec9, ec10, ec11, ec12 = st.columns(4)
                edit_조치 = ec9.text_area("조치내역", value=val_조치)
                edit_부동 = ec10.number_input("부동시간[Hr]", min_value=0.0, step=0.1, value=val_부동)
                edit_비용 = ec11.number_input("소요비용[천원]", min_value=0, value=val_비용)
                edit_정비자 = ec12.text_input("정비자", value=val_정비자)
                
                edit_비고 = st.text_input("비고", value=val_비고)
                
                if st.form_submit_button("✏️ 구글 클라우드에 수정 내용 반영하기"):
                    # 구글 시트는 엑셀처럼 1부터 시작하고 헤더가 1이므로 데이터 인덱스에 +2를 해야 정확한 행 번호가 됩니다.
                    sheet_row_num = int(edit_index) + 2
                    
                    # 수정한 내용을 리스트로 결합
                    updated_row = [
                        edit_공정, edit_세부, str(edit_일자), edit_분류, edit_설비명,
                        edit_마력, edit_기동, edit_고장, edit_조치, edit_부동, edit_비용, edit_정비자, edit_비고
                    ]
                    
                    # gspread 전용 특정 행 업데이트 명령 수행
                    sheet.update(range_name=f"A{sheet_row_num}:M{sheet_row_num}", values=[updated_row])
                    st.success("구글 클라우드에 수정 내용이 완벽하게 반영되었습니다!")
                    st.rerun()

    # [삭제 기능]
    with tab3:
        if not df.empty:
            delete_index = st.selectbox("삭제할 이력 선택", df.index, format_func=lambda x: f"[{x}] {df.iloc[x]['설비명']} ({df.iloc[x]['정비일자']})")
            if st.button("🗑️ 선택한 정비 이력 영구 삭제"):
                sheet_row_num = int(delete_index) + 2
                # gspread 전용 행 삭제 함수 호출
                sheet.delete_rows(sheet_row_num)
                st.success("데이터가 구글 클라우드에서 영구 제거되었습니다.")
                st.rerun()
else:
    st.warning("🔒 데이터 관리 기능을 사용하시려면 왼쪽 사이드바에 패스워드를 입력해 주세요.")
