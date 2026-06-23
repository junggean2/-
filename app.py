import streamlit as st
import pandas as pd
from streamlit_chartjs import st_chartjs
from streamlit_gsheets import GSheetsConnection

# 1. 웹 페이지 기본 설정 및 디자인 테마 정의
st.set_page_config(page_title="설비 정비 이력 관리 시스템", layout="wide")

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
    spreadsheet_url = "https://docs.google.com/spreadsheets/d/1HekCxNYxt05v2V-sldwXcdBJHwNGzzwJddpPfvSa_Mk/edit?usp=sharing"
    df = conn.read(spreadsheet=spreadsheet_url, ttl="0")
except Exception as e:
    st.error(f"클라우드 데이터베이스 연결 실패: {e}")
    st.stop()

if df.empty:
    st.warning("데이터베이스에 표시할 데이터가 없습니다.")
    st.stop()

# 데이터 타입 강제 정제 및 누락 데이터 보정
df["부동시간[Hr]"] = pd.to_numeric(df["부동시간[Hr]"], errors='coerce').fillna(0)
df["소요비용[천원]"] = pd.to_numeric(df["소요비용[천원]"], errors='coerce').fillna(0)
df["설비명"] = df["설비명"].fillna("미지정 설비")
df["공정"] = df["공정"].fillna("기타")

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

filtered_df = df.copy()
if selected_process != "전체":
    filtered_df = filtered_df[filtered_df["공정"] == selected_process]
filtered_df = filtered_df[filtered_df["부동시간[Hr]"] >= selected_hours]

# 4. 메인 대시보드 스코어보드 (KPI)
st.title("🏭 설비 정비 이력 클라우드 대시보드")

col1, col2, col3 = st.columns(3)
with col1:
    st.metric("총 정비 건수", f"{len(filtered_df)} 건")
with col2:
    st.metric("총 부동시간 합계", f"{filtered_df['부동시간[Hr]'].sum():.1f} Hr")
with col3:
    st.metric("총 소요비용 합계", f"{filtered_df['소요비용[천원]'].sum():,.0f} 천원")

st.markdown("---")

# 5. 📊 Chart.js 기반 비교분석 최적화 차트 빌드
st.subheader("📊 필터 기준 설비별 부동시간 분석 (Chart.js)")

if not filtered_df.empty:
    # 대형 설비 위주 비교분석을 위해 부동시간 기준 내림차순 정렬
    chart_data = filtered_df.sort_values(by="부동시간[Hr]", ascending=False).head(20)
    labels = chart_data["설비명"].tolist()
    values = chart_data["부동시간[Hr]"].tolist()
    
    # 가시성 확보 및 눈 피로 방지를 위한 단일 차분한 슬레이트 블루 톤
    chart_config = {
        "type": "bar",
        "data": {
            "labels": labels,
            "datasets": [{
                "label": "부동시간 [단위: Hr]",
                "data": values,
                "backgroundColor": "rgba(30, 41, 59, 0.8)", # Slate Navy
                "borderColor": "rgba(30, 41, 59, 1)",
                "borderWidth": 1,
                "borderRadius": 4
            }]
        },
        "options": {
            "responsive": True,
            "maintainAspectRatio": False,
            "plugins": {
                "legend": {"display": True, "labels": {"color": "#0f172a"}},
                "tooltip": { # 커서를 가져다 대면 나오는 세부 수치 팝업 최적화
                    "enabled": True,
                    "backgroundColor": "#0f172a",
                    "titleColor": "#ffffff",
                    "bodyColor": "#ffffff",
                    "padding": 12,
                    "cornerRadius": 6
                }
            },
            "scales": {
                "y": {
                    "beginAtZero": True,
                    "grid": {"color": "rgba(226, 232, 240, 0.6)"},
                    "ticks": {"color": "#475569"}
                },
                "x": {
                    "grid": {"display": False},
                    "ticks": {"color": "#475569", "font": {"size": 11}}
                }
            }
        }
    }
    
    # 캔버스 높이 지정하여 가시성 확보
    st_chartjs(chart_config, height=380)
else:
    st.warning("선택하신 필터 조건에 부합하는 정비 데이터가 없습니다.")

st.markdown("---")

# 6. 실시간 정비 이력 데이터 테이블
st.subheader("📋 실시간 정비 데이터 테이블")
st.dataframe(filtered_df, use_container_width=True)

# 7. 관리자 전용 제어 센터 (추가 / 수정 / 삭제)
if is_admin:
    st.markdown("---")
    st.subheader("🛠️ 데이터 관리 커맨드 센터 (관리자 인증 완료)")
    
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
                    "부동시간[Hr]": add_부동, "소요비용[천원]": add_비용, "정비자": add_정비자, "비고": add_비고
                }])
                updated_df = pd.concat([df, new_row], ignore_index=True)
                conn.update(spreadsheet=spreadsheet_url, data=updated_df)
                st.success("구글 스프레드시트에 실시간 저장이 완료되었습니다!")
                st.rerun()
                
    # [수정]
    with tab2:
        if not df.empty:
            edit_index = st.selectbox("수정할 기록 선택", df.index, format_func=lambda x: f"[{x}] {df.iloc[x]['설비명']} ({df.iloc[x]['정비일자']})")
            row_to_edit = df.iloc[edit_index]
            
            with st.form("edit_form"):
                st.info(f"선택한 번호 [{edit_index}]의 기존 내용이 로드되었습니다.")
                
                ec1, ec2, ec3, ec4 = st.columns(4)
                process_options = ["파쇄", "선광", "채광", "제련"]
                p_idx = process_options.index(row_to_edit["공정"]) if row_to_edit["공정"] in process_options else 0
                edit_공정 = ec1.selectbox("공정", process_options, index=p_idx)
                edit_세부 = ec2.text_input("세부공정", value=str(row_to_edit["세부공정"]) if pd.notna(row_to_edit["세부공정"]) else "")
                
                try: default_date = pd.to_datetime(row_to_edit["정비일자"]).date()
                except: default_date = pd.Timestamp.now().date()
                edit_일자 = ec3.date_input("정비일자", value=default_date)
                
                type_options = ["대", "중", "소"]
                t_idx = type_options.index(row_to_edit["설비분류"]) if row_to_edit["설비분류"] in type_options else 0
                edit_분류 = ec4.selectbox("설비분류", type_options, index=t_idx)
                
                ec5, ec6, ec7, ec8 = st.columns(4)
                edit_설비명 = ec5.text_input("설비명", value=str(row_to_edit["설비명"]))
                edit_마력 = ec6.number_input("마력(HP)", min_value=0, value=int(row_to_edit["마력"]) if pd.notna(row_to_edit["마력"]) else 0)
                edit_기동 = ec7.text_input("기동방식", value=str(row_to_edit["기동방식"]) if pd.notna(row_to_edit["기동방식"]) else "")
                edit_고장 = ec8.text_input("고장현상", value=str(row_to_edit["고장현상"]) if pd.notna(row_to_edit["고장현상"]) else "")
                
                ec9, ec10, ec11, ec12 = st.columns(4)
                edit_조치 = ec9.text_area("조치내역", value=str(row_to_edit["조치내역"]) if pd.notna(row_to_edit["조치내역"]) else "")
                edit_부동 = ec10.number_input("부동시간[Hr]", min_value=0.0, step=0.1, value=float(row_to_edit["부동시간[Hr]"]))
                edit_비용 = ec11.number_input("소요비용[천원]", min_value=0, value=int(row_to_edit["소요비용[천원]"]))
                edit_정비자 = ec12.text_input("정비자", value=str(row_to_edit["정비자"]) if pd.notna(row_to_edit["정비자"]) else "")
                edit_비고 = st.text_input("비고", value=str(row_to_edit["비고"]) if pd.notna(row_to_edit["비고"]) else "")
                
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
                    st.success("기록 데이터 수정이 성공적으로 반영되었습니다!")
                    st.rerun()

    # [삭제]
    with tab3:
        if not df.empty:
            delete_index = st.selectbox("삭제할 이력 선택", df.index, format_func=lambda x: f"[{x}] {df.iloc[x]['설비명']} ({df.iloc[x]['정비일자']})")
            if st.button("🗑️ 선택한 정비 이력 영구 삭제"):
                updated_df = df.drop(delete_index).reset_index(drop=True)
                conn.update(spreadsheet=spreadsheet_url, data=updated_df)
                st.success("구글 클라우드에서 데이터가 완벽하게 제거되었습니다.")
                st.rerun()
