import pandas as pd
import os

def add_economic_data():
    # 1. 경로 설정
    raw_dir = 'data_raw'
    processed_dir = 'data_processed'
    ranking_path = os.path.join(processed_dir, 'final_ranking_v2.csv')
    seoul_housing = os.path.join(raw_dir, 'seoul_housing.csv')
    gyeonggi_housing = os.path.join(raw_dir, 'gyeonggi_housing.csv')
    output_path = os.path.join(processed_dir, 'final_ranking_v3_economic.csv')

    if not os.path.exists(ranking_path):
        print("기존 분석 결과(v2)가 없습니다.")
        return

    # 2. 아파트 실거래가 데이터 로드 및 병합
    print("하우징 데이터 로드 중...")
    def load_housing(path):
        # 국토교통부 데이터 보충: 보통 15줄 정도가 안내 문구임
        df = pd.read_csv(path, encoding='cp949', skiprows=15)
        return df

    df_seoul = load_housing(seoul_housing)
    df_gyeonggi = load_housing(gyeonggi_housing)
    df_housing = pd.concat([df_seoul, df_gyeonggi], ignore_index=True)

    # 3. 데이터 전처리
    print("하우징 데이터 전처리 중...")
    # 거래금액(만원) 숫자 변환
    df_housing['거래금액(만원)'] = df_housing['거래금액(만원)'].astype(str).str.replace(',', '').astype(int)
    
    # 평당가격 계산 (전용면적당 가격 * 3.3)
    df_housing['평당가격'] = df_housing['거래금액(만원)'] / (df_housing['전용면적(㎡)'] / 3.3)

    # 주소 파싱 (시군구 컬럼: "서울특별시 강남구 개포동")
    # ranking 데이터의 '시도', '시군구', '읍면동'과 맞춰야 함
    def parse_addr(full_addr):
        parts = full_addr.split()
        sido = parts[0] if len(parts) > 0 else ''
        # 시군구가 두 단어인 경우 고려 (예: 수원시 팔달구)
        if len(parts) == 3:
            sigungu = parts[1]
            dong = parts[2]
        elif len(parts) >= 4:
            sigungu = ' '.join(parts[1:-1])
            dong = parts[-1]
        else:
            sigungu = ''
            dong = ''
        return pd.Series([sido, sigungu, dong])

    df_housing[['시도', '시군구_parsed', '읍면동_parsed']] = df_housing['시군구'].apply(parse_addr)

    # 4. 동별 경제력 지표 산출
    print("경제력 지표 산출 중...")
    # 법정동 기준 평균가 계산
    legal_dong_avg = df_housing.groupby(['시도', '시군구_parsed', '읍면동_parsed'])['평당가격'].mean().reset_index()
    legal_dong_avg.columns = ['시도', '시군구', '읍면동_legal', '경제력_지수']

    # 5. 기존 분석 결과와 병합 및 매칭 고도화
    print("최종 데이터 병합 및 행정동-법정동 매칭 개선...")
    df_ranking = pd.read_csv(ranking_path).fillna('')

    # [매칭 로직 개선] 행정동(신정3동) -> 법정동(신정동) 변환 함수
    import re
    def get_base_dong(dong):
        # 1. 숫자 및 '제', '.' 제거 (예: 신정3동 -> 신정동, 창제1동 -> 창동)
        # 2. '동/면/읍'으로 끝나는 부분까지만 추출
        base = re.sub(r'[0-9제\.]', '', dong)
        return base

    # 랭킹 데이터의 읍면동을 법정동 기준으로 변환한 임시 컬럼 생성
    df_ranking['읍면동_base'] = df_ranking['읍면동'].apply(get_base_dong)

    # 법정동 평균 데이터와 병합 (시도, 시군구, 법정동명으로 매칭)
    df_final = pd.merge(
        df_ranking, 
        legal_dong_avg, 
        left_on=['시도', '시군구', '읍면동_base'], 
        right_on=['시도', '시군구', '읍면동_legal'], 
        how='left'
    )

    # 데이터가 없는 곳은 0으로 처리 (사용자 요청: 외부 검색 데이터 배제)
    df_final['경제력_지수'] = df_final['경제력_지수'].fillna(0)
    
    # 임시 컬럼 정리
    df_final = df_final.drop(columns=['읍면동_base', '읍면동_legal'])

    # 6. 최종 스코어링 업데이트 (Streamlit 앱과 동일 로직 적용)
    print("스코어링 로직 고도화 적용 중...")
    
    def normalize_score(col_series):
        min_val = col_series.min()
        max_val = col_series.max()
        # 1~10점 스케일로 변환
        return 1 + (col_series - min_val) / (max_val - min_val) * 9

    # 각 지표 정규화 (1~10점)
    df_final['노인인구_점수'] = normalize_score(df_final['노인인구수'])
    df_final['공급부족_점수'] = normalize_score(df_final['구별_지표']) # 구별_지표는 '구별_치과수' 대비 인구 등을 의미한다고 가정
    df_final['경제력_점수'] = normalize_score(df_final['경제력_지수'])

    # 가중치 설정 (기본값: 노인 1.0, 경제력 1.0)
    # Score = (Pop^1.0) * (Comp^1.0) * (Econ^1.0)
    df_final['Total_Score'] = (df_final['노인인구_점수'] ** 1.0) * (df_final['공급부족_점수'] ** 1.0) * (df_final['경제력_점수'] ** 1.0)

    # 7. 결과 저장 및 출력
    df_final = df_final.sort_values(by='Total_Score', ascending=False)
    df_final.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    print("\n--- [경제력 반영 최종 유망 입지 TOP 20 (v3)] ---")
    cols = ['시도', '시군구', '읍면동', '노인인구수', '구별_치과수', '경제력_지수', 'Total_Score']
    print(df_final[cols].head(20))
    print(f"\n최종 결과 저장 완료: {output_path}")

if __name__ == "__main__":
    add_economic_data()
