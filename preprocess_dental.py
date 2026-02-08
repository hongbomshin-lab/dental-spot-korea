import pandas as pd
import os

def preprocess_dental_data():
    # 1. 파일 경로 설정
    raw_dir = 'data_raw'
    processed_dir = 'data_processed'
    
    file1 = os.path.join(raw_dir, '치과병원.csv')
    file2 = os.path.join(raw_dir, '치과의원.csv')
    
    # 2. 파일 로드 함수 (인코딩 시도)
    def load_csv(path):
        if not os.path.exists(path):
            print(f"파일을 찾을 수 없습니다: {path}")
            return None
        
        # 사용자가 언급한 cp949, euc-kr을 먼저 시도
        for enc in ['cp949', 'euc-kr', 'utf-8-sig', 'utf-8']:
            try:
                df = pd.read_csv(path, encoding=enc)
                print(f"성공적으로 로드함 ({enc}): {path}")
                return df
            except Exception:
                continue
        print(f"파일 로드 실패: {path}")
        return None

    print("데이터 로딩 중...")
    df_hosp = load_csv(file1)
    df_clinic = load_csv(file2)

    # 3. 데이터 합치기
    if df_hosp is None and df_clinic is None:
        print("데이터를 로드할 수 없습니다.")
        return

    df_dental = pd.concat([df_hosp, df_clinic], ignore_index=True)
    print(f"전체 데이터 개수: {len(df_dental)}")

    # 4. '영업상태명' 필터링 (영업/정상인 행만 유지)
    # 데이터에 따라 '영업상태명'이 없거나 '상세영업상태명'만 있을 수 있음
    status_col = None
    if '영업상태명' in df_dental.columns:
        status_col = '영업상태명'
        target_status = '영업/정상'
    elif '상세영업상태명' in df_dental.columns:
        status_col = '상세영업상태명'
        target_status = '영업중'
        
    if status_col:
        df_dental = df_dental[df_dental[status_col] == target_status].copy()
        print(f"영업 중인 데이터 개수 ({status_col}='{target_status}'): {len(df_dental)}")
    else:
        print("영업 상태 관련 컬럼을 찾을 수 없어 필터링을 건너뜁니다.")

    # 5. 주소 정보 추출 (시도, 시군구, 읍면동)
    # '소재지전체주소'가 지번 주소이므로 우선 사용, 없으면 '도로명전체주소' 사용
    # NaN 처리를 위해 두 컬럼을 합침
    df_dental['address'] = df_dental['소재지전체주소'].fillna(df_dental['도로명전체주소']).fillna('')
    
    def extract_addr(addr):
        if not addr:
            return pd.Series(['', '', ''])
        parts = addr.split()
        sido = parts[0] if len(parts) > 0 else ''
        sigungu = parts[1] if len(parts) > 1 else ''
        # 읍면동: 지번주소(소재지전체주소)의 3번째 토큰이 보통 읍면동임
        dong = parts[2] if len(parts) > 2 else ''
        return pd.Series([sido, sigungu, dong])

    df_dental[['시도', '시군구', '읍면동']] = df_dental['address'].apply(extract_addr)
    
    # 6. 필요한 컬럼만 선택 [병원명, 시도, 시군구, 읍면동]
    # '사업장명'이 보통 병원 이름임
    name_col = '사업장명'
    if name_col not in df_dental.columns:
        if '병원명' in df_dental.columns:
            name_col = '병원명'
        else:
            name_col = df_dental.columns[0]
            
    df_result = df_dental[[name_col, '시도', '시군구', '읍면동']].copy()
    df_result.columns = ['병원명', '시도', '시군구', '읍면동']

    # 7. 결과 저장
    if not os.path.exists(processed_dir):
        os.makedirs(processed_dir)
        
    output_path = os.path.join(processed_dir, 'dental_preprocessed.csv')
    df_result.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"전처리 완료. 파일 저장됨: {output_path}")

    # 8. 시도별 치과 개수 출력
    print("\n--- 시도별 치과 개수 확인 ---")
    counts = df_result['시도'].value_counts()
    print(counts.head(20)) # 너무 많을 수 있으니 상위 20개 출력

if __name__ == "__main__":
    preprocess_dental_data()

