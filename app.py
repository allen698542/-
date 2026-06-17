import streamlit as st
import pandas as pd
import plotly.express as px
import datetime
import numpy as np
import requests

# ==========================================
# 頁面設定 (必須在第一行)
# ==========================================
st.set_page_config(page_title="公會每周統計", page_icon="🍁", layout="wide")

# ==========================================
# [新增] 全域 CSS 樣式：定義彩虹文字特效 & 強制滾動鎖定
# ==========================================
st.markdown("""
<style>
/* 定義彩虹文字特效 */
.rainbow-text {
    background: linear-gradient(90deg, #ff0000, #ff7f00, #ffff00, #00ff00, #0000ff, #4b0082, #9400d3);
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-weight: bold;
    animation: rainbow-move 3s linear infinite;
}

/* 彩虹流動動畫 */
@keyframes rainbow-move {
    to {
        background-position: 200% center;
    }
}

/* === 終極版修改：強制防止表格滾動時帶動整個頁面 ===
   使用 none 並加上 !important 強制覆蓋 Streamlit 預設行為
*/
div[data-testid="stDataFrame"], 
div[data-testid="stDataFrame"] * {
    overscroll-behavior: none !important;
}
</style>
""", unsafe_allow_html=True)

# ==========================================
# API 串接設定
# ==========================================
API_KEY = st.secrets.get("NEXON_API_KEY", None)

# ==========================================
# 全域設定：圖表工具列與互動鎖定
# ==========================================
PLOT_CONFIG = {
    'displayModeBar': True, 
    'displaylogo': False,
    'modeBarButtonsToRemove': [
        'zoom2d', 'pan2d', 'select2d', 'lasso2d', 'zoomIn2d', 'zoomOut2d', 
        'autoScale2d', 'resetScale2d', 'hoverClosestCartesian', 'hoverCompareCartesian'
    ],
    'toImageButtonOptions': {
        'format': 'png',
        'filename': 'chart_image',
        'height': 600,
        'width': 1000,
        'scale': 2
    }
}

@st.cache_data(ttl=600)
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
        st.write(""); st.write(""); st.write("")
        c1, c2, c3 = st.columns([1, 1.5, 1])
        with c2:
            with st.container(border=True):
                st.markdown("<h3 style='text-align: center;'>🔐 請輸入密碼</h3>", unsafe_allow_html=True)
                password = st.text_input("密碼", type="password", label_visibility="collapsed")
                
                if password == actual_password or password == actual_password2:
                    st.session_state.password_correct = True
                    st.rerun()
                elif password:
                    st.error("❌ 密碼錯誤")
        return False
    return True

if not check_password():
    st.stop()

# ==========================================
# 2. 讀取與處理資料
# ==========================================
@st.cache_data(ttl=600)
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

st.sidebar.header("📅 日期區間設定")

data_min_date = df['周次'].min().date()
data_max_date = df['周次'].max().date()

col_start, col_end = st.sidebar.columns(2)

with col_start:
    start_date = st.date_input(
        "開始日期",
        value=data_min_date,      
        min_value=data_min_date,
        max_value=data_max_date,
        format="YYYY-MM-DD"        
    )

with col_end:
    end_date = st.date_input(
        "結束日期",
        value=data_max_date,      
        min_value=data_min_date,
        max_value=data_max_date,
        format="YYYY-MM-DD"
    )

if start_date > end_date:
    st.sidebar.error("⚠️ 「開始日期」不能晚於「結束日期」")

mask_period = (df['周次'].dt.date >= start_date) & (df['周次'].dt.date <= end_date)
df_period = df[mask_period]

st.markdown("### 🔍 功能面板")

search_mode = st.radio(
    "請選擇功能：",
    ["個人查詢 (層級篩選)", "個人查詢 (直接搜尋)", "🏆 全公會排行榜", "📂 原始資料查詢"],
    horizontal=True
)

# ==========================================
# 分支 A: 全公會排行榜
# ==========================================
if search_mode == "🏆 全公會排行榜":
    st.markdown("---")
    st.markdown(f"### 📊 公會排行榜 ({start_date} ~ {end_date})")
    
    leaderboard_df = df_period.groupby('暱稱').agg({
        '旗幟戰': 'sum',
        '地下水道': 'sum',
        '公會城每周': 'sum',
        '周次': 'nunique',
        '職業': 'first',
        '圖片': 'first'
    }).reset_index()
    
    tab_rank_flag, tab_rank_water, tab_rank_castle = st.tabs(["🚩 旗幟戰排行", "💧 地下水道排行", "🏰 公會城全勤榜"])
    
    def draw_leaderboard(data, col_name, color_scale, label_name, is_attendance=False):
        sorted_df = data.sort_values(by=col_name, ascending=False).reset_index(drop=True)
        sorted_df['名次'] = sorted_df.index + 1
        
        def get_img_tag(url, width=150):
            if url and str(url) != "nan" and str(url).strip() != "":
                return f'<img src="{url}" style="width: {width}px; height: auto; border-radius: 8px; object-fit: contain; margin: 5px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.3);">'
            return ""

        # 使用單行 CSS 並放大字體
        base_style = "text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.3); height: 100%;"

        style_1st = f"""
            <div style="{base_style} padding: 12px; border-radius: 15px; border: 3px solid #FFD700; background: linear-gradient(135deg, #262730 0%, #3a3200 100%); box-shadow: 0 0 20px rgba(255, 215, 0, 0.4);">
                <div style="font-size: 2.5rem; line-height: 1; margin-bottom: 5px;">{{icon}}</div>
                {{img_tag}}
                <div style="font-size: 1.6rem; font-weight: bold; color: #FFF; margin-bottom: 2px; margin-top: 5px;">{{name}}</div>
                <div style="font-size: 1.1rem; color: #BBB;">{{score_label}}</div>
                <div style="font-size: 2.2rem; font-weight: bold; color: {{color}};">{{score}}</div>
            </div>
        """
        
        style_2nd3rd = f"""
            <div style="{base_style} padding: 10px; border-radius: 12px; background-color: #262730; border: 2px solid {{border_color}};">
                <div style="font-size: 2.8rem; line-height: 1; margin-bottom: 5px;">{{icon}}</div>
                {{img_tag}}
                <div style="font-size: 1.3rem; font-weight: bold; color: #EEE; margin-bottom: 2px; margin-top: 5px;">{{name}}</div>
                <div style="font-size: 1rem; color: #BBB;">{{score_label}}</div>
                <div style="font-size: 1.8rem; font-weight: bold; color: {{color}};">{{score}}</div>
            </div>
        """

        style_4th5th = f"""
            <div style="{base_style} padding: 8px; border-radius: 10px; background-color: #20212b; border: 1px solid #444;">
                <div style="font-size: 2.2rem; line-height: 1; margin-bottom: 5px;">{{icon}}</div>
                {{img_tag}}
                <div style="font-size: 1.2rem; font-weight: bold; color: #DDD; margin-bottom: 2px; margin-top: 5px;">{{name}}</div>
                <div style="font-size: 0.9rem; color: #BBB;">{{score_label}}</div>
                <div style="font-size: 1.6rem; font-weight: bold; color: {{color}};">{{score}}</div>
            </div>
        """

        cols = st.columns([0.9, 1.1, 1.3, 1.1, 0.9])
        spacer_mid = 3 
        spacer_low = 6 

        # 排行榜前五名顯示邏輯
        with cols[0]:
            if len(sorted_df) > 3:
                p = sorted_df.iloc[3]
                for _ in range(spacer_low): st.write("")
                st.markdown(style_4th5th.format(
                    icon="4️⃣", img_tag=get_img_tag(p.get('圖片'), width=110), 
                    name=p['暱稱'], score_label="分數", score=f"{int(p[col_name]):,}", color="#4D96FF"
                ), unsafe_allow_html=True)
        with cols[1]:
            if len(sorted_df) > 1:
                p = sorted_df.iloc[1]
                for _ in range(spacer_mid): st.write("")
                st.markdown(style_2nd3rd.format(
                    icon="🥈", img_tag=get_img_tag(p.get('圖片'), width=130), 
                    name=p['暱稱'], score_label="分數", score=f"{int(p[col_name]):,}", 
                    color="#C0C0C0", border_color="#C0C0C0"
                ), unsafe_allow_html=True)
        with cols[2]:
            if len(sorted_df) > 0:
                p = sorted_df.iloc[0]
                st.markdown(style_1st.format(
                    icon="🥇", img_tag=get_img_tag(p.get('圖片'), width=150), 
                    name=p['暱稱'], score_label="分數", score=f"{int(p[col_name]):,}", color="#FFD700"
                ), unsafe_allow_html=True)
        with cols[3]:
            if len(sorted_df) > 2:
                p = sorted_df.iloc[2]
                for _ in range(spacer_mid): st.write("")
                st.markdown(style_2nd3rd.format(
                    icon="🥉", img_tag=get_img_tag(p.get('圖片'), width=130), 
                    name=p['暱稱'], score_label="分數", score=f"{int(p[col_name]):,}", 
                    color="#CD7F32", border_color="#CD7F32"
                ), unsafe_allow_html=True)
        with cols[4]:
            if len(sorted_df) > 4:
                p = sorted_df.iloc[4]
                for _ in range(spacer_low): st.write("")
                st.markdown(style_4th5th.format(
                    icon="5️⃣", img_tag=get_img_tag(p.get('圖片'), width=110), 
                    name=p['暱稱'], score_label="分數", score=f"{int(p[col_name]):,}", color="#4D96FF"
                ), unsafe_allow_html=True)

        st.markdown("---")
        
        top15_df = sorted_df.head(15).copy()
        fig = px.bar(top15_df, x=col_name, y='暱稱', orientation='h', text=col_name, title=f"🏆 {label_name} Top 15", color=col_name, color_continuous_scale=color_scale)
        fig.update_layout(yaxis={'categoryorder':'total ascending', 'fixedrange': True}, xaxis={'fixedrange': True}, dragmode=False)
        fig.update_traces(texttemplate='%{text:,}', textposition='outside')
        st.plotly_chart(fig, use_container_width=True, config=PLOT_CONFIG)
        
        st.markdown("#### 📋 完整名單")
        display_df = sorted_df[['名次', '暱稱', '職業', '周次', col_name]].copy()
        val_format = "%d 次" if is_attendance else "%d"
        st.dataframe(display_df, use_container_width=True, hide_index=True, column_config={col_name: st.column_config.ProgressColumn(label_name, format=val_format, min_value=0, max_value=int(sorted_df[col_name].max()) if len(sorted_df) > 0 else 100,), "名次": st.column_config.NumberColumn(format="No. %d")})

    with tab_rank_flag:
        draw_leaderboard(leaderboard_df, '旗幟戰', 'Reds', '旗幟戰分數')
    with tab_rank_water:
        draw_leaderboard(leaderboard_df, '地下水道', 'Blues', '地下水道分數')
    with tab_rank_castle:
        draw_leaderboard(leaderboard_df, '公會城每周', 'Greens', '公會城參與數', is_attendance=True)

# ==========================================
# 分支 B: 原始資料查詢
# ==========================================
elif search_mode == "📂 原始資料查詢":
    st.markdown("---")
    st.markdown("### 📂 原始資料庫搜尋")
    
    # 1. 搜尋框
    search_query = st.text_input("🔍 請輸入關鍵字 (搜尋暱稱、職業、分數、達成狀態...)", placeholder="例如: 陰陽師, 1000, 達成...")
    
    # 2. 篩選邏輯
    if search_query:
        mask = df_period.astype(str).apply(lambda x: x.str.contains(search_query, case=False, na=False)).any(axis=1)
        df_display = df_period[mask]
        st.success(f"🔍 搜尋結果：共找到 {len(df_display)} 筆資料")
    else:
        df_display = df_period
        st.info(f"💡 顯示目前日期區間內的所有資料，目前共有 {len(df_display)} 筆資料")

    # 3. 資料處理：排序並重置索引 (解決 unhashable type Error)
    df_display = df_display.sort_values('周次', ascending=False).reset_index(drop=True)
    
    target_cols = [
        '周次', '暱稱', '職業', '旗幟戰', '地下水道', '公會城每周', 
        '本周是否達成', '近兩周是否達成', '異動與否'
    ]
    cols_to_show = [col for col in target_cols if col in df_display.columns]

    st.dataframe(
        df_display[cols_to_show], 
        use_container_width=True, 
        hide_index=True,
        height=800,
        column_config={
            "周次": st.column_config.DateColumn("周次", format="YYYY-MM-DD")
        }
    )

# ==========================================
# 分支 C: 個人查詢模式
# ==========================================
else: 
    final_selected_player = None 
    
    # 變數初始化，避免 NameError
    selected_group = None
    selected_category = None
    selected_job = None

    with st.container(border=True):
        if search_mode == "個人查詢 (層級篩選)":
            st.caption("依序選擇：職業群 > 分類 > 職業 > 玩家")
            col_group, col_cat, col_job, col_player = st.columns(4)
            with col_group:
                groups = df_hierarchy['group'].unique().tolist()
                selected_group = st.selectbox("1️⃣ 職業群", groups, index=None, placeholder="請選擇...")
            with col_cat:
                if selected_group:
                    categories = df_hierarchy[df_hierarchy['group'] == selected_group]['category'].unique().tolist()
                    selected_category = st.selectbox("2️⃣ 分類", categories, index=None, placeholder="請選擇...")
                else: 
                    st.selectbox("2️⃣ 分類", [], disabled=True, placeholder="請先選職業群")
            with col_job:
                if selected_category:
                    jobs = df_hierarchy[(df_hierarchy['group'] == selected_group) & (df_hierarchy['category'] == selected_category)]['job'].unique().tolist()
                    selected_job = st.selectbox("3️⃣ 職業", jobs, index=None, placeholder="請選擇...")
                else: 
                    st.selectbox("3️⃣ 職業", [], disabled=True, placeholder="請先選分類")
            with col_player:
                if selected_job:
                    players_in_job = sorted(df[df['職業'] == selected_job]['暱稱'].unique().tolist())
                    if not players_in_job:
                        st.warning("無數據")
                        final_selected_player = None
                    else: final_selected_player = st.selectbox("4️⃣ 玩家 ID", players_in_job, index=None, placeholder="請選擇玩家...")
                else: st.selectbox("4️⃣ 玩家 ID", [], disabled=True, placeholder="請先選職業")

        elif search_mode == "個人查詢 (直接搜尋)":
            st.caption("直接輸入關鍵字搜尋玩家 ID")
            col_search_1, col_search_2 = st.columns([1, 3])
            with col_search_1: st.markdown("**🔎 搜尋玩家**")
            with col_search_2:
                all_players_list = sorted(df['暱稱'].unique().tolist())
                final_selected_player = st.selectbox("請輸入或選擇玩家 ID：", all_players_list, index=None, placeholder="輸入玩家 ID...")

    if not final_selected_player:
        st.markdown("---")
        st.info("👋 請在上方選擇一位玩家以查看詳細數據。")
    else:
        df_filtered = df_period[df_period['暱稱'] == final_selected_player]

        if len(df_filtered) == 0:
            st.warning(f"玩家 {final_selected_player} 在此日期區間內無資料。")
        else:
            df_sorted = df_filtered.sort_values('周次', ascending=False)
            player_info = df_sorted.iloc[0]
            
            # === 修正圖片消失問題：往回找歷史紀錄中的第一個有效等級與圖片 ===
            valid_levels = df_sorted[pd.to_numeric(df_sorted['等級'], errors='coerce') > 0]
            if not valid_levels.empty:
                display_level = int(float(valid_levels.iloc[0]['等級']))
            else:
                display_level = "???"

            valid_imgs = df_sorted[df_sorted['圖片'].notna() & (df_sorted['圖片'].astype(str).str.strip() != '') & (df_sorted['圖片'].astype(str).str.lower() != 'nan')]
            if not valid_imgs.empty:
                img_url = valid_imgs.iloc[0]['圖片']
            else:
                img_url = None

            job_display = player_info.get('職業', '未知')
            if str(job_display) == 'nan': job_display = '未知'

            st.markdown(f"## 👤 {final_selected_player} 的個人數據報告")

            with st.container(border=True):
                col_profile_img, col_profile_info = st.columns([1.5, 3.5])
                with col_profile_img:
                    if img_url: st.image(img_url, width=130)
                    else: st.markdown("# 👤") 
                with col_profile_info:
                    st.markdown(f"#### 📜 角色詳細資料\n* **職業：** {job_display}\n* **等級：** {display_level}\n* **資料來源：** 靜態資料庫 (非即時API回溯法)")

            st.markdown("---")

            # 計算公會排名
            guild_stats = df_period.groupby('暱稱').agg({'旗幟戰': 'sum', '地下水道': 'sum', '公會城每周': 'sum', '周次': 'nunique'})
            guild_stats['flag_rank'] = guild_stats['旗幟戰'].rank(ascending=False, method='min')
            guild_stats['water_rank'] = guild_stats['地下水道'].rank(ascending=False, method='min')
            guild_stats['castle_rank'] = guild_stats['公會城每周'].rank(ascending=False, method='min')

            my_stats = guild_stats.loc[final_selected_player]
            p_flag = int(my_stats['旗幟戰']); p_water = int(my_stats['地下水道']); p_castle = int(my_stats['公會城每周']); my_weeks = int(my_stats['周次']) 
            rank_flag = int(my_stats['flag_rank']); rank_water = int(my_stats['water_rank']); rank_castle = int(my_stats['castle_rank'])

            avg_flag = int(p_flag / my_weeks) if my_weeks > 0 else 0
            avg_water = int(p_water / my_weeks) if my_weeks > 0 else 0
            avg_castle_pct = int(float(p_castle / my_weeks)*10000)/100 if my_weeks > 0 else 0

            def get_rank_icon(rank):
                if rank == 1: return "🥇 "
                elif rank == 2: return "🥈 "
                elif rank == 3: return "🥉 "
                else: return ""     

            def get_detailed_neighbors(df_source, target_player, col_sum, col_weeks, mode='avg'):
                df_sorted = df_source.sort_values(by=col_sum, ascending=False).reset_index()
                try:
                    my_score = df_sorted[df_sorted['暱稱'] == target_player][col_sum].values[0]
                    my_idx = df_sorted[df_sorted['暱稱'] == target_player].index[0]
                except IndexError: return None, None

                def format_row(row, idx, is_neighbor=True):
                    score = int(row[col_sum]); weeks = int(row[col_weeks]); neighbor_name = row['暱稱']
                    real_rank = int(df_source.loc[neighbor_name][f"{'flag' if col_sum == '旗幟戰' else 'water' if col_sum == '地下水道' else 'castle'}_rank"])
                    tie_text = " (同分)" if is_neighbor and score == my_score else ""
                    if mode == 'avg':
                        avg_val = int(score / weeks) if weeks > 0 else 0
                        return f"第 {real_rank} 名{tie_text} : {score:,} (均 {avg_val:,})"
                    else: 
                        pct_val = int(float(score / weeks)*10000)/100 if weeks > 0 else 0.0
                        return f"第 {real_rank} 名{tie_text} : {score} ({pct_val}%)"

                if my_idx > 0: prev_str = f"⬆️ {format_row(df_sorted.iloc[my_idx - 1], my_idx)}" 
                else: prev_str = "👑 目前第一"
                if my_idx < len(df_sorted) - 1: next_str = f"⬇️ {format_row(df_sorted.iloc[my_idx + 1], my_idx + 2)}"
                else: next_str = "🛡️ 目前墊底"
                return prev_str, next_str

            st.markdown("### 🏆 本周戰績與排名情報")
            
            def draw_stat_card(title, score_str, rank_str, prev_txt, next_txt, rank=999):
                base_style = "box-sizing: border-box; border-radius: 10px; padding: 15px; height: 100%; display: flex; flex-direction: column; justify-content: space-between; flex-grow: 1;"

                if rank == 1:
                    container_style = f"{base_style} border: 3px solid #FFD700; background: linear-gradient(135deg, #262730 0%, #3a3200 100%); box-shadow: 0 0 55px rgba(255, 215, 0, 0.4); color: white;"
                    score_color = "#FFD700"
                elif rank == 2:
                    container_style = f"{base_style} border: 3px solid #C0C0C0; background: linear-gradient(135deg, #262730 0%, #383838 100%); box-shadow: 0 0 55px rgba(192, 192, 192, 0.4); color: white;"
                    score_color = "#E0E0E0" 
                elif rank == 3:
                    container_style = f"{base_style} border: 3px solid #CD7F32; background: linear-gradient(135deg, #262730 0%, #3a2500 100%); box-shadow: 0 0 55px rgba(205, 127, 50, 0.4); color: white;"
                    score_color = "#CD7F32"
                else:
                    container_style = f"{base_style} border: 3px solid #444; background-color: #262730; box-shadow: 0 1px 3px rgba(0,0,0,0.12); color: white;"
                    score_color = "#FF9F1C"

                html_code = f"""
                <div style="{container_style}">
                    <div>
                        <div style="font-weight: bold; font-size: 1.5rem; margin-bottom: 5px;">{title}</div>
                        <div style="font-size: 2.5rem; font-weight: bold; color: {score_color}; line-height: 1.2;">{score_str}</div>
                        <div style="font-size: 1.5rem; margin-bottom: 5px;">{rank_str}</div>
                    </div>
                    <div>
                        <hr style="margin: 10px 0; border-color: #555;">
                        <div style="font-size: 0.9rem; color: #CCC; margin-bottom: 3px;">{prev_txt}</div>
                        <div style="font-size: 0.9rem; color: #CCC;">{next_txt}</div>
                    </div>
                </div>
                """
                st.markdown(html_code, unsafe_allow_html=True)

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                left_card_style = "box-sizing: border-box; border-radius: 10px; padding: 15px; height: 100%; display: flex; flex-direction: column; justify-content: space-between; flex-grow: 1; border: 3px solid #444; background-color: #262730; box-shadow: 0 1px 3px rgba(0,0,0,0.12); color: white;"
                html_left = f"""
                <div style="{left_card_style}">
                    <div>
                        <div style="font-weight: bold; font-size: 1.5rem; margin-bottom: 5px;">📊 統計週數</div>
                        <div style="font-size: 2.5rem; font-weight: bold; color: #FF9F1C; line-height: 1.2;">{my_weeks} 週</div>
                        <div style="font-size: 1.5rem; margin-bottom: 5px;">📅 區間累計</div>
                    </div>
                    <div>
                        <hr style="margin: 10px 0; border-color: #555;">
                        <div style="font-size: 0.9rem; color: #CCC; margin-bottom: 3px;">📅 開始：{start_date}</div>
                        <div style="font-size: 0.9rem; color: #CCC;">📅 結束：{end_date}</div>
                    </div>
                </div>
                """
                st.markdown(html_left, unsafe_allow_html=True)

            with col2:
                prev_txt, next_txt = get_detailed_neighbors(guild_stats, final_selected_player, '旗幟戰', '周次', mode='avg')
                rank_str = f"{get_rank_icon(rank_flag)}第 {rank_flag} 名 <span style='font-size:1.0rem; color:#BBB'>(均 {avg_flag:,})</span>"
                draw_stat_card("🚩 旗幟戰", f"{p_flag:,} 分", rank_str, prev_txt, next_txt, rank=rank_flag)

            with col3:
                prev_txt, next_txt = get_detailed_neighbors(guild_stats, final_selected_player, '地下水道', '周次', mode='avg')
                rank_str = f"{get_rank_icon(rank_water)}第 {rank_water} 名 <span style='font-size:1.0rem; color:#BBB'>(均 {avg_water:,})</span>"
                draw_stat_card("💧 地下水道", f"{p_water:,} 分", rank_str, prev_txt, next_txt, rank=rank_water)

            with col4:
                castle_title = "👑 公會城 (全勤)" if avg_castle_pct == 100 else "🏰 公會城"
                prev_txt, next_txt = get_detailed_neighbors(guild_stats, final_selected_player, '公會城每周', '周次', mode='pct')
                
                if avg_castle_pct == 100:
                    rank_str = f"👑 <span class='rainbow-text'>完美全勤!!</span> <span style='font-size:1.0rem; color:#BBB'>({avg_castle_pct}%)</span>"
                    display_rank = 1 
                else:
                    rank_str = f"{get_rank_icon(rank_castle)}第 {rank_castle} 名 <span style='font-size:1.0rem; color:#BBB'>({avg_castle_pct}%)</span>"
                    display_rank = rank_castle

                draw_stat_card(castle_title, f"{p_castle} 次", rank_str, prev_txt, next_txt, rank=display_rank)

            tab1, tab2, tab3, tab4 = st.tabs(["📈 個人走勢圖", "📋 詳細記錄", "🍩 達成狀況", "⚖️ 升降階紀錄"])

            with tab1:
                chart_type = st.radio("選擇數據類型", ["旗幟戰", "地下水道", "公會城每周"], horizontal=True)
                if chart_type == "旗幟戰": line_color = "#FF6B6B"; y_label = "分數"
                elif chart_type == "地下水道": line_color = "#4D96FF"; y_label = "分數"
                else: line_color = "#6BCB77"; y_label = "完成狀態 (1=有, 0=無)"

                fig_line = px.line(df_filtered, x='周次', y=chart_type, title=f"{final_selected_player} - {chart_type} 趨勢", markers=True)
                fig_line.update_traces(line_color=line_color, line_width=3, marker_size=6, marker_color=line_color, name="實際分數")

                if chart_type == "地下水道" and len(df_filtered) > 1:
                    try:
                        base_date = df_filtered['周次'].min()
                        x_days = (df_filtered['周次'] - base_date).dt.days
                        y_scores = df_filtered[chart_type]
                        
                        slope_daily, intercept = np.polyfit(x_days, y_scores, 1)
                        slope_weekly = slope_daily * 7
                        y_trend = slope_daily * x_days + intercept
                        
                        trend_label = f'📈 趨勢 (週成長: {int(slope_weekly):+,})'
                        
                        fig_line.add_scatter(
                            x=df_filtered['周次'], 
                            y=y_trend, 
                            mode='lines', 
                            name=trend_label,
                            line=dict(color='red', width=2, dash='dash'), 
                            hoverinfo='name+y'
                        )
                    except Exception as e:
                        pass

                avg_score = df_filtered[chart_type].mean()
                if chart_type != "公會城每周" and avg_score > 0:
                    fig_line.add_hline(y=avg_score, line_dash="dot", line_color="gray", annotation_text=f"平均: {int(avg_score):,}", annotation_position="bottom right")

                fig_line.update_layout(
                    xaxis=dict(tickformat="%Y-%m-%d", fixedrange=True),
                    yaxis=dict(title=y_label, fixedrange=True),
                    hovermode="x unified",
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    dragmode=False 
                )
                
                st.plotly_chart(fig_line, use_container_width=True, config=PLOT_CONFIG, height=600)
                if chart_type == "公會城每周": st.caption("ℹ️ 1 代表有完成，0 代表未完成")

            with tab2:
                df_detail_view = df_filtered.sort_values('周次', ascending=False).reset_index(drop=True)
                st.dataframe(
                    df_detail_view[['周次', '旗幟戰', '地下水道', '公會城每周', '本周是否達成']], 
                    use_container_width=True, 
                    hide_index=True,
                    height=800,
                    column_config={
                        "周次": st.column_config.DateColumn("周次", format="YYYY-MM-DD")
                    }
                )

            with tab3:
                st.markdown("### 📊 達成率分析對比")
                col1, col2 = st.columns(2)
                
                with col1:
                    if '本周是否達成' in df_filtered.columns:
                        cnt1 = df_filtered['本周是否達成'].value_counts().reset_index()
                        cnt1.columns = ['狀態', '數量']
                        if not cnt1.empty:
                            fig1 = px.pie(cnt1, values='數量', names='狀態', title='周達成率(單周/不會降階)', 
                                          color='狀態', color_discrete_map={'達成': '#28FF28', '未達成': '#FF2D2D', 'NA': '#636EFA'}, hole=0.6)
                            st.plotly_chart(fig1, use_container_width=True, height=600,)
            
                with col2:
                    if '異動與否' in df_filtered.columns:
                        valid_changes = df_filtered[df_filtered['異動與否'] != 'NA']
                        change_counts = valid_changes['異動與否'].value_counts().reset_index()
                        change_counts.columns = ['狀態', '數量']
                        
                        if not change_counts.empty:
                            color_map = {
                                '升階': '#28FF28', 
                                '降階': '#FF2D2D', 
                                '否': '#0080FF'    
                            }
                            fig_pie_change = px.pie(
                                change_counts, 
                                values='數量', 
                                names='狀態', 
                                title='職位異動統計 (排除首週)', 
                                color='狀態', 
                                color_discrete_map=color_map, 
                                hole=0.6
                            )
                            st.plotly_chart(fig_pie_change, use_container_width=True, config=PLOT_CONFIG, height=600)

            with tab4:
                st.markdown("### ⚖️ 職位異動歷史")
                if '異動與否' in df_filtered.columns:
                    change_log = df_filtered[df_filtered['異動與否'].isin(['升階', '降階'])].copy()
                    
                    if not change_log.empty:
                        change_log = change_log.sort_values('周次', ascending=False)

                        def generate_note(row):
                            notes = []
                            if row['地下水道'] > 0: notes.append(f"地下水道{int(row['地下水道'])}分")
                            if row['旗幟戰'] > 0: notes.append(f"旗幟{int(row['旗幟戰'])}分")
                            if row['公會城每周'] > 0: notes.append("公會城每周達成")
                            if not notes: return "近兩周未有記錄"
                            return " / ".join(notes)
                        
                        change_log['備註'] = change_log.apply(generate_note, axis=1)
                        
                        # 解決衝突：將日期轉成字串，就不需用 column_config
                        change_log['周次'] = change_log['周次'].dt.strftime('%Y-%m-%d')
                        
                        display_df = change_log[['周次', '異動與否', '備註']]
                        display_df.columns = ['日期', '變動類型', '備註']

                        # 重置索引，防止 Styler 崩潰
                        display_df = display_df.reset_index(drop=True)

                        def highlight_rows(row):
                            styles = [''] * len(row)
                            if row['變動類型'] == '升階':
                                return ['background-color: #006000; color: #00EC00; font-weight: bold;'] * len(row)
                            elif row['變動類型'] == '降階':
                                return ['background-color: #800000; color: #F08080; font-weight: bold;'] * len(row)
                            return styles

                        styled_df = display_df.style.apply(highlight_rows, axis=1)

                        # 移除 column_config 和 hide_index 避免與 Styler 衝突
                        st.dataframe(
                            styled_df, 
                            use_container_width=True, 
                            height=800
                        )
                    else:
                        st.info("此玩家目前沒有「升階」或「降階」的紀錄。")
                else:
                    st.warning("資料中找不到 '異動與否' 欄位。")
