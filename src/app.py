# 실행 방법: 터미널에서 `streamlit run src/app.py` 입력
import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 페이지 설정
st.set_page_config(page_title="치과 개원 유망 지역 분석 대시보드 V3", layout="wide")

# 데이터 로드 함수
@st.cache_data
def load_data():
    path = 'data_processed/final_ranking_v3_economic.csv'
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path)
    # 데이터 정제: 읍면동이 없는 구 합계 행 등은 제외하고 동 단위만 보기
    df = df[df['읍면동'].notna() & (df['읍면동'] != '')]
    return df

df_raw = load_data()

if df_raw is None:
    st.error("분석 결과 파일(final_ranking_v3_economic.csv)을 찾을 수 없습니다. 고도화 코드를 먼저 실행해주세요.")
else:
    # 1. 사이드바 구성
    st.sidebar.title("🔍 분석 옵션 (V3)")
    
    # 지역 선택
    target_sido = st.sidebar.radio(
        "분석 대상 시도 선택",
        options=["서울특별시", "경기도"],
        index=0
    )
    
    # 노인 인구 가중치
    pop_weight = st.sidebar.slider(
        "👴 노인 인구 가중치",
        min_value=0.5,
        max_value=2.0,
        value=1.0,
        step=0.1
    )

    # 경제력 가중치
    econ_weight = st.sidebar.slider(
        "💰 경제력 가중치",
        min_value=0.0,
        max_value=2.0,
        value=1.0,
        step=0.1,
        help="아파트 평당 가격이 높은 지역의 가점을 조절합니다."
    )

    # 전체 경제력 평균 산출 (기준값)
    # avg_econ = df_raw[df_raw['경제력_지수'] > 0]['경제력_지수'].mean() # 구 로직 사용 안함

    # 데이터 필터링
    df = df_raw[df_raw['시도'] == target_sido].copy()
    
    # --- 스코어링 로직 고도화 ---
    # 문제점 해결: 단순 곱셈 가중치는 순위에 영향을 주지 않음 (A*W > B*W == A > B)
    # 해결책: Min-Max 정규화(0~10점) 후 지수(Exponent)가중치 방식 적용 (기하평균 응용)
    
    def normalize_score(col_series):
        min_val = col_series.min()
        max_val = col_series.max()
        # 1~10점 스케일로 변환 (0점 방지 위해 1부터 시작)
        return 1 + (col_series - min_val) / (max_val - min_val) * 9

    # 각 지표 정규화 (1~10점)
    norm_pop = normalize_score(df['노인인구수'])
    norm_comp = normalize_score(df['구별_지표'])
    norm_econ = normalize_score(df['경제력_지수'])

    # 최종 유망 지수 계산 (Cobb-Douglas 효용함수 형태)
    # Score = (Pop^w1) * (Comp^1) * (Econ^w2)
    # 가중치가 클수록 해당 지표가 높은 지역이 더 큰 점수 폭으로 상승함
    df['실시간_유망_지수'] = (norm_pop ** pop_weight) * (norm_comp ** 1.0) * (norm_econ ** econ_weight)
    
    df = df.sort_values(by='실시간_유망_지수', ascending=False)

    # 2. 메인 화면 타이틀
    st.title(f"🏥 {target_sido} 치과 개원 유망 지역 TOP 3")
    
    # 유망지수 산출 방식 설명
    with st.expander("💡 가중치가 어떻게 순위를 바꾸나요?"):
        st.markdown(r"""
        단순한 곱셈 방식이 아닌, **지수(Power) 가중치 방식**을 도입하여 사용자가 중요하게 생각하는 요소가 순위에 결정적인 영향을 미치도록 개선했습니다.
        
        ### 📐 고도화된 산출 공식
        모든 데이터를 **1~10점**으로 변환한 뒤 다음 공식을 적용합니다:
        $$
        \text{Score} = (\text{인구 점수}^{\text{가중치}}) \times (\text{공급부족 점수}) \times (\text{경제력 점수}^{\text{가중치}})
        $$

        ### 🔍 가중치 조절 효과
        - **노인 인구 가중치 증가 ( > 1.0 )**: 노인 인구가 압도적으로 많은 지역의 점수가 기하급수적으로 높아져 상위권으로 올라갑니다.
        - **경제력 가중치 증가 ( > 1.0 )**: 평당 가격이 비싼 부촌 지역의 영향력이 커집니다.
        - **가중치 감소 ( < 1.0 )**: 해당 요소의 차이가 전체 순위에 미치는 영향이 줄어들어 평준화됩니다.
        """)

    st.markdown("---")

    # 3. KPI 지표 (Top 3 동)
    top_3 = df.head(3)
    cols = st.columns(3)

    for i, (idx, row) in enumerate(top_3.iterrows()):
        with cols[i]:
            st.metric(label=f"TOP {i+1} 유망 지역", value=row['읍면동'])
            st.caption(f"📍 {row['시군구']}")
            col1, col2 = st.columns(2)
            col1.write(f"👴 노인: {int(row['노인인구수']):,}명")
            # 만원 단위를 천만원 단위로 변환
            col2.write(f"💰 평단가: {row['경제력_지수']/1000:.1f}천만")
    
    st.markdown("---")

    # 4. 분석 시각화 Section
    col_table, col_chart = st.columns([1.2, 0.8])

    with col_table:
        st.subheader("📊 상세 데이터 순위")
        display_df = df[['시군구', '읍면동', '노인인구수', '구별_지표', '경제력_지수', '실시간_유망_지수']].copy()
        display_df['경제력_지수'] = display_df['경제력_지수'] / 1000 # 천만원 단위
        
        # 보기 좋게 컬럼 정규화 점수도 보여줄까요? 아니면 원본? 사용자는 원본을 선호함.
        display_df.columns = ['시군구', '읍면동', '노인인구(명)', '구공급부족도', '평단가(천만)', '유망지수']

        st.dataframe(
            display_df,
            column_config={
                "유망지수": st.column_config.NumberColumn(
                    "🎨 유망지수", 
                    format="%.0f",
                    help="노인 인구, 치과 공급, 경제력을 종합적으로 계산한 최종 입지 점수입니다."
                ),
                "구공급부족도": st.column_config.NumberColumn(
                    "구공급부족도",
                    help="해당 구 전체의 치과 1개당 노인 인구수입니다. 값이 클수록 경쟁이 낮고 수요가 많음을 의미합니다."
                ),
                "노인인구(명)": st.column_config.NumberColumn("👴 노인", format="%d"),
                "평단가(천만)": st.column_config.ProgressColumn(
                    "💰 평단가", 
                    min_value=0, 
                    max_value=int(display_df['평단가(천만)'].max()), 
                    format="%.1f"
                ),
            },
            hide_index=True,
            use_container_width=True
        )

    with col_chart:
        st.subheader("📈 경제력 vs 공급부족도 분포")
        # 산점도: X부유함, Y공급부족
        fig = px.scatter(
            df,
            x='경제력_지수',
            y='구별_지표',
            size='노인인구수',
            color='실시간_유망_지수',
            hover_name='읍면동',
            hover_data=['시군구', '노인인구수'],
            labels={
                '경제력_지수': '평당 아파트 가격 (만원)',
                '구별_지표': '치과 1개당 노인 인구 (부족도)',
                '실시간_유망_지수': '최종 점수'
            },
            template='plotly_white',
            color_continuous_scale='Viridis'
        )
        # 우상향 영역 강조 설명
        st.plotly_chart(fig, use_container_width=True)
        st.info("💡 **그래프 우측 상단**에 위치할수록 경제력이 높고 경쟁은 낮아 개원하기에 매우 유리한 입지입니다.")

    # 5. 구별 경쟁 강도 (추가 지표)
    st.markdown("---")
    st.subheader(f"📍 {target_sido} 구별 경쟁 강도")
    gu_intensity = df.groupby('시군구')['구별_지표'].first().sort_values(ascending=False)
    st.bar_chart(gu_intensity, horizontal=True)
