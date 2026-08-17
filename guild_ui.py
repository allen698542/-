import html

import numpy as np
import plotly.express as px
import streamlit as st

from guild_config import JOB_HIERARCHY, PLOT_CONFIG
from guild_data import build_guild_stats, get_latest_profile


# ============================================================
# 共用小工具
# ============================================================
def rank_text(rank):
    return f"第 {int(rank)} 名"


def rank_label(guild_stats, player, metric):
    rank_col_map = {
        "旗幟戰": "flag_rank",
        "地下水道": "water_rank",
        "公會城每周": "castle_rank",
    }
    if player not in guild_stats.index:
        return "—"

    score = guild_stats.loc[player, metric]
    rank = int(guild_stats.loc[player, rank_col_map[metric]])
    tie_count = int((guild_stats[metric] == score).sum())

    if tie_count > 1:
        return f"並列第 {rank} 名（{tie_count} 人）"
    return f"第 {rank} 名"


def get_detailed_neighbors(guild_stats, target_player, metric, mode="avg"):
    if target_player not in guild_stats.index:
        return "—", "—"

    rank_col_map = {
        "旗幟戰": "flag_rank",
        "地下水道": "water_rank",
        "公會城每周": "castle_rank",
    }
    rank_col = rank_col_map[metric]

    sorted_stats = guild_stats.sort_values(
        [metric, "周次"],
        ascending=[False, False],
    ).reset_index()

    matches = sorted_stats.index[
        sorted_stats["暱稱"] == target_player
    ].tolist()
    if not matches:
        return "—", "—"

    my_idx = matches[0]
    my_score = int(sorted_stats.loc[my_idx, metric])

    def format_row(row):
        score = int(row[metric])
        weeks = int(row["周次"])
        real_rank = int(row[rank_col])
        neighbor_name = str(row["暱稱"])
        tie_text = "（同分）" if score == my_score else ""

        if mode == "avg":
            avg_val = int(score / weeks) if weeks else 0
            return f"{real_rank} · {neighbor_name}{tie_text} · {score:,} / 週均 {avg_val:,}"

        pct_val = round(score / weeks * 100, 2) if weeks else 0
        return f"{real_rank} · {neighbor_name}{tie_text} · {score} / {pct_val}%"

    prev_str = "目前已在最前段" if my_idx == 0 else "前一位：" + format_row(sorted_stats.iloc[my_idx - 1])
    next_str = (
        "目前為最後一位"
        if my_idx == len(sorted_stats) - 1
        else "下一位：" + format_row(sorted_stats.iloc[my_idx + 1])
    )
    return prev_str, next_str


def render_summary_card(parent, title, value, caption, prev_text=None, next_text=None, width=255):
    card = parent.container(border=True, width=width)
    card.metric(title, value)
    card.caption(caption)
    if prev_text:
        card.caption(prev_text)
    if next_text:
        card.caption(next_text)


def render_name_chips(names):
    safe_names = [html.escape(str(name)) for name in names]
    chips = "".join(f'<span class="name-chip">{name}</span>' for name in safe_names)
    st.markdown(f'<div class="name-chip-wrap">{chips}</div>', unsafe_allow_html=True)



def render_section_title(title, subtitle=None):
    subtitle_html = (
        f'<span>{html.escape(str(subtitle))}</span>' if subtitle else ''
    )
    st.markdown(
        f'''        <div class="section-heading">
            <div class="section-heading-line"></div>
            <div>
                <h2>{html.escape(str(title))}</h2>
                {subtitle_html}
            </div>
        </div>
        ''',
        unsafe_allow_html=True,
    )


def render_stat_grid(cards):
    """cards: [(css_class, label, value, meta)]"""
    html_cards = []
    for css_class, label, value, meta in cards:
        html_cards.append(
            f'''            <div class="stat-card {html.escape(css_class)}">
                <div class="stat-label">{html.escape(str(label))}</div>
                <div class="stat-value">{html.escape(str(value))}</div>
                <div class="stat-meta">{html.escape(str(meta))}</div>
            </div>
            '''
        )
    st.markdown(
        '<div class="stat-grid">' + ''.join(html_cards) + '</div>',
        unsafe_allow_html=True,
    )


# ============================================================
# 首頁
# ============================================================
def render_home_page(df, quality):
    latest_week = df["周次"].max()
    latest_df = df.loc[df["周次"] == latest_week].copy()

    latest_players = int(latest_df["暱稱"].nunique())
    flag_perfect = int((latest_df["旗幟戰"] >= 1000).sum())
    castle_done = int((latest_df["公會城每周"] > 0).sum())
    castle_rate = round(castle_done / latest_players * 100, 1) if latest_players else 0

    water_top = latest_df.sort_values("地下水道", ascending=False).iloc[0] if not latest_df.empty else None
    change_count = int(latest_df["異動與否"].isin(["升階", "降階"]).sum())

    st.markdown(
        f"""
        <div class="site-hero">
            <div class="site-kicker">WEEKLY GUILD RECORDS</div>
            <h1>公會每週統計</h1>
            <p>每週戰績、參與紀錄與玩家歷史資料。最新資料更新至 {latest_week:%Y-%m-%d}。</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_stat_grid([
        ("neutral", "最新週次", latest_week.strftime("%Y-%m-%d"), "每週更新一次"),
        ("blue", "本週記錄玩家", f"{latest_players} 人", "目前週次有資料的玩家"),
        ("accent", "旗幟戰滿分", f"{flag_perfect} 人", "本週達到 1,000 分"),
        ("green", "公會城完成率", f"{castle_rate}%", f"{castle_done} 人完成"),
    ])

    render_section_title("本週焦點", "快速查看最新一週的重要紀錄")
    highlights = st.container(horizontal=True, gap="small")

    water_card = highlights.container(border=True, width=510)
    water_card.caption("地下水道最高紀錄")
    if water_top is not None:
        water_card.markdown(f"### {water_top['暱稱']}")
        water_card.metric("本週分數", f"{int(water_top['地下水道']):,}")
        water_card.caption(str(water_top.get("職業", "")))

    change_card = highlights.container(border=True, width=510)
    change_card.caption("本週職位異動")
    change_card.markdown(f"### {change_count} 筆紀錄")
    change_card.write("包含本週的升階與降階紀錄，可至「玩家資料」查看個人歷史。")

    st.markdown(
        '<p class="home-note">使用上方選單切換玩家資料、公會排行與資料查詢。各頁面會記住自己的週次範圍。</p>',
        unsafe_allow_html=True,
    )


# ============================================================
# 排行榜
# ============================================================
def render_top_rank_cards(sorted_df, col_name, label_name):
    if sorted_df.empty:
        return

    render_section_title("前三名", "本區間地下水道最高分玩家")
    cards = st.container(horizontal=True, gap="small")

    top3 = sorted_df.head(3)
    for _, row in top3.iterrows():
        card = cards.container(border=True, width=310)
        rank = int(row["名次"])
        card.caption(rank_text(rank))

        image = str(row.get("圖片", "") or "").strip()
        if image and image.lower() != "nan":
            card.image(image, width=92)

        card.markdown(f"### {row['暱稱']}")
        card.caption(str(row.get("職業", "")))
        card.metric(label_name, f"{int(row[col_name]):,} 分")


def render_capped_metric_summary(data, metric, selected_week_count):
    """旗幟戰、公會城改用達成率概況，避免大量同分的 Top 3 失去意義。"""
    if data.empty:
        st.info("這個週次範圍沒有資料。")
        return

    is_flag = metric == "旗幟戰"
    max_per_week = 1000 if is_flag else 1
    theoretical_max = selected_week_count * max_per_week
    label = "滿分" if is_flag else "全勤"
    unit = "分" if is_flag else "次"

    sorted_df = data.sort_values(
        [metric, "周次"],
        ascending=[False, False],
    ).reset_index(drop=True)
    sorted_df["名次"] = sorted_df[metric].rank(
        ascending=False, method="min"
    ).astype(int)

    sorted_df["區間達成率"] = (
        sorted_df[metric] / theoretical_max * 100
        if theoretical_max else 0
    )
    sorted_df["區間達成率"] = sorted_df["區間達成率"].clip(0, 100).round(1)

    perfect_df = sorted_df.loc[sorted_df[metric] >= theoretical_max].copy()
    perfect_count = len(perfect_df)
    active_mask = sorted_df[metric] > 0
    active_count = int(active_mask.sum())
    zero_count = int((~active_mask).sum())
    avg_rate = (
        float(sorted_df.loc[active_mask, "區間達成率"].mean())
        if active_count else 0
    )

    render_stat_grid([
        ("accent", f"{label}玩家", f"{perfect_count} 人", f"{theoretical_max:,} {unit} / {selected_week_count} 週"),
        ("blue", "有參與玩家", f"{active_count} 人", f"共 {len(sorted_df)} 位玩家有週次紀錄"),
        ("neutral", "0 分 / 未完成", f"{zero_count} 人", "完整名單仍會保留這些玩家"),
        ("green", "參與者平均達成率", f"{avg_rate:.1f}%", "只計算本區間有實際參與的玩家"),
    ])

    if perfect_count:
        render_section_title(f"{label}名單", f"本區間共有 {perfect_count} 位玩家達成 {label}")
        names = perfect_df["暱稱"].tolist()
        render_name_chips(names[:28])
        if len(names) > 28:
            with st.expander(f"查看其餘 {len(names) - 28} 位玩家"):
                render_name_chips(names[28:])

    render_section_title(
        "參與玩家達成率分布",
        f"主圖只分析有實際參與的 {active_count} 位玩家；另外 {zero_count} 位 0 分 / 未完成玩家已在上方單獨列出",
    )

    active_df = sorted_df.loc[active_mask].copy()
    if active_df.empty:
        st.info("本區間沒有可繪製的參與紀錄。")
    else:
        rate = active_df["區間達成率"]
        labels = ["100%", "75–99%", "50–74%", "1–49%"]
        active_df["達成區間"] = np.select(
            [
                rate >= 100,
                rate >= 75,
                rate >= 50,
            ],
            labels[:-1],
            default="1–49%",
        )

        distribution = (
            active_df["達成區間"]
            .value_counts()
            .reindex(labels, fill_value=0)
            .rename_axis("達成區間")
            .reset_index(name="玩家數")
        )

        fig = px.bar(
            distribution,
            x="玩家數",
            y="達成區間",
            orientation="h",
            text="玩家數",
            category_orders={"達成區間": list(reversed(labels))},
        )
        fig.update_layout(
            xaxis={"title": "玩家數", "fixedrange": True, "rangemode": "tozero"},
            yaxis={"title": None, "fixedrange": True},
            margin=dict(l=10, r=30, t=15, b=20),
            height=300,
            dragmode=False,
            bargap=0.3,
        )
        fig.update_traces(textposition="outside", cliponaxis=False)
        st.plotly_chart(fig, width="stretch", config=PLOT_CONFIG)

    render_section_title("完整名單", "可依名次、分數與區間達成率查看所有玩家")
    display_df = sorted_df[["名次", "暱稱", "職業", "周次", metric, "區間達成率"]].copy()
    st.dataframe(
        display_df,
        width="stretch",
        hide_index=True,
        height=540,
        column_config={
            "名次": st.column_config.NumberColumn("名次", format="%d"),
            "周次": st.column_config.NumberColumn("記錄週數", format="%d"),
            metric: st.column_config.NumberColumn(metric, format="%d"),
            "區間達成率": st.column_config.ProgressColumn(
                "區間達成率",
                format="%.1f%%",
                min_value=0,
                max_value=100,
            ),
        },
    )


def draw_water_leaderboard(data):
    if data.empty:
        st.info("這個週次範圍沒有資料。")
        return

    col_name = "地下水道"
    sorted_df = data.sort_values(
        by=[col_name, "周次"],
        ascending=[False, False],
    ).reset_index(drop=True)
    sorted_df["名次"] = sorted_df[col_name].rank(
        ascending=False,
        method="min",
    ).astype(int)

    top_score = sorted_df.iloc[0][col_name]
    top_ties = int((sorted_df[col_name] == top_score).sum())
    if top_ties <= 3:
        render_top_rank_cards(sorted_df, col_name, "地下水道分數")
    else:
        st.markdown(
            f"""
            <div class="ranking-callout">
                <strong>最高分共有 {top_ties} 人並列</strong><br>
                本區間最高分為 {int(top_score):,} 分，因此不另外製造人工破同分規則。
            </div>
            """,
            unsafe_allow_html=True,
        )
        render_name_chips(sorted_df.loc[sorted_df[col_name] == top_score, "暱稱"].tolist())

    render_section_title("Top 15", "依地下水道累積分數排序")
    top15_df = sorted_df.head(15).copy()
    fig = px.bar(
        top15_df,
        x=col_name,
        y="暱稱",
        orientation="h",
        text=col_name,
    )
    fig.update_layout(
        yaxis={"categoryorder": "total ascending", "fixedrange": True, "title": None},
        xaxis={"fixedrange": True, "title": "地下水道分數"},
        margin=dict(l=10, r=20, t=20, b=20),
        height=460,
        dragmode=False,
    )
    fig.update_traces(texttemplate="%{text:,}", textposition="outside")
    st.plotly_chart(fig, width="stretch", config=PLOT_CONFIG)

    st.markdown("### 完整名單")
    display_df = sorted_df[["名次", "暱稱", "職業", "周次", col_name]].copy()
    st.dataframe(
        display_df,
        width="stretch",
        hide_index=True,
        height=540,
        column_config={
            "名次": st.column_config.NumberColumn("名次", format="%d"),
            "周次": st.column_config.NumberColumn("記錄週數", format="%d"),
            col_name: st.column_config.NumberColumn("地下水道分數", format="%d"),
        },
    )


def render_leaderboard_page(df_period, start_date, end_date, selected_week_count):
    leaderboard_df = build_guild_stats(df_period).reset_index()

    metric = st.segmented_control(
        "排行項目",
        ["旗幟戰", "地下水道", "公會城"],
        default="旗幟戰",
        selection_mode="single",
        key="leaderboard_metric",
    ) or "旗幟戰"

    if metric == "旗幟戰":
        render_capped_metric_summary(leaderboard_df, "旗幟戰", selected_week_count)
    elif metric == "地下水道":
        draw_water_leaderboard(leaderboard_df)
    else:
        render_capped_metric_summary(leaderboard_df, "公會城每周", selected_week_count)


# ============================================================
# 原始資料
# ============================================================
def render_raw_data_page(df_period, quality=None):
    search_query = st.text_input(
        "搜尋資料",
        placeholder="輸入玩家 ID、職業、分數或狀態",
    ).strip()

    if search_query:
        mask = df_period["_search_text"].str.contains(
            search_query.lower(),
            regex=False,
            na=False,
        )
        df_display = df_period.loc[mask].copy()
    else:
        df_display = df_period.copy()

    st.caption(f"目前顯示 {len(df_display):,} 筆資料")

    df_display = df_display.sort_values(
        "周次",
        ascending=False,
    ).reset_index(drop=True)

    target_cols = [
        "周次", "暱稱", "職業", "旗幟戰", "地下水道", "公會城每周",
        "本周是否達成", "近兩周是否達成", "異動與否",
    ]
    cols_to_show = [col for col in target_cols if col in df_display.columns]

    st.dataframe(
        df_display[cols_to_show],
        width="stretch",
        hide_index=True,
        height=600,
        column_config={
            "周次": st.column_config.DateColumn("週次", format="YYYY-MM-DD"),
        },
    )

    if quality:
        with st.expander("資料品質（管理用）", expanded=False):
            st.write(
                f"玩家 {quality['players']:,} 位 · 週次 {quality['weeks']:,} 個 · "
                f"最新週次 {quality['latest_week']}"
            )
            st.write(
                f"CSV {quality['raw_rows']:,} 列，清理後 {quality['clean_rows']:,} 列。"
            )
            if quality["duplicate_rows"] > 0:
                st.write(
                    f"偵測到 {quality['duplicate_groups']:,} 組玩家＋週次重複紀錄，"
                    "已自動保留資料較完整的一筆。"
                )
            if quality["invalid_date_rows"] > 0:
                st.write(f"排除 {quality['invalid_date_rows']:,} 筆無效日期。")


# ============================================================
# 玩家頁面
# ============================================================
def render_player_selector(df):
    render_section_title("選擇玩家", "可直接搜尋 ID，或依職業逐步縮小名單")

    mode = st.segmented_control(
        "查詢方式",
        ["直接搜尋", "依職業篩選"],
        default="直接搜尋",
        selection_mode="single",
        key="player_search_mode",
    ) or "直接搜尋"

    if mode == "直接搜尋":
        players = sorted(df["暱稱"].dropna().unique().tolist())
        return st.selectbox(
            "玩家 ID",
            players,
            index=None,
            placeholder="輸入玩家 ID 或展開名單",
            help="輸入部分文字即可搜尋。",
            key="player_direct_select",
        )

    filter_box = st.container(border=True)
    filter_box.caption("依序選擇職業群、分類與職業；最後直接從符合條件的玩家名單中選擇，不需要另外輸入 ID。")

    row = filter_box.container(horizontal=True, gap="small")
    groups = JOB_HIERARCHY["group"].unique().tolist()
    group_box = row.container(width=245)
    selected_group = group_box.selectbox(
        "1. 職業群",
        groups,
        index=None,
        placeholder="選擇職業群",
        key="filter_group",
    )

    selected_category = None
    selected_job = None

    cat_box = row.container(width=245)
    if selected_group:
        categories = (
            JOB_HIERARCHY.loc[
                JOB_HIERARCHY["group"] == selected_group, "category"
            ]
            .unique()
            .tolist()
        )
        selected_category = cat_box.selectbox(
            "2. 分類",
            categories,
            index=None,
            placeholder="選擇分類",
            key="filter_category",
        )
    else:
        cat_box.selectbox(
            "2. 分類", [], disabled=True, placeholder="先選職業群", key="filter_category_disabled"
        )

    job_box = row.container(width=245)
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
        selected_job = job_box.selectbox(
            "3. 職業",
            jobs,
            index=None,
            placeholder="選擇職業",
            key="filter_job",
        )
    else:
        job_box.selectbox(
            "3. 職業", [], disabled=True, placeholder="先選分類", key="filter_job_disabled"
        )

    player_source = df
    if selected_job:
        player_source = df.loc[df["職業"] == selected_job]
    elif selected_group and selected_category:
        valid_jobs = JOB_HIERARCHY.loc[
            (JOB_HIERARCHY["group"] == selected_group)
            & (JOB_HIERARCHY["category"] == selected_category),
            "job",
        ].tolist()
        player_source = df.loc[df["職業"].isin(valid_jobs)]
    elif selected_group:
        valid_jobs = JOB_HIERARCHY.loc[
            JOB_HIERARCHY["group"] == selected_group, "job"
        ].tolist()
        player_source = df.loc[df["職業"].isin(valid_jobs)]

    players = sorted(player_source["暱稱"].dropna().unique().tolist())

    result_box = filter_box.container()
    if not selected_group:
        result_box.info("先選擇職業群後，這裡會顯示符合條件的玩家。")
        return None

    result_box.caption(f"目前符合條件：{len(players)} 位玩家")
    if not players:
        result_box.warning("目前條件下找不到玩家。")
        return None

    if len(players) == 1:
        result_box.success(f"已找到玩家：{players[0]}")
        return players[0]

    # 已選到具體職業且人數不多時，直接把玩家做成可點選按鈕，
    # 比再開一個下拉選單更直覺；人數多時才退回可搜尋下拉選單。
    if selected_job and len(players) <= 18:
        return result_box.pills(
            "4. 選擇玩家",
            players,
            selection_mode="single",
            key="player_filtered_pills",
        )

    return result_box.selectbox(
        "4. 玩家",
        players,
        index=None,
        placeholder=f"從 {len(players)} 位玩家中選擇",
        key="player_filtered_select",
    )


def render_player_profile(player, display_level, img_url, job_display):
    profile = st.container(
        border=True,
        horizontal=True,
        vertical_alignment="center",
        gap="medium",
    )

    if img_url:
        profile.image(img_url, width=120)

    info = profile.container(width=460)
    info.caption("PLAYER PROFILE")
    info.markdown(f"### {player}")
    info.markdown(f"**{job_display}**　Lv. {display_level}")
    info.caption("角色圖片與等級會從完整歷史資料中尋找最新有效紀錄。")


def render_player_summary(
    guild_stats,
    player,
    start_date,
    end_date,
    selected_week_count,
):
    my_stats = guild_stats.loc[player]
    p_flag = int(my_stats["旗幟戰"])
    p_water = int(my_stats["地下水道"])
    p_castle = int(my_stats["公會城每周"])
    my_weeks = int(my_stats["周次"])

    avg_water = int(p_water / my_weeks) if my_weeks else 0
    flag_possible = selected_week_count * 1000
    flag_pct = round(p_flag / flag_possible * 100, 1) if flag_possible else 0
    castle_pct = round(p_castle / selected_week_count * 100, 1) if selected_week_count else 0

    render_section_title("區間摘要", f"{start_date:%Y-%m-%d} ～ {end_date:%Y-%m-%d}")

    water_rank = rank_label(guild_stats, player, "地下水道")
    castle_status = "全勤" if castle_pct >= 100 else rank_label(guild_stats, player, "公會城每周")
    flag_status = "滿分" if flag_pct >= 100 else f"達成率 {flag_pct}%"

    render_stat_grid([
        ("neutral", "記錄週數", f"{my_weeks} / {selected_week_count} 週", "區間內有留下紀錄的週數"),
        ("accent", "旗幟戰", f"{p_flag:,} 分", f"{flag_status} · 理論滿分 {flag_possible:,}"),
        ("blue", "地下水道", f"{p_water:,} 分", f"{water_rank} · 週均 {avg_water:,}"),
        ("green", "公會城", f"{p_castle} / {selected_week_count} 次", f"{castle_status} · {castle_pct}%"),
    ])

    prev_text, next_text = get_detailed_neighbors(
        guild_stats, player, "地下水道", mode="avg"
    )
    st.markdown(
        f'''        <div class="rank-context">
            <span><strong>地下水道排名位置</strong></span>
            <span>{html.escape(prev_text)}</span>
            <span>{html.escape(next_text)}</span>
        </div>
        ''',
        unsafe_allow_html=True,
    )


def render_player_page(df, df_period, start_date, end_date, selected_week_count):
    player = render_player_selector(df)

    if not player:
        st.info("選擇一位玩家後即可查看完整資料。")
        return

    player_period = df_period.loc[df_period["暱稱"] == player].copy()
    if player_period.empty:
        st.warning(f"{player} 在目前週次範圍內沒有資料。")
        return

    player_history = df.loc[df["暱稱"] == player].copy()
    display_level, img_url, job_display = get_latest_profile(player_history)

    st.divider()
    render_player_profile(player, display_level, img_url, job_display)

    guild_stats = build_guild_stats(df_period)
    if player not in guild_stats.index:
        st.warning("此玩家在目前週次範圍內沒有可用的排名資料。")
        return

    render_player_summary(
        guild_stats,
        player,
        start_date,
        end_date,
        selected_week_count,
    )

    render_section_title("詳細資料", "切換查看走勢、每週記錄、達成狀況與升降階")
    detail_view = st.segmented_control(
        "內容",
        ["走勢", "每週記錄", "達成狀況", "升降階"],
        default="走勢",
        selection_mode="single",
        key="player_detail_view",
    ) or "走勢"

    if detail_view == "走勢":
        render_player_trend(player_period, player)
    elif detail_view == "每週記錄":
        render_player_detail(player_period)
    elif detail_view == "達成狀況":
        render_player_completion(player_period)
    else:
        render_player_changes(player_period)


def render_player_trend(player_period, player):
    chart_type = st.segmented_control(
        "數據項目",
        ["旗幟戰", "地下水道", "公會城每周"],
        default="旗幟戰",
        selection_mode="single",
        key="player_chart_type",
    ) or "旗幟戰"

    settings = {
        "旗幟戰": ("#C79A52", "分數"),
        "地下水道": ("#5A8FC4", "分數"),
        "公會城每周": ("#65A57A", "完成狀態 (1=有, 0=無)"),
    }
    line_color, y_label = settings[chart_type]

    chart_df = player_period.sort_values("周次").copy()

    fig_line = px.line(
        chart_df,
        x="周次",
        y=chart_type,
        markers=True,
    )
    fig_line.update_traces(
        line_color=line_color,
        line_width=2.5,
        marker_size=6,
        marker_color=line_color,
        name="實際數據",
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
                name=f"週趨勢 {int(slope_weekly):+,}",
                line=dict(color="#8B8B8B", width=2, dash="dash"),
                hoverinfo="name+y",
            )

    avg_score = chart_df[chart_type].mean()
    if chart_type != "公會城每周" and avg_score > 0:
        fig_line.add_hline(
            y=avg_score,
            line_dash="dot",
            line_color="#9A9A9A",
            annotation_text=f"平均 {int(avg_score):,}",
            annotation_position="bottom right",
        )

    fig_line.update_layout(
        xaxis=dict(tickformat="%Y-%m-%d", fixedrange=True, title=None),
        yaxis=dict(title=y_label, fixedrange=True),
        hovermode="x unified",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        dragmode=False,
        height=460,
        margin=dict(l=10, r=10, t=40, b=20),
    )

    st.plotly_chart(fig_line, width="stretch", config=PLOT_CONFIG)

    if chart_type == "公會城每周":
        st.caption("1 代表有完成，0 代表未完成。")


def render_player_detail(player_period):
    df_detail = player_period.sort_values(
        "周次",
        ascending=False,
    ).reset_index(drop=True)

    st.dataframe(
        df_detail[["周次", "旗幟戰", "地下水道", "公會城每周", "本周是否達成"]],
        width="stretch",
        hide_index=True,
        height=520,
        column_config={
            "周次": st.column_config.DateColumn("週次", format="YYYY-MM-DD"),
        },
    )


def render_player_completion(player_period):
    charts = st.container(horizontal=True, gap="small")

    cnt = (
        player_period["本周是否達成"]
        .value_counts()
        .rename_axis("狀態")
        .reset_index(name="數量")
    )

    if not cnt.empty:
        card = charts.container(border=True, width=500)
        card.markdown("#### 每週達成率")
        fig = px.pie(
            cnt,
            values="數量",
            names="狀態",
            color="狀態",
            color_discrete_map={
                "達成": "#65A57A",
                "未達成": "#C05E5E",
                "NA": "#7A7A7A",
            },
            hole=0.55,
        )
        fig.update_layout(height=360, margin=dict(l=10, r=10, t=20, b=20))
        card.plotly_chart(fig, width="stretch", config=PLOT_CONFIG)

    valid_changes = player_period.loc[player_period["異動與否"] != "NA"]
    change_counts = (
        valid_changes["異動與否"]
        .value_counts()
        .rename_axis("狀態")
        .reset_index(name="數量")
    )

    if not change_counts.empty:
        card = charts.container(border=True, width=500)
        card.markdown("#### 職位異動")
        fig = px.pie(
            change_counts,
            values="數量",
            names="狀態",
            color="狀態",
            color_discrete_map={
                "升階": "#65A57A",
                "降階": "#C05E5E",
                "否": "#5B6F88",
            },
            hole=0.55,
        )
        fig.update_layout(height=360, margin=dict(l=10, r=10, t=20, b=20))
        card.plotly_chart(fig, width="stretch", config=PLOT_CONFIG)


def render_player_changes(player_period):
    change_log = player_period.loc[
        player_period["異動與否"].isin(["升階", "降階"])
    ].copy()

    if change_log.empty:
        st.info("目前沒有升階或降階紀錄。")
        return

    change_log = change_log.sort_values("周次", ascending=False)

    def generate_note(row):
        notes = []
        if row["地下水道"] > 0:
            notes.append(f"地下水道 {int(row['地下水道']):,} 分")
        if row["旗幟戰"] > 0:
            notes.append(f"旗幟戰 {int(row['旗幟戰']):,} 分")
        if row["公會城每周"] > 0:
            notes.append("公會城完成")
        return " / ".join(notes) if notes else "近兩週未有記錄"

    change_log["備註"] = change_log.apply(generate_note, axis=1)

    display_df = change_log[["周次", "異動與否", "備註"]].copy()
    display_df.columns = ["週次", "變動類型", "備註"]
    display_df = display_df.reset_index(drop=True)

    st.dataframe(
        display_df,
        width="stretch",
        hide_index=True,
        height=500,
        column_config={
            "週次": st.column_config.DateColumn("週次", format="YYYY-MM-DD"),
        },
    )
