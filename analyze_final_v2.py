import pandas as pd
import os

def analyze_final_v2():
    # 1. 파일 로드
    pop_path = 'data_processed/population_preprocessed.csv'
    gu_score_path = 'data_processed/gu_competition_score.csv'
    output_path = 'data_processed/final_ranking_v2.csv'
    
    if not os.path.exists(pop_path) or not os.path.exists(gu_score_path):
        print("필요한 데이터 파일이 없습니다. 이전 단계를 먼저 수행해주세요.")
        return

    df_pop = pd.read_csv(pop_path).fillna('')
    df_gu_score = pd.read_csv(gu_score_path).fillna('')

    # 2. '시군구' 기준으로 Left Join
    # 시도와 시군구를 함께 매칭하여 지역 오차 방지
    df_merged = pd.merge(df_pop, df_gu_score, on=['시도', '시군구'], how='left')

    # 3. '최종_유망_지수' 계산
    # 공식: 노인인구수(동 단위) * 구별_지표(구 단위)
    # NaN 값(매칭되지 않은 구)은 0으로 처리
    df_merged['구별_지표'] = df_merged['구별_지표'].fillna(0)
    df_merged['최종_유망_지수'] = df_merged['노인인구수'] * df_merged['구별_지표']

    # 4. 필터링 및 정렬
    # 읍면동이 있는 행만 선택 (하위 행정구역 데이터)
    final_ranking = df_merged[df_merged['읍면동'] != ''].copy()
    
    # 지수 기준 내림차순 정렬
    top_20 = final_ranking.sort_values(by='최종_유망_지수', ascending=False).head(20)

    # 5. 결과 출력
    cols_to_show = ['시도', '시군구', '읍면동', '노인인구수', '구별_치과수', '최종_유망_지수']
    print("--- [최종 유망 입지 랭킹 V2 (Top 20)] ---")
    print(top_20[cols_to_show])

    # 6. 결과 저장
    final_ranking.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"\n분석 결과가 {output_path}에 저장되었습니다.")

if __name__ == "__main__":
    analyze_final_v2()
