from html import escape

import numpy as np
import plotly.express as px
import streamlit as st

from guild_config import JOB_HIERARCHY, PLOT_CONFIG
from guild_data import build_guild_stats, get_latest_profile


# ============================================================
# 4. UI 共用元件
# ============================================================
def get_rank_icon(rank):
    return {1: "🥇 ", 2: "🥈 ", 3: "🥉 "}.get(int(rank), "")


def get_img_tag(url, width=150):
    if url is None:
        return ""
    url_text = str(url).strip()
    if not url_text or url_text.lower() == "nan":
        return ""
    safe_url = escape(url_text, quote=True)
    return (
        f'<img src="{safe_url}" style="width:{width}px;height:auto;border-radius:8px;'
        'object-fit:contain;margin:5px 0;box-shadow:0 2px 4px rgba(0,0,0,0.3);">'
    )


def draw_leaderboard(data, col_name, color_scale, label_name, is_attendance=False):
    if data.empty:
        st.info("此日期區間沒有資料。")
        return

    sorted_df = data.sort_values(by=col_name, ascending=False).reset_index()
    sorted_df["名次"] = sorted_df[col_name].rank(ascending=False, method="min").astype(int)

    base_style = "text-align:center;box-shadow:0 4px 6px rgba(0,0,0,0.3);height:100%;"

    style_1st = f"""
        <div style="{base_style} padding:12px;border-radius:15px;border:3px solid #FFD700;
                    background:linear-gradient(135deg,#262730 0%,#3a3200 100%);
                    box-shadow:0 0 20px rgba(255,215,0,0.4);">
            <div style="font-size:2.5rem;line-height:1;margin-bottom:5px;">{{icon}}</div>
            {{img_tag}}
            <div style="font-size:1.6rem;font-weight:bold;color:#FFF;margin:5px 0 2px;">{{name}}</div>
            <div style="font-size:1.1rem;color:#BBB;">{{score_label}}</div>
            <div style="font-size:2.2rem;font-weight:bold;color:{{color}};">{{score}}</div>
        </div>
    """

    style_2nd3rd = f"""
        <div style="{base_style} padding:10px;border-radius:12px;background-color:#262730;
                    border:2px solid {{border_color}};">
            <div style="font-size:2.8rem;line-height:1;margin-bottom:5px;">{{icon}}</div>
            {{img_tag}}
            <div style="font-size:1.3rem;font-weight:bold;color:#EEE;margin:5px 0 2px;">{{name}}</div>
            <div style="font-size:1rem;color:#BBB;">{{score_label}}</div>
            <div style="font-size:1.8rem;font-weight:bold;color:{{color}};">{{score}}</div>
        </div>
    """

    style_4th5th = f"""
        <div style="{base_style} padding:8px;border-radius:10px;background-color:#20212b;border:1px solid #444;">
            <div style="font-size:2.2rem;line-height:1;margin-bottom:5px;">{{icon}}</div>
            {{img_tag}}
            <div style="font-size:1.2rem;font-weight:bold;color:#DDD;margin:5px 0 2px;">{{name}}</div>
            <div style="font-size:0.9rem;color:#BBB;">{{score_label}}</div>
            <div style="font-size:1.6rem;font-weight:bold;color:{{color}};">{{score}}</div>
        </div>
    """

    podium_positions = [
        (3, 0, "4️⃣", style_4th5th, "#4D96FF", None, 110, 6),
        (1, 1, "🥈", style_2nd3rd, "#C0C0C0", "#C0C0C0", 130, 3),
        (0, 2, "🥇", style_1st, "#FFD700", None, 150, 0),
        (2, 3, "🥉", style_2nd3rd, "#CD7F32", "#CD7F32", 130, 3),
        (4, 4, "5️⃣", style_4th5th, "#4D96FF", None, 110, 6),
    ]

    cols = st.columns([0.9, 1.1, 1.3, 1.1, 0.9])
    score_label = "參與次數" if is_attendance else "分數"

    for row_idx, col_idx, icon, template, color, border_color, image_width, spacer in podium_positions:
        if len(sorted_df) <= row_idx:
            continue

        p = sorted_df.iloc[row_idx]
        with cols[col_idx]:
            for _ in range(spacer):
                st.write("")

            values = {
                "icon": icon,
                "img_tag": get_img_tag(p.get("圖片"), width=image_width),
                "name": escape(str(p["暱稱"])),
                "score_label": score_label,
                "score": f"{int(p[col_name]):,}",
                "color": color,
                "border_color": border_color or color,
            }
            st.markdown(template.format(**values), unsafe_allow_html=True)

    st.markdown("---")

    top15_df = sorted_df.head(15).copy()
    fig = px.bar(
        top15_df,
        x=col_name,
        y="暱稱",
        orientation="h",
        text=col_name,
        title=f"🏆 {label_name} Top 15",
        color=col_name,
        color_continuous_scale=color_scale,
    )
    fig.update_layout(
        yaxis={"categoryorder": "total ascending", "fixedrange": True},
        xaxis={"fixedrange": True},
        dragmode=False,
    )
    fig.update_traces(texttemplate="%{text:,}", textposition="outside")
    st.plotly_chart(fig, use_container_width=True, config=PLOT_CONFIG)

    st.markdown("#### 📋 完整名單")
    display_df = sorted_df[["名次", "暱稱", "職業", "周次", col_name]].copy()
    max_value = max(int(sorted_df[col_name].max()), 1)
    val_format = "%d 次" if is_attendance else "%d"

    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            col_name: st.column_config.ProgressColumn(
                label_name,
                format=val_format,
                min_value=0,
                max_value=max_value,
            ),
            "名次": st.column_config.NumberColumn(format="No. %d"),
        },
    )


def get_detailed_neighbors(guild_stats, target_player, metric, mode="avg"):
    if target_player not in guild_stats.index:
        return "—", "—"

    rank_col_map = {
        "旗幟戰": "flag_rank",
        "地下水道": "water_rank",
        "公會城每周": "castle_rank",
    }
    rank_col = rank_col_map[metric]

    sorted_stats = guild_stats.sort_values([metric, "周次"], ascending=[False, False]).reset_index()
    matches = sorted_stats.index[sorted_stats["暱稱"] == target_player].tolist()
    if not matches:
        return "—", "—"

    my_idx = matches[0]
    my_score = sorted_stats.loc[my_idx, metric]

    def format_row(row):
        score = int(row[metric])
        weeks = int(row["周次"])
        real_rank = int(row[rank_col])
        neighbor_name = escape(str(row["暱稱"]))
        tie_text = " (同分)" if score == int(my_score) else ""

        if mode == "avg":
            avg_val = int(score / weeks) if weeks else 0
            return (
                f"第 {real_rank} 名{tie_text} {neighbor_name}："
                f"{score:,} (均 {avg_val:,})"
            )

        pct_val = round(score / weeks * 100, 2) if weeks else 0
        return (
            f"第 {real_rank} 名{tie_text} {neighbor_name}："
            f"{score} ({pct_val}%)"
        )

    prev_str = "👑 目前第一" if my_idx == 0 else "⬆️ " + format_row(sorted_stats.iloc[my_idx - 1])
    next_str = (
        "🛡️ 目前墊底"
        if my_idx == len(sorted_stats) - 1
        else "⬇️ " + format_row(sorted_stats.iloc[my_idx + 1])
    )
    return prev_str, next_str


def draw_stat_card(title, score_str, rank_str, prev_txt, next_txt, rank=999):
    base_style = (
        "box-sizing:border-box;border-radius:10px;padding:15px;height:100%;"
        "display:flex;flex-direction:column;justify-content:space-between;flex-grow:1;"
    )

    card_styles = {
        1: (
            "border:3px solid #FFD700;background:linear-gradient(135deg,#262730 0%,#3a3200 100%);"
            "box-shadow:0 0 55px rgba(255,215,0,0.4);color:white;",
            "#FFD700",
        ),
        2: (
            "border:3px solid #C0C0C0;background:linear-gradient(135deg,#262730 0%,#383838 100%);"
            "box-shadow:0 0 55px rgba(192,192,192,0.4);color:white;",
            "#E0E0E0",
        ),
        3: (
            "border:3px solid #CD7F32;background:linear-gradient(135deg,#262730 0%,#3a2500 100%);"
            "box-shadow:0 0 55px rgba(205,127,50,0.4);color:white;",
            "#CD7F32",
        ),
    }

    extra_style, score_color = card_styles.get(
        int(rank),
        ("border:3px solid #444;background-color:#262730;box-shadow:0 1px 3px rgba(0,0,0,0.12);color:white;", "#FF9F1C"),
    )
    container_style = base_style + extra_style

    st.markdown(
        f"""
        <div style="{container_style}">
            <div>
                <div style="font-weight:bold;font-size:1.5rem;margin-bottom:5px;">{title}</div>
                <div style="font-size:2.5rem;font-weight:bold;color:{score_color};line-height:1.2;">{score_str}</div>
                <div style="font-size:1.5rem;margin-bottom:5px;">{rank_str}</div>
            </div>
            <div>
                <hr style="margin:10px 0;border-color:#555;">
                <div style="font-size:0.9rem;color:#CCC;margin-bottom:3px;">{prev_txt}</div>
                <div style="font-size:0.9rem;color:#CCC;">{next_txt}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# 5. 各功能頁面
# ============================================================
def render_leaderboard_page(df_period, start_date, end_date):
    st.markdown("---")
    st.markdown(f"### 📊 公會排行榜 ({start_date} ~ {end_date})")

    leaderboard_df = build_guild_stats(df_period).reset_index()

    tab_flag, tab_water, tab_castle = st.tabs(
        ["🚩 旗幟戰排行", "💧 地下水道排行", "🏰 公會城參與排行"]
    )

    with tab_flag:
        draw_leaderboard(leaderboard_df, "旗幟戰", "Reds", "旗幟戰分數")

    with tab_water:
        draw_leaderboard(leaderboard_df, "地下水道", "Blues", "地下水道分數")

    with tab_castle:
        draw_leaderboard(
            leaderboard_df,
            "公會城每周",
            "Greens",
            "公會城參與數",
            is_attendance=True,
        )
        st.caption("ℹ️ 這裡是依「完成總次數」排序，不是完成率排序。")


def render_raw_data_page(df_period):
    st.markdown("---")
    st.markdown("### 📂 原始資料庫搜尋")

    search_query = st.text_input(
        "🔍 請輸入關鍵字 (搜尋暱稱、職業、分數、達成狀態...)",
        placeholder="例如：陰陽師、1000、達成...",
    ).strip()

    if search_query:
        mask = df_period["_search_text"].str.contains(
            search_query.lower(),
            regex=False,
            na=False,
        )
        df_display = df_period.loc[mask].copy()
        st.success(f"🔍 搜尋結果：共找到 {len(df_display)} 筆資料")
    else:
        df_display = df_period.copy()
        st.info(f"💡 顯示目前日期區間內的所有資料，共 {len(df_display)} 筆")

    df_display = df_display.sort_values("周次", ascending=False).reset_index(drop=True)

    target_cols = [
        "周次", "暱稱", "職業", "旗幟戰", "地下水道", "公會城每周",
        "本周是否達成", "近兩周是否達成", "異動與否",
    ]
    cols_to_show = [col for col in target_cols if col in df_display.columns]

    st.dataframe(
        df_display[cols_to_show],
        use_container_width=True,
        hide_index=True,
        height=800,
        column_config={
            "周次": st.column_config.DateColumn("周次", format="YYYY-MM-DD"),
        },
    )


def render_player_selector(df, search_mode):
    selected_player = None

    with st.container(border=True):
        if search_mode == "個人查詢 (層級篩選)":
            st.caption("依序選擇：職業群 > 分類 > 職業 > 玩家")
            col_group, col_cat, col_job, col_player = st.columns(4)

            with col_group:
                groups = JOB_HIERARCHY["group"].unique().tolist()
                selected_group = st.selectbox(
                    "1️⃣ 職業群",
                    groups,
                    index=None,
                    placeholder="請選擇...",
                )

            with col_cat:
                if selected_group:
                    categories = (
                        JOB_HIERARCHY.loc[JOB_HIERARCHY["group"] == selected_group, "category"]
                        .unique()
                        .tolist()
                    )
                    selected_category = st.selectbox(
                        "2️⃣ 分類",
                        categories,
                        index=None,
                        placeholder="請選擇...",
                    )
                else:
                    selected_category = None
                    st.selectbox("2️⃣ 分類", [], disabled=True, placeholder="請先選職業群")

            with col_job:
                if selected_group and selected_category:
                    jobs = (
                        JOB_HIERARCHY.loc[
                            (JOB_HIERARCHY["group"] == selected_group)
                            & (JOB_HIERARCHY["category"] == selected_category),
                            "job",
                        ]
                        .unique()
                        .tolist()
                    )
                    selected_job = st.selectbox(
                        "3️⃣ 職業",
                        jobs,
                        index=None,
                        placeholder="請選擇...",
                    )
                else:
                    selected_job = None
                    st.selectbox("3️⃣ 職業", [], disabled=True, placeholder="請先選分類")

            with col_player:
                if selected_job:
                    players = sorted(df.loc[df["職業"] == selected_job, "暱稱"].unique().tolist())
                    if players:
                        selected_player = st.selectbox(
                            "4️⃣ 玩家 ID",
                            players,
                            index=None,
                            placeholder="請選擇玩家...",
                        )
                    else:
                        st.warning("此職業目前沒有資料")
                else:
                    st.selectbox("4️⃣ 玩家 ID", [], disabled=True, placeholder="請先選職業")

        else:
            st.caption("直接輸入關鍵字搜尋玩家 ID")
            col_label, col_search = st.columns([1, 3])

            with col_label:
                st.markdown("**🔎 搜尋玩家**")

            with col_search:
                all_players = sorted(df["暱稱"].unique().tolist())
                selected_player = st.selectbox(
                    "請輸入或選擇玩家 ID：",
                    all_players,
                    index=None,
                    placeholder="輸入玩家 ID...",
                )

    return selected_player


def render_player_page(df, df_period, search_mode, start_date, end_date):
    player = render_player_selector(df, search_mode)

    if not player:
        st.markdown("---")
        st.info("👋 請在上方選擇一位玩家以查看詳細數據。")
        return

    player_period = df_period.loc[df_period["暱稱"] == player].copy()
    if player_period.empty:
        st.warning(f"玩家 {player} 在此日期區間內無資料。")
        return

    player_history = df.loc[df["暱稱"] == player].copy()
    display_level, img_url, job_display = get_latest_profile(player_history)

    st.markdown(f"## 👤 {player} 的個人數據報告")

    with st.container(border=True):
        col_profile_img, col_profile_info = st.columns([1.5, 3.5])

        with col_profile_img:
            if img_url:
                st.image(img_url, width=130)
            else:
                st.markdown("# 👤")

        with col_profile_info:
            st.markdown(
                f"""#### 📜 角色詳細資料
* **職業：** {job_display}
* **等級：** {display_level}
* **資料來源：** CSV 歷史資料（會自動往前找最新有效圖片與等級）
"""
            )

    st.markdown("---")

    guild_stats = build_guild_stats(df_period)
    if player not in guild_stats.index:
        st.warning("此玩家在目前日期區間沒有可用的排名資料。")
        return

    my_stats = guild_stats.loc[player]
    p_flag = int(my_stats["旗幟戰"])
    p_water = int(my_stats["地下水道"])
    p_castle = int(my_stats["公會城每周"])
    my_weeks = int(my_stats["周次"])

    rank_flag = int(my_stats["flag_rank"])
    rank_water = int(my_stats["water_rank"])
    rank_castle = int(my_stats["castle_rank"])

    avg_flag = int(p_flag / my_weeks) if my_weeks else 0
    avg_water = int(p_water / my_weeks) if my_weeks else 0
    castle_pct = round(p_castle / my_weeks * 100, 2) if my_weeks else 0

    st.markdown("### 🏆 區間戰績與排名情報")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        left_style = (
            "box-sizing:border-box;border-radius:10px;padding:15px;height:100%;display:flex;"
            "flex-direction:column;justify-content:space-between;flex-grow:1;border:3px solid #444;"
            "background-color:#262730;box-shadow:0 1px 3px rgba(0,0,0,0.12);color:white;"
        )
        st.markdown(
            f"""
            <div style="{left_style}">
                <div>
                    <div style="font-weight:bold;font-size:1.5rem;margin-bottom:5px;">📊 統計週數</div>
                    <div style="font-size:2.5rem;font-weight:bold;color:#FF9F1C;line-height:1.2;">{my_weeks} 週</div>
                    <div style="font-size:1.5rem;margin-bottom:5px;">📅 區間累計</div>
                </div>
                <div>
                    <hr style="margin:10px 0;border-color:#555;">
                    <div style="font-size:0.9rem;color:#CCC;margin-bottom:3px;">📅 開始：{start_date}</div>
                    <div style="font-size:0.9rem;color:#CCC;">📅 結束：{end_date}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        prev_txt, next_txt = get_detailed_neighbors(guild_stats, player, "旗幟戰", mode="avg")
        rank_str = (
            f"{get_rank_icon(rank_flag)}第 {rank_flag} 名 "
            f"<span style='font-size:1.0rem;color:#BBB'>(均 {avg_flag:,})</span>"
        )
        draw_stat_card("🚩 旗幟戰", f"{p_flag:,} 分", rank_str, prev_txt, next_txt, rank_flag)

    with col3:
        prev_txt, next_txt = get_detailed_neighbors(guild_stats, player, "地下水道", mode="avg")
        rank_str = (
            f"{get_rank_icon(rank_water)}第 {rank_water} 名 "
            f"<span style='font-size:1.0rem;color:#BBB'>(均 {avg_water:,})</span>"
        )
        draw_stat_card("💧 地下水道", f"{p_water:,} 分", rank_str, prev_txt, next_txt, rank_water)

    with col4:
        castle_title = "👑 公會城 (全勤)" if castle_pct == 100 else "🏰 公會城"
        prev_txt, next_txt = get_detailed_neighbors(guild_stats, player, "公會城每周", mode="pct")

        if castle_pct == 100:
            rank_str = (
                "👑 <span class='rainbow-text'>完美全勤!!</span> "
                f"<span style='font-size:1.0rem;color:#BBB'>({castle_pct}%)</span>"
            )
            display_rank = 1
        else:
            rank_str = (
                f"{get_rank_icon(rank_castle)}第 {rank_castle} 名 "
                f"<span style='font-size:1.0rem;color:#BBB'>({castle_pct}%)</span>"
            )
            display_rank = rank_castle

        draw_stat_card(
            castle_title,
            f"{p_castle} 次",
            rank_str,
            prev_txt,
            next_txt,
            display_rank,
        )

    tab1, tab2, tab3, tab4 = st.tabs(
        ["📈 個人走勢圖", "📋 詳細記錄", "🍩 達成狀況", "⚖️ 升降階紀錄"]
    )

    with tab1:
        render_player_trend(player_period, player)

    with tab2:
        render_player_detail(player_period)

    with tab3:
        render_player_completion(player_period)

    with tab4:
        render_player_changes(player_period)


def render_player_trend(player_period, player):
    chart_type = st.radio(
        "選擇數據類型",
        ["旗幟戰", "地下水道", "公會城每周"],
        horizontal=True,
    )

    settings = {
        "旗幟戰": ("#FF6B6B", "分數"),
        "地下水道": ("#4D96FF", "分數"),
        "公會城每周": ("#6BCB77", "完成狀態 (1=有, 0=無)"),
    }
    line_color, y_label = settings[chart_type]

    chart_df = player_period.sort_values("周次").copy()

    fig_line = px.line(
        chart_df,
        x="周次",
        y=chart_type,
        title=f"{player} - {chart_type} 趨勢",
        markers=True,
    )
    fig_line.update_traces(
        line_color=line_color,
        line_width=3,
        marker_size=6,
        marker_color=line_color,
        name="實際分數",
    )

    if chart_type == "地下水道" and len(chart_df) > 1:
        base_date = chart_df["周次"].min()
        x_days = (chart_df["周次"] - base_date).dt.days.astype(float)
        y_scores = chart_df[chart_type].astype(float)

        if x_days.nunique() > 1:
            slope_daily, intercept = np.polyfit(x_days, y_scores, 1)
            slope_weekly = slope_daily * 7
            y_trend = slope_daily * x_days + intercept

            fig_line.add_scatter(
                x=chart_df["周次"],
                y=y_trend,
                mode="lines",
                name=f"📈 趨勢 (週成長: {int(slope_weekly):+,})",
                line=dict(color="red", width=2, dash="dash"),
                hoverinfo="name+y",
            )

    avg_score = chart_df[chart_type].mean()
    if chart_type != "公會城每周" and avg_score > 0:
        fig_line.add_hline(
            y=avg_score,
            line_dash="dot",
            line_color="gray",
            annotation_text=f"平均: {int(avg_score):,}",
            annotation_position="bottom right",
        )

    fig_line.update_layout(
        xaxis=dict(tickformat="%Y-%m-%d", fixedrange=True),
        yaxis=dict(title=y_label, fixedrange=True),
        hovermode="x unified",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        dragmode=False,
        height=600,
    )

    st.plotly_chart(fig_line, use_container_width=True, config=PLOT_CONFIG)

    if chart_type == "公會城每周":
        st.caption("ℹ️ 1 代表有完成，0 代表未完成")


def render_player_detail(player_period):
    df_detail = player_period.sort_values("周次", ascending=False).reset_index(drop=True)

    st.dataframe(
        df_detail[["周次", "旗幟戰", "地下水道", "公會城每周", "本周是否達成"]],
        use_container_width=True,
        hide_index=True,
        height=800,
        column_config={
            "周次": st.column_config.DateColumn("周次", format="YYYY-MM-DD"),
        },
    )


def render_player_completion(player_period):
    st.markdown("### 📊 達成率分析對比")
    col1, col2 = st.columns(2)

    with col1:
        cnt = (
            player_period["本周是否達成"]
            .value_counts()
            .rename_axis("狀態")
            .reset_index(name="數量")
        )

        if not cnt.empty:
            fig = px.pie(
                cnt,
                values="數量",
                names="狀態",
                title="周達成率 (單周/不會降階)",
                color="狀態",
                color_discrete_map={
                    "達成": "#28FF28",
                    "未達成": "#FF2D2D",
                    "NA": "#636EFA",
                },
                hole=0.6,
            )
            fig.update_layout(height=600)
            st.plotly_chart(fig, use_container_width=True, config=PLOT_CONFIG)

    with col2:
        valid_changes = player_period.loc[player_period["異動與否"] != "NA"]
        change_counts = (
            valid_changes["異動與否"]
            .value_counts()
            .rename_axis("狀態")
            .reset_index(name="數量")
        )

        if not change_counts.empty:
            fig = px.pie(
                change_counts,
                values="數量",
                names="狀態",
                title="職位異動統計 (排除首週)",
                color="狀態",
                color_discrete_map={
                    "升階": "#28FF28",
                    "降階": "#FF2D2D",
                    "否": "#0080FF",
                },
                hole=0.6,
            )
            fig.update_layout(height=600)
            st.plotly_chart(fig, use_container_width=True, config=PLOT_CONFIG)


def render_player_changes(player_period):
    st.markdown("### ⚖️ 職位異動歷史")

    change_log = player_period.loc[
        player_period["異動與否"].isin(["升階", "降階"])
    ].copy()

    if change_log.empty:
        st.info("此玩家目前沒有「升階」或「降階」的紀錄。")
        return

    change_log = change_log.sort_values("周次", ascending=False)

    def generate_note(row):
        notes = []
        if row["地下水道"] > 0:
            notes.append(f"地下水道{int(row['地下水道'])}分")
        if row["旗幟戰"] > 0:
            notes.append(f"旗幟{int(row['旗幟戰'])}分")
        if row["公會城每周"] > 0:
            notes.append("公會城每周達成")
        return " / ".join(notes) if notes else "近兩周未有記錄"

    change_log["備註"] = change_log.apply(generate_note, axis=1)
    change_log["周次"] = change_log["周次"].dt.strftime("%Y-%m-%d")

    display_df = change_log[["周次", "異動與否", "備註"]].copy()
    display_df.columns = ["日期", "變動類型", "備註"]
    display_df = display_df.reset_index(drop=True)

    def highlight_rows(row):
        if row["變動類型"] == "升階":
            return ["background-color:#006000;color:#00EC00;font-weight:bold;"] * len(row)
        if row["變動類型"] == "降階":
            return ["background-color:#800000;color:#F08080;font-weight:bold;"] * len(row)
        return [""] * len(row)

    styled_df = display_df.style.apply(highlight_rows, axis=1)
    st.dataframe(styled_df, use_container_width=True, height=800)


