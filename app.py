import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import datetime

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
    df = pd.read_excel("data.xlsx")
    
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

# --- 搜尋模式切換 ---
st.markdown("### 🔍 成員查詢面板")

search_mode = st.radio(
    "請選擇查詢方式：",
    ["層級篩選 (職業分類)", "直接搜尋 (輸入 ID)"],
    horizontal=True
)

final_selected_player = None 

with st.container(border=True):
    
    # === 模式 A: 層級篩選 ===
    if search_mode == "層級篩選 (職業分類)":
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

    # === 模式 B: 直接搜尋 ===
    else:
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
# 4. 資料過濾與顯示
# ==========================================

# 檢查是否有選到人
if not final_selected_player:
    st.markdown("---")
    st.info("👋 請在上方選擇一位玩家以查看詳細數據。")
    st.stop()

# --- 分開篩選 (為了計算排名) ---
# 1. 先篩選出「符合日期區間」的所有資料 (用來算全公會排名)
mask_period = (df['周次'] >= pd.to_datetime(start_date)) & (df['周次'] <= pd.to_datetime(end_date))
df_period = df[mask_period]

# 2. 再從上面篩選出「選定玩家」的資料 (用來畫圖與顯示個人數值)
df_filtered = df_period[df_period['暱稱'] == final_selected_player]

# ==========================================
# 5. 個人數據儀表板 (含 API 資訊)
# ==========================================

if len(df_filtered) == 0:
    st.warning(f"玩家 {final_selected_player} 在此日期區間內無資料。")
    st.stop()

# --- 1. 標題與 API 資料 ---
api_data, api_error = get_maple_character_info(final_selected_player)

header_text = f"👤 {final_selected_player} 的個人數據報告"
if api_data:
    level = api_data.get('character_level', '???')
    header_text = f"👤 {final_selected_player} 的個人數據報告 (Lv. {level})"

st.markdown(f"## {header_text}")

# --- 2. 玩家檔案卡片 ---
with st.container(border=True):
    if api_data:
        # 處理圖片
        img_url = api_data.get('character_image')
        # 處理登入狀態
        raw_flag = api_data.get('access_flag')
        
        if str(raw_flag).lower() == 'true':
            login_status = "✅ **近期活躍** (7天內有登入)"
        elif str(raw_flag).lower() == 'false':
            login_status = "💤 **近期不活躍** (7天未登入)"
        else:
            login_status = "❓ **無法取得** (需查詢公會 API)"

        col_profile_img, col_profile_info = st.columns([1.5, 3.5])
        
        with col_profile_img:
            if img_url:
                st.image(img_url, width=130)
            else:
                st.markdown("# 👤")
            
        with col_profile_info:
            st.markdown(f"""
            #### 📜 角色詳細資料
            
            * **職業：** {api_data.get('character_class')}
            * **等級：** {api_data.get('character_level')}
            * **狀態：** {login_status}
            """)
            
    elif API_KEY and api_error:
        st.warning(f"無法載入官方資訊：{api_error}")
    else:
        st.info("未設定 API Key，僅顯示 Excel 紀錄。")

st.markdown("---")

# ==========================================
# 6. KPI 計算與排名系統 (含 Top3 特效)
# ==========================================

# 1. 準備排名資料
# 這裡將全公會(df_period)依據ID加總
guild_ranking = df_period.groupby('暱稱')[['旗幟戰', '地下水道', '公會城每周']].sum()

# 2. 計算排名 (method='min' 代表並列名次處理方式)
guild_ranking['flag_rank'] = guild_ranking['旗幟戰'].rank(ascending=False, method='min')
guild_ranking['water_rank'] = guild_ranking['地下水道'].rank(ascending=False, method='min')
guild_ranking['castle_rank'] = guild_ranking['公會城每周'].rank(ascending=False, method='min')

# 3. 抓取目前玩家的總分與排名
my_stats = guild_ranking.loc[final_selected_player]

p_flag = int(my_stats['旗幟戰'])
p_water = int(my_stats['地下水道'])
p_castle = int(my_stats['公會城每周'])

rank_flag = int(my_stats['flag_rank'])
rank_water = int(my_stats['water_rank'])
rank_castle = int(my_stats['castle_rank'])

# 4. 其他數值計算
total_weeks = df_filtered['周次'].nunique() # 資料週數

# 5. 平均值計算
avg_flag = int(p_flag / total_weeks) if total_weeks > 0 else 0
avg_water = int(p_water / total_weeks) if total_weeks > 0 else 0
avg_castle_pct = int(float(p_castle / total_weeks)*10000)/100 if total_weeks > 0 else 0

# --- 🏆 排名特效邏輯區 ---

# (A) 旗幟戰特效
if rank_flag == 1:
    flag_label = f"🥇 公會第一 (均 {avg_flag:,})"
elif rank_flag == 2:
    flag_label = f"🥈 公會第二 (均 {avg_flag:,})"
elif rank_flag == 3:
    flag_label = f"🥉 公會第三 (均 {avg_flag:,})"
else:
    flag_label = f"第 {rank_flag} 名 (均 {avg_flag:,})"

# (B) 水道特效
if rank_water == 1:
    water_label = f"🥇 公會第一 (均 {avg_water:,})"
elif rank_water == 2:
    water_label = f"🥈 公會第二 (均 {avg_water:,})"
elif rank_water == 3:
    water_label = f"🥉 公會第三 (均 {avg_water:,})"
else:
    water_label = f"第 {rank_water} 名 (均 {avg_water:,})"

# (C) 公會城特效 (第一名給皇冠)
if rank_castle == 1 and avg_castle_pct == 100:
    # 修改：把皇冠放最前面，並用 " | " 符號區隔，看起來乾淨很多
    castle_label = f"🥇 公會第一 ({avg_castle_pct}%) | 👑 完美全勤"
elif rank_castle == 1:
    castle_label = f"🥇 公會第一 (達成率 {avg_castle_pct}%)"
elif rank_castle == 2:
    castle_label = f"🥈 公會第二 (達成率 {avg_castle_pct}%)"
elif rank_castle == 3:
    castle_label = f"🥉 公會第三 (達成率 {avg_castle_pct}%)"
else:
    castle_label = f"第 {rank_castle} 名 (達成率 {avg_castle_pct}%)"

# --- 顯示 KPI ---
col1, col2, col3, col4 = st.columns(4)

col1.metric("📊 資料筆數", f"{total_weeks} 週")

col2.metric("🚩 旗幟戰總分", f"{p_flag:,}", flag_label)
col3.metric("💧 水道總傷分", f"{p_water:,}", water_label)
col4.metric("🏰 公會城完成數", f"{p_castle} 次", castle_label)

# ==========================================
# 7. 圖表與詳細資料區
# ==========================================
tab1, tab2, tab3 = st.tabs(["📈 個人走勢圖", "📋 詳細記錄", "🍩 達成狀況"])

with tab1:
    chart_type = st.radio("選擇數據類型", ["旗幟戰", "地下水道", "公會城每周"], horizontal=True)
    
    fig_line = px.line(
        df_filtered,
        x='周次',
        y=chart_type,
        title=f"{final_selected_player} - {chart_type} 趨勢",
        markers=True,
    )
    fig_line.update_layout(hovermode="x unified")
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




