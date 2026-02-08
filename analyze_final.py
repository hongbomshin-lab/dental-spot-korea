import pandas as pd
import os

def final_analysis():
    # 1. 파일 로드
    dental_path = 'data_processed/dental_preprocessed.csv'
    pop_path = 'data_processed/population_preprocessed.csv'
    output_path = 'data_processed/final_analysis_result.csv'
    
    if not os.path.exists(dental_path) or not os.path.exists(pop_path):
        print("필요한 전처리 파일이 없습니다.")
        return

    df_dental = pd.read_csv(dental_path)
    df_pop = pd.read_csv(pop_path)

    # 2. 치과 데이터 그룹화 (동별 치과 개수 카운트)
    # NaN 값은 빈 문자열로 대체하여 매칭 확률 높임
    df_dental['시군구'] = df_dental['시군구'].fillna('')
    df_dental['읍면동'] = df_dental['읍면동'].fillna('')
    
    dental_counts = df_dental.groupby(['시도', '시군구', '읍면동']).size().reset_index(name='치과수')

    # 3. 인구 데이터와 병합 (Left Join)
    df_pop['시군구'] = df_pop['시군구'].fillna('')
    df_pop['읍면동'] = df_pop['읍면동'].fillna('')
    
    # 병합
    df_merged = pd.merge(df_pop, dental_counts, on=['시도', '시군구', '읍면동'], how='left')
    
    # 치과가 없는 지역은 0으로 채움
    df_merged['치과수'] = df_merged['치과수'].fillna(0).astype(int)

    # 4. 매칭 확인
    # 읍면동이 비어있지 않은 하위 행정구역 중에서 치과수가 0인 비율 확인
    dong_rows = df_merged[df_merged['읍면동'] != '']
    unmatched_count = dong_rows[dong_rows['치과수'] == 0].shape[0]
    total_dong_count = dong_rows.shape[0]
    
    print(f"--- 매칭 통계 ---")
    print(f"전체 '동' 개수: {total_dong_count}")
    print(f"치과가 0개로 찍힌 '동' 개수 (미매칭 포함): {unmatched_count} ({unmatched_count/total_dong_count*100:.2f}%)")
    print("TIP: 주소 체계(법정동 vs 행정동) 차이로 인해 실제 치과가 있어도 매칭되지 않았을 수 있습니다.\n")

    # 5. 지표 계산
    # '치과 1개당 노인 인구수' = (노인인구수) / (치과 수 + 1)
    df_merged['치과1개당_노인인구수'] = df_merged['노인인구수'] / (df_merged['치과수'] + 1)

    # 6. 정렬 및 상위 20개 출력
    # 동 단위 데이터만 출력하기 위해 읍면동이 있는 행만 필터링
    final_dong_level = df_merged[df_merged['읍면동'] != ''].copy()
    top_20 = final_dong_level.sort_values(by='치과1개당_노인인구수', ascending=False).head(20)

    print("--- 치과 1개당 노인 인구수가 많은 상위 20개 지역 ---")
    print(top_20[['시도', '시군구', '읍면동', '노인인구수', '치과수', '치과1개당_노인인구수']])

    # 7. 최종 결과 저장
    df_merged.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"\n최종 분석 결과 저장됨: {output_path}")

if __name__ == "__main__":
    final_analysis()
