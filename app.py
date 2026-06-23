import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_gsheets import GSheetsConnection

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

# 2. 클라우드 구글 스프레드시트 실시간 연동 (ttl=0 강제 새로고침)
try:
    st.cache_data.clear()
    conn = st.connection("gsheets", type=GSheetsConnection)
    spreadsheet_url = "https://docs.google.com/spreadsheets/d/1HekCxNYxt05v2V-sldwXcdBJHwNGzzwJddpPfvSa_Mk/edit?usp=sharing"
    df = conn.read(spreadsheet=spreadsheet_url, ttl=0)
except Exception as e:
    st.error(f"클라우드 데이터베이스 연결 실패: {e}")
    st.stop()

if df.empty:
    st.warning("데이터베이스에 표시할 데이터가 없습니다.")
    st.stop()

# 데이터 타입 무결성 정제
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

# 5. 📊 특수문자 버그를 해결한 고해상도 Plotly 비교분석 차트
st.subheader("📊 필터 기준 설비별 부동시간 분석 (비교분석 모드)")

if not filtered_df.empty:
    chart_data = filtered_df.sort_values(by="부동시간[Hr]", ascending=False).head(20)
    chart_pivot = chart_data[chart_data["부동시간[Hr]"] > 0]
    
    if not chart_pivot.empty:
        # 다크모드 전용 선명한 하늘색(#38bdf8) 테마 바 차트 빌드
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
            margin=dict(l=10, r=10, t=10, b=10)
        )
        st.plotly_chart(fig, use_container_width=True)
        st.caption("💡 그래프 기둥에 마우스 커서를 올리면 상세 수치 팝업 툴팁이 작동합니다.")
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
                new_row = pd.DataFrame([{
                    "공정": add_공정, "세부공정": add_세부, "정비일자": str(add_일자), 
                    "설비분류": add_분류, "설비명": add_설비명, "마력": add_마력, 
                    "기동방식": add_기동, "고장현상": add_고장, "조치내역": add_조치, 
                    "부동시간[Hr]": add_부동, "소요비용[천원]": add_비용, "정비자": add_정비자, "비고": add_비고
                }])
                updated_df = pd.concat([df, new_row], ignore_index=True)
                conn.update(spreadsheet=spreadsheet_url, data=updated_df)
                st.success("데이터가 성공적으로 추가되었습니다!")
                st.rerun()
                
    # [수정 기능]
    with tab2:
        if not df.empty:
            edit_index = st.selectbox("수정할 기록 선택", df.index, format_func=lambda x: f"[{x}] {df.iloc[x]['설비명']} ({df.iloc[x]['정비일자']})")
            row_to_edit = df.iloc[edit_index]
            
            with st.form("edit_form"):
                st.info(f"선택한 번호 [{edit_index}]의 데이터가 로드되었습니다.")
                
                # 가독성 분리 가공 (글자 잘림 현상 원천 차단)
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
                
                # 컴포넌트 렌더링
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
                    df.loc[edit_index, "공정"] = edit_공정
                    df.loc[edit_index, "세부공정"] = edit_세부
                    df.loc[edit_index, "정비일자"] = str(edit_일자)
                    df.loc[edit_index, "설비분류"] = edit_분류
                    df.loc[edit_index, "설비명"] = edit_설비명
                    df.loc[edit_index, "마력"] = edit_마력
                    df.loc[edit_index, "기동방식"] = edit_기동
                    df.loc[edit_index, "고장현상"] = edit_고장
                    df.loc[edit_index, "조치내역"] = edit_조치
                    df.loc[edit_index, "부동시간[Hr]"] = edit_부동
                    df.loc[edit_index, "소요비용[천원]"] = edit_비용
                    df.loc[edit_index, "정비자"] = edit_정비자
                    df.loc[edit_index, "비고"] = edit_비고
                    
                    conn.update(spreadsheet=spreadsheet_url, data=df)
                    st.success("선택한 정비 기록 수정이 완료되었습니다!")
                    st.rerun()

    # [삭제 기능]
    with tab3:
        if not df.empty:
            delete_index = st.selectbox("삭제할 이력 선택", df.index, format_func=lambda x: f"[{x}] {df.iloc[x]['설비명']} ({df.iloc[x]['정비일자']})")
            if st.button("🗑️ 선택한 정비 이력 영구 삭제"):
                updated_df = df.drop(delete_index).reset_index(drop=True)
                conn.update(spreadsheet=spreadsheet_url, data=updated_df)
                st.success("데이터가 완벽하게 제거되었습니다.")
                st.rerun()
else:
    st.warning("🔒 데이터 관리 기능을 사용하시려면 왼쪽 사이드바에 패스워드를 입력해 주세요.")
