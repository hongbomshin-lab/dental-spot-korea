import pandas as pd
import os
import re

def preprocess_population_data():
    raw_path = 'data_raw/연령별인구현황.csv'
    processed_dir = 'data_processed'
    output_path = os.path.join(processed_dir, 'population_preprocessed.csv')
    
    # 1. 파일 로드
    print(f"Loading {raw_path}...")
    try:
        # 천단위 구분자(,) 처리 및 인코딩 설정
        df = pd.read_csv(raw_path, encoding='cp949', thousands=',')
    except Exception as e:
        print(f"Error loading file: {e}")
        return

    # 2. 행정구역 전처리
    print("Processing '행정구역' column...")
    
    # 괄호와 코드 제거
    df['clean_addr'] = df['행정구역'].str.split('(').str[0].str.strip()
    
    # 시도, 시군구, 읍면동 분리 로직
    # 주소 형식이 "시도 시군구 읍면동" 형태임
    def split_address(addr):
        parts = addr.split()
        sido = parts[0] if len(parts) > 0 else ''
        
        if len(parts) == 1:
            return pd.Series([sido, '', ''])
        elif len(parts) == 2:
            return pd.Series([sido, parts[1], ''])
        elif len(parts) >= 3:
            # 시군구가 두 단어일 수도 있음 (예: 수원시 팔달구)
            # 하지만 보통 마지막이 읍면동이므로 뒤에서부터 채우는 것이 안전할 수 있음
            # 여기서는 사용자 요청에 따라 앞부분 시군구, 마지막 읍면동으로 처리
            sigungu = ' '.join(parts[1:-1])
            dong = parts[-1]
            return pd.Series([sido, sigungu, dong])
        return pd.Series(['', '', ''])

    df[['시도', '시군구', '읍면동']] = df['clean_addr'].apply(split_address)

    # 3. 인구수 계산 (노인인구수: 65세 이상 합계)
    print("Calculating population counts...")
    
    # 총인구수 컬럼 찾기 (날짜가 바뀔 수 있으므로 '총인구수' 키워드로 검색)
    total_pop_col = [col for col in df.columns if '총인구수' in col][0]
    
    # 연령별 컬럼 추출 (65세 ~ 100세 이상)
    # 컬럼명 예: '2026년01월_계_65세'
    senior_cols = []
    for col in df.columns:
        # '65세'부터 '99세'까지 찾기
        match = re.search(r'_(\d+)세$', col)
        if match:
            age = int(match.group(1))
            if age >= 65:
                senior_cols.append(col)
        # '100세 이상' 컬럼 포함
        if '100세 이상' in col:
            senior_cols.append(col)
            
    # 노인인구수 합산 (숫자 데이터로 자동 변환됐는지 확인 필요, thousands=',' 옵션 사용함)
    df['노인인구수'] = df[senior_cols].sum(axis=1)
    df['총인구수'] = df[total_pop_col]

    # 4. 필요한 컬럼만 선택 [시도, 시군구, 읍면동, 총인구수, 노인인구수]
    # '읍면동'이 비어있는 행(시도 전체, 시군구 전체)은 제외할지 고민... 
    # 요구사항에 명시되지 않았으므로 일단 모든 행 유지
    df_result = df[['시도', '시군구', '읍면동', '총인구수', '노인인구수']].copy()

    # 5. 결과 저장 및 출력
    if not os.path.exists(processed_dir):
        os.makedirs(processed_dir)
        
    df_result.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"Preprocessing complete. Saved to: {output_path}")

    print("\n--- 상위 5개 데이터 확인 ---")
    print(df_result.head(5))

if __name__ == "__main__":
    preprocess_population_data()
