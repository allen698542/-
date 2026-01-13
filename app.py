import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import datetime
# ==========================================
# API 串接設定 (新功能)
# ==========================================
# 嘗試從 Secrets 讀取 Key，如果沒有設定就不執行 API
API_KEY = st.secrets.get("NEXON_API_KEY", None)

@st.cache_data(ttl=3600) # 設定快取 1 小時，避免一直扣 API 額度
def get_maple_character_info(character_name):
    if not API_KEY:
        return None, "未設定 API Key"
    
    headers = {
        "x-nxopen-api-key": API_KEY,
        "accept": "application/json"
    }
    
    try:
        # 1. 取得 OCID (把暱稱換成 ID)
        url_id = "https://open.api.nexon.com/maplestory/v1/id"
        resp_id = requests.get(url_id, headers=headers, params={"character_name": character_name})
        
        if resp_id.status_code != 200:
            return None, "找不到角色或 API 額度不足"
        
        ocid = resp_id.json().get("ocid")
        
        # 2. 取得角色基本資料
        # 注意：API 資料通常會有延遲，我們抓「昨天」的資料比較保險
        yesterday = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        url_basic = "https://open.api.nexon.com/maplestory/v1/character/basic"
        resp_basic = requests.get(url_basic, headers=headers, params={"ocid": ocid, "date": yesterday})
        
        if resp_basic.status_code == 200:
            return resp_basic.json(), None # 回傳資料
        else:
            return None, "無法讀取角色資料"
            
    except Exception as e:
        return None, f"連線錯誤: {e}"

#====================================================================================================
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
# 3. 介面與搜尋邏輯 (核心修改區)
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

# 使用 Radio Button 切換模式
search_mode = st.radio(
    "請選擇查詢方式：",
    ["層級篩選 (職業分類)", "直接搜尋 (輸入 ID)"],
    horizontal=True
)

final_selected_player = None # 最終要查詢的玩家

with st.container(border=True):
    
    # === 模式 A: 層級篩選 (原本的功能) ===
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

    # === 模式 B: 直接搜尋 (新功能) ===
    else:
        st.caption("直接輸入關鍵字搜尋玩家 ID")
        col_search_1, col_search_2 = st.columns([1, 3])
        
        with col_search_1:
            st.markdown("**🔎 搜尋玩家**")
        
        with col_search_2:
            # 取得全伺服器所有玩家名單
            all_players_list = sorted(df['暱稱'].unique().tolist())
            
            # 使用 selectbox 讓它可以打字搜尋，也能下拉選擇
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

# 開始過濾
mask = (df['周次'] >= pd.to_datetime(start_date)) & (df['周次'] <= pd.to_datetime(end_date))
mask = mask & (df['暱稱'] == final_selected_player)

df_filtered = df[mask]

# ==========================================
# 5. 個人數據儀表板
# ==========================================

if len(df_filtered) == 0:
    st.warning(f"玩家 {final_selected_player} 在此日期區間內無資料。")
    st.stop()

st.markdown(f"### 👤 {final_selected_player} 的個人數據報告")
st.markdown("---")

# ==================== 新增：API 資訊卡片區 ====================
# 呼叫上面的函式去抓資料
api_data, api_error = get_maple_character_info(final_selected_player)

if api_data:
    # 如果抓到資料，切分版面顯示頭像
    col_api_img, col_api_info = st.columns([1, 4])
    
    with col_api_img:
        # 顯示角色圖片
        st.image(api_data.get('character_image'), width=150)
        
    with col_api_info:
        # 顯示角色詳細資訊
        st.markdown(f"""
        **職業**: {api_data.get('character_class')}  
        **等級**: Lv. {api_data.get('character_level')}  
        **伺服器**: {api_data.get('world_name')}
        """)
elif API_KEY:
    # 有 Key 但抓不到 (可能是 ID 打錯或 API 維修)
    st.caption(f"⚠️ 無法載入 API 資訊: {api_error} (可能是官方資料延遲或暱稱不符)")
# ==================== 結束 API 區塊 ====================

# (下面接回原本的 KPI 計算與顯示程式碼)
# 計算數值
p_flag = int(df_filtered['旗幟戰'].sum())

# 計算數值
p_flag = int(df_filtered['旗幟戰'].sum())
p_water = int(df_filtered['地下水道'].sum())
p_castle = int(df_filtered['公會城每周'].sum())

# 取得資料總筆數 (週數)
total_weeks = len(df_filtered)

# 計算平均值 (避免除以 0，雖然上面有擋但在數學運算上保持嚴謹)
avg_flag = int(p_flag / total_weeks) if total_weeks > 0 else 0
avg_water = int(p_water / total_weeks) if total_weeks > 0 else 0
avg_castle = int(float(p_castle / total_weeks)*10000)/100 if total_weeks > 0 else 0

# KPI
col1, col2, col3, col4 = st.columns(4)
col1.metric("📊 資料筆數", f"{len(df_filtered)} 週")
col2.metric("🚩 旗幟戰總分", f"{p_flag:,}",delta=f"平均一周 {avg_flag:,}分", delta_color="off")
col3.metric("💧 水道總傷分", f"{p_water:,}",delta=f"平均一周 {avg_water:,}分", delta_color="off")
col4.metric("🏰 公會城完成數", f"{p_castle} 次",delta=f"達成率 {avg_castle:,}%", delta_color="off")

# 圖表
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
















