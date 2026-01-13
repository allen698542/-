import pandas as pd
import requests
import time
import os

# ================= 設定區 =================
# 請將這裡換成您的 NEXON API KEY
API_KEY = "test_610de0b1b6fc24f5d76920c0cc30d8f1901f340686cafe9296eed000958263abefe8d04e6d233bd35cf2fabdeb93fb0d"

# 檔案名稱設定
INPUT_FILE = "data.xlsx"       # 您手動輸入的 Excel 檔名
OUTPUT_FILE = "guild_data.csv" # 程式會自動產生的檔名 (給網站用)
# =========================================

def get_character_info(name):
    """輸入暱稱，回傳 (OCID, 等級, 職業, 圖片網址)"""
    headers = {
        "x-nxopen-api-key": API_KEY,
        "accept": "application/json"
    }
    
    try:
        # 1. 查 OCID
        url_id = "https://open.api.nexon.com/maplestorytw/v1/id"
        r_id = requests.get(url_id, headers=headers, params={"character_name": name})
        
        if r_id.status_code != 200:
            return None # 查無此人
            
        ocid = r_id.json().get("ocid")
        
        # 2. 查基本資料
        # 這裡會抓「昨天」的資料，因為官方 API 有時會有延遲
        url_basic = "https://open.api.nexon.com/maplestorytw/v1/character/basic"
        r_basic = requests.get(url_basic, headers=headers, params={"ocid": ocid})
        
        if r_basic.status_code == 200:
            data = r_basic.json()
            return {
                "等級": data.get("character_level"),
                "職業": data.get("character_class"),
                "圖片": data.get("character_image")
            }
    except Exception as e:
        print(f"查詢錯誤 {name}: {e}")
    
    return None

def main():
    print("🚀 啟動更新小幫手...")
    print(f"📖 正在讀取 {INPUT_FILE}...")
    
    try:
        # 讀取原本的 Excel
        df = pd.read_excel(INPUT_FILE)
        
        # 為了省流量，我們先找出「不重複」的名單
        # 假設 Excel 有 1000 行，但只有 50 個公會成員，我們只要查這 50 人
        unique_members = df['暱稱'].unique()
        print(f"🔍 發現共 {len(unique_members)} 位成員，開始更新資料...")
        
        # 建立一個字典來存這些人的最新資料
        member_info_map = {}
        
        for i, name in enumerate(unique_members):
            print(f"[{i+1}/{len(unique_members)}] 更新: {name} ...", end="\r")
            
            info = get_character_info(name)
            if info:
                member_info_map[name] = info
            else:
                # 查不到 (可能改名或刪角)，就給空值
                member_info_map[name] = {"等級": 0, "職業": "未知", "圖片": ""}
            
            # 重要：休息 0.2 秒，避免被鎖 IP (每秒限制 5 次)
            time.sleep(0.2)
            
        print("\n✅ API 資料查詢完畢！正在合併資料...")
        
        # === 核心步驟：把查到的資料，對應回原本的 Excel ===
        # 1. 把字典轉成 DataFrame
        info_df = pd.DataFrame.from_dict(member_info_map, orient='index')
        info_df.index.name = '暱稱'
        info_df.reset_index(inplace=True)
        
        # 2. 如果原本 Excel 裡已經有 '職業' 欄位，我們先移除，以免重複
        cols_to_drop = [c for c in ['等級', '職業', '圖片'] if c in df.columns]
        df = df.drop(columns=cols_to_drop, errors='ignore')
        
        # 3. 合併 (Left Join)
        # 這會把最新的等級、圖片，填入 Excel 的每一行對應的名字後面
        final_df = pd.merge(df, info_df, on='暱稱', how='left')
        
        # 4. 存檔
        final_df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
        print(f"💾 檔案已輸出至: {OUTPUT_FILE}")
        print("🎉 網站資料庫更新完成！")

    except Exception as e:
        print(f"❌ 發生錯誤: {e}")
        input("按任意鍵退出...")

if __name__ == "__main__":
    main()
