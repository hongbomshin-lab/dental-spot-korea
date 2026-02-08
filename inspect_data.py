import pandas as pd
import os

def inspect_csv(filename):
    path = os.path.join('data_raw', filename)
    print(f"--- Inspecting {filename} ---")
    try:
        # Try cp949 first as per user requirement hint
        df = pd.read_csv(path, encoding='cp949', nrows=5)
        print("Loaded with cp949")
    except:
        df = pd.read_csv(path, encoding='utf-8-sig', nrows=5)
        print("Loaded with utf-8-sig")
    
    print("Columns:", df.columns.tolist())
    print("First row data:")
    print(df.iloc[0].to_dict())
    print("\n")

inspect_csv('치과병원.csv')
inspect_csv('치과의원.csv')
