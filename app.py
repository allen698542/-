import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import numpy as np
import requests

# ==========================================
# API 串接設定
# ==========================================
API_KEY = st.secrets.get("NEXON_API_KEY", None)

@st.cache_data(ttl=3600)
def get_maple_character_info(character_name):
    if not API_KEY:
        return None, "未設定 API Key"
    
    headers = {
        "x-nxopen-api-key": API_KEY,
        "accept": "application/json"
    }
    
    try:
        # 1. 取得 OCID
        url_id = "https://open.api.nexon.com/maplestorytw/v1/id"
        resp_id = requests.get(url_id, headers=headers, params={"character_name": character_name})
        
        if resp_id.status_code != 200:
            return None, "找不到角色或 API 額度不足"
        
        ocid = resp_id.json().get("ocid")
        
        # 2. 取得角色基本資料
        yesterday = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        url_basic = "https://open.api.nexon.com/maplestorytw/v1/character/basic"
        resp_basic = requests.get(url_basic, headers=headers, params={"ocid": ocid, "date": yesterday})
        
        if resp_basic.status_code == 200:
            return resp_basic.json(), None
        else:
            return None, "無法讀取角色資料"
            
    except Exception as e:
        return None, f"連線錯誤: {e}"

# ==========================================
# 頁面設定
# ==========================================
st.set_page_config(page_title="公會每周統計", page_icon="🍁", layout="wide")

# ==========================================
# 0. 職業階層定義
# ==========================================
JOB_HIERARCHY_DATA = [
    {"group": "冒險家", "category": "劍士", "job": "英雄"},
    {"group": "冒險家", "category": "劍士", "job": "聖騎士"},
    {"group": "冒險家", "category": "劍士", "job": "黑騎士"},
    {"group": "冒險家", "category": "法師", "job": "大魔導士(火、毒)"},
    {"group": "冒險家", "category": "法師", "job": "大魔導士(冰、雷)"},
    {"group": "冒險家", "category": "法師", "job": "主教"},
    {"group": "冒險家", "category": "弓箭手", "job": "箭神"},
    {"group": "冒險家", "category": "弓箭手", "job": "神射手"},
    {"group": "冒險家", "category": "弓箭手", "job": "開拓者"},
    {"group": "冒險家", "category": "盜賊", "job": "夜使者"},
    {"group": "冒險家", "category": "盜賊", "job": "暗影神偷"},
    {"group": "冒險家", "category": "盜賊", "job": "影武者"},
    {"group": "冒險家", "category": "海盜", "job": "拳霸"},
    {"group": "冒險家", "category": "海盜", "job": "槍神"},
    {"group": "冒險家", "category": "海盜", "job": "重砲指揮官"},
    
    {"group": "英雄團", "category": "劍士", "job": "狂狼勇士"},
    {"group": "英雄團", "category": "法師", "job": "龍魔導士"},
    {"group": "英雄團", "category": "法師", "job": "夜光"},
    {"group": "英雄團", "category": "弓箭手", "job": "精靈遊俠"},
    {"group": "英雄團", "category": "盜賊", "job": "幻影俠盜"},
    {"group": "英雄團", "category": "海盜", "job": "隱月"},
    
    {"group": "皇家騎士團", "category": "劍士", "job": "聖魂劍士"},
    {"group": "皇家騎士團", "category": "劍士", "job": "米哈逸"},
    {"group": "皇家騎士團", "category": "法師", "job": "烈焰巫師"},
    {"group": "皇家騎士團", "category": "弓箭手", "job": "破風使者"},
    {"group": "皇家騎士團", "category": "盜賊", "job": "暗夜行者"},
    {"group": "皇家騎士團", "category": "海盜", "job": "閃雷悍將"},
    
    {"group": "末日反抗軍", "category": "劍士", "job": "惡魔殺手"},
    {"group": "末日反抗軍", "category": "劍士", "job": "惡魔復仇者"},
    {"group": "末日反抗軍", "category": "劍士", "job": "爆拳槍神"},
    {"group": "末日反抗軍", "category": "法師", "job": "煉獄巫師"},
    {"group": "末日反抗軍", "category": "弓箭手", "job": "狂豹獵人"},
    {"group": "末日反抗軍", "category": "盜賊", "job": "傑諾"},
    {"group": "末日反抗軍", "category": "海盜", "job": "傑諾"},
    {"group": "末日反抗軍", "category": "海盜", "job": "機甲戰神"},
    
    {"group": "神之子", "category": "劍士", "job": "神之子"},
    
    {"group": "超新星", "category": "劍士", "job": "凱撒"},
    {"group": "超新星", "category": "弓箭手", "job": "凱殷"},
    {"group": "超新星", "category": "盜賊", "job": "卡蒂娜"},
    {"group": "超新星", "category": "海盜", "job": "天使破壞者"},
    
    {"group": "雷普族", "category": "劍士", "job": "阿戴爾"},
    {"group": "雷普族", "category": "法師", "job": "伊利恩"},
    {"group": "雷普族", "category": "盜賊", "job": "卡莉"},
    {"group": "雷普族", "category": "海盜", "job": "亞克"},
    
    {"group": "阿尼瑪", "category": "劍士", "job": "蓮"},
    {"group": "阿尼瑪", "category": "法師", "job": "菈菈"},
    {"group": "阿尼瑪", "category": "盜賊", "job": "虎影"},
    
    {"group": "朋友世界", "category": "法師", "job": "凱內西斯"},
    
    {"group": "曉之陣", "category": "劍士", "job": "劍豪"},
    {"group": "曉之陣", "category": "法師", "job": "陰陽師"},
    
    {"group": "江湖", "category": "法師", "job": "琳恩"},
    {"group": "江湖", "category": "海盜", "job": "墨玄"},

    {"group": "其他", "category": "劍士", "job": "炭治郎"},
    {"group": "其他", "category": "劍士", "job": "粉豆"},
    {"group": "其他", "category": "海盜", "job": "雪吉拉"},
    {"group": "其他", "category": "其他", "job": "null"},
]

df_hierarchy = pd.DataFrame(JOB_HIERARCHY_DATA)

# ==========================================
# 1. 密碼保護區
# ==========================================
def check_password():
    actual_password = "share1150112"
    actual_password2 = "1113"
    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    if not st.session_state.password_correct:
        password = st.text_input("請輸入密碼", type="password")
        if password == actual_password or password == actual_password2:
            st.session_state.password_correct = True
            st.rerun()
        elif password:
            st.error("密碼錯誤")
        return False
    return True

if not check_password():
    st.stop()

# ==========================================
# 2. 讀取與處理資料
# ==========================================
@st.cache_data
def load_data():
    df = pd.read_csv("guild_data.csv")
    
    df.dropna(how='all', inplace=True)
    df.dropna(subset=['職業'], inplace=True)
    df['職業'] = df['職業'].astype(str)
    df['暱稱'] = df['暱稱'].astype(str)
    
    df['周次'] = pd.to_datetime(df['周次'])
    df['旗幟戰'] = pd.to_numeric(df['旗幟戰'], errors='coerce').fillna(0)
    df['地下水道'] = pd.to_numeric(df['地下水道'], errors='coerce').fillna(0)
    df['公會城每周'] = pd.to_numeric(df['公會城每周'], errors='coerce').fillna(0)
    
    df['本周是否達成'] = df['本周是否達成'].astype(str).str.strip()
    
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"讀取資料失敗: {e}")
    st.stop()

# ==========================================
# 3. 介面與搜尋邏輯
# ==========================================
st.title("🍁 公會每周統計")

# --- 日期區間 (共用) ---
st.sidebar.header("📅 日期區間設定")
min_date = df['周次'].min()
max_date = df['周次'].max()

start_date = st.sidebar.date_input("開始日期", value=min_date, min_value=min_date, max_value=max_date)
end_date = st.sidebar.date_input("結束日期", value=max_date, min_value=min_date, max_value=max_date)

if start_date > end_date:
    st.sidebar.error("⚠️ 開始日期不能晚於結束日期")

# 篩選日期區間資料 (全域共用)
mask_period = (df['周次'] >= pd.to_datetime(start_date)) & (df['周次'] <= pd.to_datetime(end_date))
df_period = df[mask_period]

# --- 功能模式切換 ---
st.markdown("### 🔍 功能面板")

# 更新：將選項改為三個
search_mode = st.radio(
    "請選擇功能：",
    ["個人查詢 (層級篩選)", "個人查詢 (直接搜尋)", "🏆 全公會排行榜"],
    horizontal=True
)

# ==========================================
# 分支 A: 全公會排行榜 (新功能)
# ==========================================
if search_mode == "🏆 全公會排行榜":
    st.markdown("---")
    st.markdown(f"### 📊 公會排行榜 ({start_date} ~ {end_date})")
    
    # 準備聚合資料：依據「暱稱」加總分數
    # 使用 sum 計算區間總分，mean 計算區間平均
    leaderboard_df = df_period.groupby('暱稱').agg({
        '旗幟戰': 'sum',
        '地下水道': 'sum',
        '公會城每周': 'sum',
        '周次': 'nunique', # 參與週數
        '職業': 'first'    # 抓取第一筆職業紀錄
    }).reset_index()
    
    # 三個分頁：旗幟、水道、公會城
    tab_rank_flag, tab_rank_water, tab_rank_castle = st.tabs(["🚩 旗幟戰排行", "💧 地下水道排行", "🏰 公會城全勤榜"])
    
# --- 函式：繪製排行榜 (美化版) ---
    def draw_leaderboard(data, col_name, color_scale, label_name, is_attendance=False):
        # 排序
        sorted_df = data.sort_values(by=col_name, ascending=False).reset_index(drop=True)
        sorted_df['名次'] = sorted_df.index + 1
        
        # 1. 前三名頒獎台 (Top 3) - 視覺優化版
        # 使用 5 個欄位：[空白, 銀牌, 金牌, 銅牌, 空白] 來讓版面置中
        c_space_l, c2, c1, c3, c_space_r = st.columns([1, 2, 2.2, 2, 1])
        
        top3 = sorted_df.head(3)
        
        # 定義卡片樣式 (CSS)
        card_style = """
            <div style="
                background-color: #262730; 
                padding: 15px; 
                border-radius: 10px; 
                text-align: center; 
                border: 1px solid #444;
                margin-bottom: 20px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.3);
            ">
                <div style="font-size: 3rem; margin-bottom: 5px;">{icon}</div>
                <div style="font-size: 1.2rem; font-weight: bold; color: #FFF; margin-bottom: 5px;">{name}</div>
                <div style="font-size: 1rem; color: #BBB;">{score_label}</div>
                <div style="font-size: 1.5rem; font-weight: bold; color: {color};">{score}</div>
            </div>
        """

        # --- 第一名 (金牌) ---
        if len(top3) > 0:
            p1 = top3.iloc[0]
            val1 = int(p1[col_name])
            with c1:
                # 第一名不加 margin-top，保持最高
                st.markdown(card_style.format(
                    icon="🥇", 
                    name=p1['暱稱'], 
                    score_label="Score",
                    score=f"{val1:,}",
                    color="#FFD700" # 金色
                ), unsafe_allow_html=True)
                if not is_attendance:
                    st.caption("👑 冠軍霸主")

        # --- 第二名 (銀牌) ---
        if len(top3) > 1:
            p2 = top3.iloc[1]
            val2 = int(p2[col_name])
            with c2:
                # 加上 <br> 或是 style margin-top 讓它看起來矮一點 (頒獎台階梯效果)
                st.write("") 
                st.write("") 
                st.markdown(card_style.format(
                    icon="🥈", 
                    name=p2['暱稱'], 
                    score_label="Score",
                    score=f"{val2:,}",
                    color="#C0C0C0" # 銀色
                ), unsafe_allow_html=True)

        # --- 第三名 (銅牌) ---
        if len(top3) > 2:
            p3 = top3.iloc[2]
            val3 = int(p3[col_name])
            with c3:
                # 加上 <br> 或是 style margin-top 讓它看起來矮一點
                st.write("") 
                st.write("") 
                st.markdown(card_style.format(
                    icon="🥉", 
                    name=p3['暱稱'], 
                    score_label="Score",
                    score=f"{val3:,}",
                    color="#CD7F32" # 銅色
                ), unsafe_allow_html=True)

        st.markdown("---")
        
        # 2. 長條圖視覺化 (Top 15)
        top15_df = sorted_df.head(15).copy()
        
        fig = px.bar(
            top15_df, 
            x=col_name, 
            y='暱稱', 
            orientation='h',
            text=col_name,
            title=f"🏆 {label_name} Top 15 (區間總和)",
            color=col_name,
            color_continuous_scale=color_scale
        )
        fig.update_layout(yaxis={'categoryorder':'total ascending'}) 
        fig.update_traces(texttemplate='%{text:,}', textposition='outside')
        st.plotly_chart(fig, use_container_width=True)
        
        # 3. 完整資料表
        st.markdown("#### 📋 完整名單")
        
        display_df = sorted_df[['名次', '暱稱', '職業', '周次', col_name]].copy()
        
        if is_attendance:
            display_df['全勤率(%)'] = (display_df[col_name] / display_df['周次'] * 100).astype(int)
            val_format = "%d 次"
        else:
            val_format = "%d"

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                col_name: st.column_config.ProgressColumn(
                    label_name,
                    format=val_format,
                    min_value=0,
                    max_value=int(sorted_df[col_name].max()) if len(sorted_df) > 0 else 100,
                ),
                "名次": st.column_config.NumberColumn(format="No. %d")
            }
        )

    # 內容渲染
    with tab_rank_flag:
        draw_leaderboard(leaderboard_df, '旗幟戰', 'Reds', '旗幟戰分數')
        
    with tab_rank_water:
        draw_leaderboard(leaderboard_df, '地下水道', 'Blues', '地下水道分數')
        
    with tab_rank_castle:
        draw_leaderboard(leaderboard_df, '公會城每周', 'Greens', '公會城參與數', is_attendance=True)

# ==========================================
# 分支 B: 個人查詢模式 (原本的功能)
# ==========================================
else: 
    final_selected_player = None 

    with st.container(border=True):
        
        # === 模式 1: 層級篩選 ===
        if search_mode == "個人查詢 (層級篩選)":
            st.caption("依序選擇：職業群 > 分類 > 職業 > 玩家")
            col_group, col_cat, col_job, col_player = st.columns(4)
            
            # Step 1. 職業群
            with col_group:
                groups = df_hierarchy['group'].unique().tolist()
                selected_group = st.selectbox("1️⃣ 職業群", groups, index=None, placeholder="請選擇...")

            # Step 2. 分類
            with col_cat:
                if selected_group:
                    categories = df_hierarchy[df_hierarchy['group'] == selected_group]['category'].unique().tolist()
                    selected_category = st.selectbox("2️⃣ 分類", categories, index=None, placeholder="請選擇...")
                else:
                    st.selectbox("2️⃣ 分類", [], disabled=True, placeholder="請先選職業群")
                    selected_category = None

            # Step 3. 職業
            with col_job:
                if selected_category:
                    jobs = df_hierarchy[
                        (df_hierarchy['group'] == selected_group) & 
                        (df_hierarchy['category'] == selected_category)
                    ]['job'].unique().tolist()
                    selected_job = st.selectbox("3️⃣ 職業", jobs, index=None, placeholder="請選擇...")
                else:
                    st.selectbox("3️⃣ 職業", [], disabled=True, placeholder="請先選分類")
                    selected_job = None

            # Step 4. 玩家 ID
            with col_player:
                if selected_job:
                    players_in_job = sorted(df[df['職業'] == selected_job]['暱稱'].unique().tolist())
                    if not players_in_job:
                        st.warning("無數據")
                        final_selected_player = None
                    else:
                        final_selected_player = st.selectbox("4️⃣ 玩家 ID", players_in_job, index=None, placeholder="請選擇玩家...")
                else:
                    st.selectbox("4️⃣ 玩家 ID", [], disabled=True, placeholder="請先選職業")
                    final_selected_player = None

        # === 模式 2: 直接搜尋 ===
        elif search_mode == "個人查詢 (直接搜尋)":
            st.caption("直接輸入關鍵字搜尋玩家 ID")
            col_search_1, col_search_2 = st.columns([1, 3])
            
            with col_search_1:
                st.markdown("**🔎 搜尋玩家**")
            
            with col_search_2:
                all_players_list = sorted(df['暱稱'].unique().tolist())
                final_selected_player = st.selectbox(
                    "請輸入或選擇玩家 ID：",
                    all_players_list,
                    index=None,
                    placeholder="輸入玩家 ID..."
                )

    # ==========================================
    # 4. 個人資料過濾與顯示 (維持不變)
    # ==========================================

    # 檢查是否有選到人
    if not final_selected_player:
        st.markdown("---")
        st.info("👋 請在上方選擇一位玩家以查看詳細數據。")
        # 這裡不使用 st.stop()，避免切換到排行榜時卡住，改用縮排邏輯
        
    else:
        # 再從 df_period (已篩選日期) 中篩選出「選定玩家」的資料
        df_filtered = df_period[df_period['暱稱'] == final_selected_player]

        if len(df_filtered) == 0:
            st.warning(f"玩家 {final_selected_player} 在此日期區間內無資料。")
        else:
            # --- 智慧搜尋：不只找最新，還要找「有資料」的那一筆 ---

            # 1. 先把資料按日期「由新到舊」排序
            df_sorted = df_filtered.sort_values('周次', ascending=False)

            # 2. 預設先抓第一筆 (最新的)
            player_info = df_sorted.iloc[0]
            current_level = player_info.get('等級', 0)
            img_url = player_info.get('圖片', None)

            # 3. 如果最新的這筆資料壞掉了 (等級是 0 或 NaN)，我們就往下找舊資料
            if pd.to_numeric(current_level, errors='coerce') == 0 or pd.isna(current_level):
                valid_rows = df_sorted[pd.to_numeric(df_sorted['等級'], errors='coerce') > 0]
                if not valid_rows.empty:
                    player_info = valid_rows.iloc[0] 
                    current_level = player_info.get('等級')
                    img_url = player_info.get('圖片')

            # 確保顯示格式
            if str(current_level) == "0" or str(current_level) == "nan":
                display_level = "???"
            else:
                display_level = int(float(current_level)) 

            # 取得職業 (顯示用)
            job_display = player_info.get('職業', '未知')
            if str(job_display) == 'nan': job_display = '未知'

            # --- 標題 ---
            st.markdown(f"## 👤 {final_selected_player} 的個人數據報告 (Lv. {display_level})")

            # --- 玩家檔案卡片 ---
            with st.container(border=True):
                col_profile_img, col_profile_info = st.columns([1.5, 3.5])
                
                with col_profile_img:
                    # 顯示圖片 (過濾掉 nan 或空字串)
                    if img_url and str(img_url) != "nan" and str(img_url).strip() != "":
                        st.image(img_url, width=130)
                    else:
                        st.markdown("# 👤") 
                        
                with col_profile_info:
                    st.markdown(f"""
                    #### 📜 角色詳細資料
                    
                    * **職業：** {job_display}
                    * **等級：** {display_level}
                    * **資料來源：** 靜態資料庫 (非即時API回溯法)
                    """)

            st.markdown("---")

            # ==========================================
            # 6. KPI 計算與排名系統
            # ==========================================

            # 1. 準備排名資料
            guild_stats = df_period.groupby('暱稱').agg({
                '旗幟戰': 'sum',
                '地下水道': 'sum',
                '公會城每周': 'sum',
                '周次': 'nunique'
            })

            # 2. 計算排名
            guild_stats['flag_rank'] = guild_stats['旗幟戰'].rank(ascending=False, method='min')
            guild_stats['water_rank'] = guild_stats['地下水道'].rank(ascending=False, method='min')
            guild_stats['castle_rank'] = guild_stats['公會城每周'].rank(ascending=False, method='min')

            # 3. 抓取目前玩家的資料
            my_stats = guild_stats.loc[final_selected_player]
            p_flag = int(my_stats['旗幟戰'])
            p_water = int(my_stats['地下水道'])
            p_castle = int(my_stats['公會城每周'])
            my_weeks = int(my_stats['周次']) 
            rank_flag = int(my_stats['flag_rank'])
            rank_water = int(my_stats['water_rank'])
            rank_castle = int(my_stats['castle_rank'])

            # 4. 平均值計算
            avg_flag = int(p_flag / my_weeks) if my_weeks > 0 else 0
            avg_water = int(p_water / my_weeks) if my_weeks > 0 else 0
            avg_castle_pct = int(float(p_castle / my_weeks)*10000)/100 if my_weeks > 0 else 0

            # --- 輔助函式：取得排名獎牌 ---
            def get_rank_icon(rank):
                if rank == 1:
                    return "🥇 "
                elif rank == 2:
                    return "🥈 "
                elif rank == 3:
                    return "🥉 "
                else:
                    return ""   

            # --- 函式：取得詳細鄰居資訊 ---
            def get_detailed_neighbors(df_source, target_player, col_sum, col_weeks, mode='avg'):
                df_sorted = df_source.sort_values(by=col_sum, ascending=False).reset_index()
                
                try:
                    my_score = df_sorted[df_sorted['暱稱'] == target_player][col_sum].values[0]
                    my_idx = df_sorted[df_sorted['暱稱'] == target_player].index[0]
                except IndexError:
                    return None, None

                def format_row(row, idx, is_neighbor=True):
                    score = int(row[col_sum])
                    weeks = int(row[col_weeks])
                    neighbor_name = row['暱稱']
                    
                    real_rank = int(df_source.loc[neighbor_name][f"{'flag' if col_sum == '旗幟戰' else 'water' if col_sum == '地下水道' else 'castle'}_rank"])
                    
                    tie_text = " (同分)" if is_neighbor and score == my_score else ""
                    
                    if mode == 'avg':
                        avg_val = int(score / weeks) if weeks > 0 else 0
                        return f"第 {real_rank} 名{tie_text} : {score:,} (均 {avg_val:,})"
                    else: # percent
                        pct_val = int(float(score / weeks)*10000)/100 if weeks > 0 else 0.0
                        return f"第 {real_rank} 名{tie_text} : {score} ({pct_val}%)"

                if my_idx > 0:
                    prev_row = df_sorted.iloc[my_idx - 1]
                    prev_str = f"⬆️ {format_row(prev_row, my_idx)}" 
                else:
                    prev_str = "👑 目前第一"

                if my_idx < len(df_sorted) - 1:
                    next_row = df_sorted.iloc[my_idx + 1]
                    next_str = f"⬇️ {format_row(next_row, my_idx + 2)}"
                else:
                    next_str = "🛡️ 目前墊底"
                    
                return prev_str, next_str

            # --- 介面顯示區 ---
            st.markdown("### 🏆 本周戰績與排名情報")

            col1, col2, col3, col4 = st.columns(4)

            # (1) 週數卡片
            with col1:
                with st.container(border=True):
                    st.markdown("#### 📊 統計週數")
                    st.markdown(f"## :orange[{my_weeks} 週]")
                    st.markdown("### 📅 區間累計") 
                    
                    st.divider()
                    st.caption(f"📅 **開始**：{start_date}")
                    st.caption(f"📅 **結束**：{end_date}")

            # (2) 旗幟戰卡片
            with col2:
                with st.container(border=True):
                    st.markdown("#### 🚩 旗幟戰")
                    st.markdown(f"## :orange[{p_flag:,}]")
                    
                    rank_icon = get_rank_icon(rank_flag)
                    st.markdown(f"### {rank_icon}第 {rank_flag} 名 <span style='font-size:0.6em; color:gray'>(均 {avg_flag:,})</span>", unsafe_allow_html=True)
                    
                    prev_txt, next_txt = get_detailed_neighbors(guild_stats, final_selected_player, '旗幟戰', '周次', mode='avg')
                    
                    st.divider()
                    st.caption(prev_txt)
                    st.caption(next_txt)

            # (3) 水道卡片
            with col3:
                with st.container(border=True):
                    st.markdown("#### 💧 地下水道")
                    st.markdown(f"## :orange[{p_water:,}]")
                    
                    rank_icon = get_rank_icon(rank_water)
                    st.markdown(f"### {rank_icon}第 {rank_water} 名 <span style='font-size:0.6em; color:gray'>(均 {avg_water:,})</span>", unsafe_allow_html=True)
                    
                    prev_txt, next_txt = get_detailed_neighbors(guild_stats, final_selected_player, '地下水道', '周次', mode='avg')
                    
                    st.divider()
                    st.caption(prev_txt)
                    st.caption(next_txt)

            # (4) 公會城卡片
            with col4:
                with st.container(border=True):
                    castle_title = "🏰 公會城"
                    if avg_castle_pct == 100:
                        castle_title = "👑 公會城 (全勤)"
                        
                    st.markdown(f"#### {castle_title}")
                    st.markdown(f"## :orange[{p_castle} 次]")
                    
                    if avg_castle_pct == 100:
                        st.markdown(f"### 👑 :rainbow[完美全勤!!] <span style='font-size:0.6em; color:gray'>({avg_castle_pct}%)</span>", unsafe_allow_html=True)
                    else:
                        rank_icon = get_rank_icon(rank_castle)
                        st.markdown(f"### {rank_icon}第 {rank_castle} 名 <span style='font-size:0.6em; color:gray'>({avg_castle_pct}%)</span>", unsafe_allow_html=True)
                        
                    prev_txt, next_txt = get_detailed_neighbors(guild_stats, final_selected_player, '公會城每周', '周次', mode='pct')
                    
                    st.divider()
                    st.caption(prev_txt)
                    st.caption(next_txt)

            # ==========================================
            # 7. 圖表與詳細資料區
            # ==========================================
            tab1, tab2, tab3 = st.tabs(["📈 個人走勢圖", "📋 詳細記錄", "🍩 達成狀況"])

            with tab1:
                chart_type = st.radio(
                    "選擇數據類型", 
                    ["旗幟戰", "地下水道", "公會城每周"], 
                    horizontal=True
                )
                
                if chart_type == "旗幟戰":
                    line_color = "#FF6B6B"  
                    y_label = "分數"
                elif chart_type == "地下水道":
                    line_color = "#4D96FF"  
                    y_label = "分數"
                else: 
                    line_color = "#6BCB77"  
                    y_label = "完成狀態 (1=有, 0=無)"

                fig_line = px.line(
                    df_filtered,
                    x='周次',
                    y=chart_type,
                    title=f"{final_selected_player} - {chart_type} 趨勢",
                    markers=True,
                )

                fig_line.update_traces(
                    line_color=line_color,
                    line_width=3,
                    marker_size=6,
                    marker_color=line_color,
                    name="實際分數" 
                )

                if chart_type == "地下水道" and len(df_filtered) > 1:
                    try:
                        x_dates = df_filtered['周次']
                        y_data = df_filtered[chart_type]
                        x_numeric = pd.to_numeric(x_dates) 
                        
                        slope, intercept = np.polyfit(x_numeric, y_data, 1)
                        trend_y = slope * x_numeric + intercept
                        
                        fig_line.add_scatter(
                            x=x_dates,
                            y=trend_y,
                            mode='lines',
                            name='📈 成長趨勢', 
                            line=dict(color='red', width=2, dash='dash'),
                            hoverinfo='skip'
                        )
                    except Exception:
                        pass 

                avg_score = df_filtered[chart_type].mean()
                if chart_type != "公會城每周" and avg_score > 0:
                    fig_line.add_hline(
                        y=avg_score, 
                        line_dash="dot", 
                        line_color="gray", 
                        annotation_text=f"平均: {int(avg_score):,}", 
                        annotation_position="bottom right"
                    )

                fig_line.update_layout(
                    xaxis_title="",          
                    yaxis_title=y_label,
                    hovermode="x unified",
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    xaxis=dict(tickformat="%Y-%m-%d")
                )
                
                st.plotly_chart(fig_line, use_container_width=True)
                
                if chart_type == "公會城每周":
                    st.caption("ℹ️ 1 代表有完成，0 代表未完成")

            with tab2:
                display_cols = ['周次', '職業', '暱稱', '旗幟戰', '地下水道', '公會城每周', '本周是否達成']
                st.dataframe(df_filtered[display_cols], use_container_width=True, hide_index=True)

            with tab3:
                achievement_counts = df_filtered['本周是否達成'].value_counts().reset_index()
                achievement_counts.columns = ['狀態', '數量']
                
                color_map = {'達成': '#00CC96', '未達成': '#EF553B', 'NA': '#636EFA'}

                if not achievement_counts.empty:
                    fig_pie = px.pie(
                        achievement_counts, 
                        values='數量', 
                        names='狀態', 
                        title='個人達成率統計',
                        color='狀態',
                        color_discrete_map=color_map,
                        hole=0.6
                    )
                    achieved_num = achievement_counts[achievement_counts['狀態']=='達成']['數量'].sum()
                    fig_pie.add_annotation(text=f"達成<br>{achieved_num}次", showarrow=False, font_size=20)
                    st.plotly_chart(fig_pie, use_container_width=True)
                else:
                    st.info("此區間無資料")

