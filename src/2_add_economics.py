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
    economic_idx = df_housing.groupby(['시도', '시군구_parsed', '읍면동_parsed'])['평당가격'].mean().reset_index()
    economic_idx.columns = ['시도', '시군구', '읍면동', '경제력_지수']

    # 5. 기존 분석 결과와 병합
    print("최종 데이터 병합 및 스코어링...")
    df_ranking = pd.read_csv(ranking_path).fillna('')
    
    # Left Join
    df_final = pd.merge(df_ranking, economic_idx, on=['시도', '시군구', '읍면동'], how='left')

    # 아파트 거래가 없는 곳 처리 (매칭되지 않은 곳)
    # 1차: 해당 시군구의 평균값으로 채움
    gu_avg = df_final.groupby(['시도', '시군구'])['경제력_지수'].transform('mean')
    df_final['경제력_지수'] = df_final['경제력_지수'].fillna(gu_avg)
    
    # 2차: 그래도 남은 곳은 0으로 (드문 경우)
    df_final['경제력_지수'] = df_final['경제력_지수'].fillna(0)

    # 6. 최종 스코어링 업데이트
    avg_econ = df_final[df_final['경제력_지수'] > 0]['경제력_지수'].mean()
    # Total_Score = (노인인구수 * 구별_지표) * (경제력_지수 / 전체평균_경제력)
    # v2의 최종_유망_지수가 이미 (노인인구수 * 구별_지표) 이므로 이를 활용
    df_final['Total_Score'] = df_final['최종_유망_지수'] * (df_final['경제력_지수'] / avg_econ)

    # 7. 결과 저장 및 출력
    df_final = df_final.sort_values(by='Total_Score', ascending=False)
    df_final.to_csv(output_path, index=False, encoding='utf-8-sig')
    
    print("\n--- [경제력 반영 최종 유망 입지 TOP 20 (v3)] ---")
    cols = ['시도', '시군구', '읍면동', '노인인구수', '구별_치과수', '경제력_지수', 'Total_Score']
    print(df_final[cols].head(20))
    print(f"\n최종 결과 저장 완료: {output_path}")

if __name__ == "__main__":
    add_economic_data()
