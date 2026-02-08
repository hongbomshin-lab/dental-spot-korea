import pandas as pd
import os

def try_read_csv(filepath):
    for enc in ['cp949', 'euc-kr', 'utf-8-sig']:
        try:
            df = pd.read_csv(filepath, encoding=enc, nrows=5)
            print(f"Successfully read {filepath} with {enc}")
            print(df.columns.tolist())
            return df
        except Exception as e:
            print(f"Failed {filepath} with {enc}: {e}")
    return None

try_read_csv('c:/Coding Project/nice_location/data_raw/치과병원.csv')
