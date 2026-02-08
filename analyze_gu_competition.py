import pandas as pd
import os

def analyze_gu_competition():
    # 사용자가 언급한 파일명으로 로드 (실제 생성된 경로인 data_processed 사용)
    # 작업 흐름상 dental_preprocessed.csv와 population_preprocessed.csv를 활용합니다.
    dental_path = 'data_processed/dental_preprocessed.csv'
    pop_path = 'data_processed/population_preprocessed.csv'
    
    if not os.path.exists(dental_path) or not os.path.exists(pop_path):
        print("전처리된 데이터 파일이 존재하지 않습니다. 이전 단계를 먼저 수행해주세요.")
        return None

    # 1. 치과 데이터 로드 및 시군구별 그룹화
    df_dental = pd.read_csv(dental_path).fillna('')
    # 시도와 시군구를 함께 그룹화하여 다른 지역의 같은 '구' 이름 충돌 방지
    df_gu_dental = df_dental[df_dental['시군구'] != ''].groupby(['시도', '시군구']).size().reset_index(name='구별_치과수')

    # 2. 인구 데이터 로드 및 시군구별 그룹화
    df_pop = pd.read_csv(pop_path).fillna('')
    # 읍면동이 비어있는 행이 해당 시군구의 합계 데이터임
    df_gu_pop = df_pop[(df_pop['시군구'] != '') & (df_pop['읍면동'] == '')].copy()
    df_gu_pop = df_gu_pop.groupby(['시도', '시군구'])['노인인구수'].sum().reset_index(name='구별_노인인구수')

    # 3. 데이터 병합
    df_gu_score = pd.merge(df_gu_pop, df_gu_dental, on=['시도', '시군구'], how='inner')

    # 4. '구별_지표' 계산 (노인인구수 / 치과수)
    # 이 값이 클수록 치과 1개당 감당해야 하는 노인 인구가 많아 경쟁이 낮고 수요가 높다고 판단 가능
    df_gu_score['구별_지표'] = df_gu_score['구별_노인인구수'] / df_gu_score['구별_치과수']

    # 5. 결과 출력 (지표 높은 순 정렬)
    df_gu_score = df_gu_score.sort_values(by='구별_지표', ascending=False).reset_index(drop=True)
    
    print("--- [시군구 단위 치과 경쟁 강도 (df_gu_score)] ---")
    print(df_gu_score.head(20))
    
    # 파일로도 저장
    output_path = 'data_processed/gu_competition_score.csv'
    df_gu_score.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"\n결과가 {output_path}에 저장되었습니다.")
    
    return df_gu_score

if __name__ == "__main__":
    df_gu_score = analyze_gu_competition()
