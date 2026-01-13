import pandas as pd
import os

# ================= 設定區 =================
ORIGINAL_EXCEL = "data.xlsx"       # 您原本手動紀錄的檔案 (有正確職業)
CURRENT_CSV = "guild_data.csv"     # 剛剛跑出來的檔案 (有等級圖片，但職業可能有缺)
# =========================================

def main():
    print("🔧 開始進行職業資料修補 (不消耗 API)...")

    # 1. 讀取兩個檔案
    if not os.path.exists(CURRENT_CSV):
        print(f"❌ 找不到 {CURRENT_CSV}，請先確認您剛剛有執行過 update_tool.py")
        return

    try:
        df_csv = pd.read_csv(CURRENT_CSV) # 這是網站要用的
        df_excel = pd.read_excel(ORIGINAL_EXCEL) # 這是原本的備份
        
        print(f"📖 讀取完成：CSV ({len(df_csv)} 筆), Excel ({len(df_excel)} 筆)")
    except Exception as e:
        print(f"❌ 讀取檔案失敗: {e}")
        return

    # 2. 建立一個「暱稱 -> 舊職業」的對照表
    # 如果 Excel 裡有重複暱稱，我們抓最後一筆資料即可
    # 這裡確保 '職業' 轉成字串，並去除前後空白
    df_excel['職業'] = df_excel['職業'].fillna("").astype(str).str.strip()
    job_map = df_excel.set_index('暱稱')['職業'].to_dict()

    # 3. 開始修補 CSV 裡的職業
    updated_count = 0
    
    for index, row in df_csv.iterrows():
        name = row['暱稱']
        current_job = str(row['職業']).strip()
        
        # 判斷標準：如果 CSV 裡的職業是 "未知"、"nan"、"None" 或是空白
        # 就去 Excel 的對照表找
        if current_job in ["未知", "nan", "None", "", "nan"]:
            original_job = job_map.get(name)
            
            # 如果 Excel 裡找得到這個人，而且職業不是空的
            if original_job and original_job not in ["nan", ""]:
                df_csv.at[index, '職業'] = original_job
                updated_count += 1
                # print(f"修補成功: {name} -> {original_job}") # 想看詳細可以取消註解

    # 4. 存檔覆蓋回去
    df_csv.to_csv(CURRENT_CSV, index=False, encoding='utf-8-sig')
    
    print("-" * 30)
    print(f"✅ 修補完成！共修正了 {updated_count} 位成員的職業資料。")
    print(f"💾 檔案已更新至 {CURRENT_CSV}，現在可以上傳到 GitHub 了。")

if __name__ == "__main__":
    main()