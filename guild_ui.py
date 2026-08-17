import numpy as np
import plotly.express as px
import streamlit as st

from guild_config import JOB_HIERARCHY, PLOT_CONFIG
from guild_data import build_guild_stats, get_latest_profile


# ============================================================
# 共用小工具
# ============================================================
def rank_text(rank):
    rank = int(rank)
    if rank == 1:
        return "第 1 名"
    if rank == 2:
        return "第 2 名"
    if rank == 3:
        return "第 3 名"
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

    prev_str = "目前已是第一名" if my_idx == 0 else "前一名：" + format_row(sorted_stats.iloc[my_idx - 1])
    next_str = (
        "目前為最後一名"
        if my_idx == len(sorted_stats) - 1
        else "下一名：" + format_row(sorted_stats.iloc[my_idx + 1])
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


# ============================================================
# 排行榜
# ============================================================
def render_top_rank_cards(sorted_df, col_name, label_name, is_attendance=False):
    if sorted_df.empty:
        return

    st.markdown("#### 前三名")
    cards = st.container(horizontal=True, gap="small")

    top3 = sorted_df.head(3)
    for _, row in top3.iterrows():
        card = cards.container(border=True, width=300)
        rank = int(row["名次"])
        card.caption(rank_text(rank))

        image = str(row.get("圖片", "") or "").strip()
        if image and image.lower() != "nan":
            card.image(image, width=96)

        card.markdown(f"### {row['暱稱']}")
        card.caption(str(row.get("職業", "")))
        suffix = " 次" if is_attendance else " 分"
        card.metric(label_name, f"{int(row[col_name]):,}{suffix}")


def draw_leaderboard(data, col_name, color_scale, label_name, is_attendance=False):
    if data.empty:
        st.info("這個週次範圍沒有資料。")
        return

    sorted_df = data.sort_values(
        by=[col_name, "周次"],
        ascending=[False, False],
    ).reset_index(drop=True)
    sorted_df["名次"] = sorted_df[col_name].rank(
        ascending=False,
        method="min",
    ).astype(int)

    render_top_rank_cards(
        sorted_df,
        col_name,
        label_name,
        is_attendance=is_attendance,
    )

    st.markdown("#### Top 15")
    top15_df = sorted_df.head(15).copy()
    fig = px.bar(
        top15_df,
        x=col_name,
        y="暱稱",
        orientation="h",
        text=col_name,
        color=col_name,
        color_continuous_scale=color_scale,
    )
    fig.update_layout(
        yaxis={"categoryorder": "total ascending", "fixedrange": True, "title": None},
        xaxis={"fixedrange": True, "title": label_name},
        coloraxis_showscale=False,
        margin=dict(l=10, r=20, t=20, b=20),
        height=460,
        dragmode=False,
    )
    fig.update_traces(texttemplate="%{text:,}", textposition="outside")
    st.plotly_chart(fig, width="stretch", config=PLOT_CONFIG)

    st.markdown("#### 完整名單")
    display_df = sorted_df[["名次", "暱稱", "職業", "周次", col_name]].copy()
    max_value = max(int(sorted_df[col_name].max()), 1)
    val_format = "%d 次" if is_attendance else "%d"

    st.dataframe(
        display_df,
        width="stretch",
        hide_index=True,
        height=520,
        column_config={
            col_name: st.column_config.ProgressColumn(
                label_name,
                format=val_format,
                min_value=0,
                max_value=max_value,
            ),
            "名次": st.column_config.NumberColumn("名次", format="%d"),
            "周次": st.column_config.NumberColumn("統計週數", format="%d"),
        },
    )


def render_leaderboard_page(df_period, start_date, end_date):
    st.header("公會排行")
    st.caption(f"{start_date:%Y-%m-%d} ～ {end_date:%Y-%m-%d}")

    leaderboard_df = build_guild_stats(df_period).reset_index()

    metric = st.pills(
        "排行項目",
        ["旗幟戰", "地下水道", "公會城"],
        default="旗幟戰",
        required=True,
        width="stretch",
        key="leaderboard_metric",
    )

    if metric == "旗幟戰":
        draw_leaderboard(
            leaderboard_df,
            "旗幟戰",
            "Reds",
            "旗幟戰分數",
        )
    elif metric == "地下水道":
        draw_leaderboard(
            leaderboard_df,
            "地下水道",
            "Blues",
            "地下水道分數",
        )
    else:
        draw_leaderboard(
            leaderboard_df,
            "公會城每周",
            "Greens",
            "公會城參與數",
            is_attendance=True,
        )
        st.caption("公會城目前依完成總次數排序，不是依完成率排序。")


# ============================================================
# 原始資料
# ============================================================
def render_raw_data_page(df_period):
    st.header("原始資料")
    st.caption("可搜尋玩家、職業、分數與達成狀態。")

    search_query = st.text_input(
        "搜尋",
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

    st.caption(f"顯示 {len(df_display):,} 筆資料")

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
        height=560,
        column_config={
            "周次": st.column_config.DateColumn("週次", format="YYYY-MM-DD"),
        },
    )


# ============================================================
# 玩家頁面
# ============================================================
def render_player_selector(df):
    st.subheader("玩家查詢")

    selected_group = None
    selected_category = None
    selected_job = None

    with st.expander("篩選條件（選填）", expanded=False):
        groups = JOB_HIERARCHY["group"].unique().tolist()
        selected_group = st.selectbox(
            "職業群",
            groups,
            index=None,
            placeholder="全部職業群",
        )

        if selected_group:
            categories = (
                JOB_HIERARCHY.loc[
                    JOB_HIERARCHY["group"] == selected_group,
                    "category",
                ]
                .unique()
                .tolist()
            )
            selected_category = st.selectbox(
                "分類",
                categories,
                index=None,
                placeholder="全部分類",
            )

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
                "職業",
                jobs,
                index=None,
                placeholder="全部職業",
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
            JOB_HIERARCHY["group"] == selected_group,
            "job",
        ].tolist()
        player_source = df.loc[df["職業"].isin(valid_jobs)]

    players = sorted(player_source["暱稱"].dropna().unique().tolist())
    return st.selectbox(
        "玩家",
        players,
        index=None,
        placeholder="輸入或選擇玩家 ID",
        help="可直接輸入玩家 ID 搜尋；上方篩選條件不是必填。",
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

    info = profile.container(width=420)
    info.markdown(f"### {player}")
    info.markdown(f"**{job_display}**　Lv. {display_level}")
    info.caption("角色圖片與等級會從完整歷史資料中尋找最新有效紀錄。")


def render_player_summary(
    guild_stats,
    player,
    start_date,
    end_date,
):
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

    st.subheader("區間摘要")
    cards = st.container(horizontal=True, gap="small")

    render_summary_card(
        cards,
        "統計週數",
        f"{my_weeks} 週",
        f"{start_date:%Y-%m-%d} ～ {end_date:%Y-%m-%d}",
    )

    prev_text, next_text = get_detailed_neighbors(
        guild_stats,
        player,
        "旗幟戰",
        mode="avg",
    )
    render_summary_card(
        cards,
        "旗幟戰",
        f"{p_flag:,} 分",
        f"{rank_text(rank_flag)} · 週均 {avg_flag:,}",
        prev_text,
        next_text,
    )

    prev_text, next_text = get_detailed_neighbors(
        guild_stats,
        player,
        "地下水道",
        mode="avg",
    )
    render_summary_card(
        cards,
        "地下水道",
        f"{p_water:,} 分",
        f"{rank_text(rank_water)} · 週均 {avg_water:,}",
        prev_text,
        next_text,
    )

    prev_text, next_text = get_detailed_neighbors(
        guild_stats,
        player,
        "公會城每周",
        mode="pct",
    )
    attendance_text = "全勤" if castle_pct == 100 else rank_text(rank_castle)
    render_summary_card(
        cards,
        "公會城",
        f"{p_castle} 次",
        f"{attendance_text} · {castle_pct}%",
        prev_text,
        next_text,
    )


def render_player_page(df, df_period, start_date, end_date):
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
    )

    st.subheader("詳細資料")
    detail_view = st.pills(
        "內容",
        ["走勢", "每週記錄", "達成狀況", "升降階"],
        default="走勢",
        required=True,
        width="stretch",
        key="player_detail_view",
    )

    if detail_view == "走勢":
        render_player_trend(player_period, player)
    elif detail_view == "每週記錄":
        render_player_detail(player_period)
    elif detail_view == "達成狀況":
        render_player_completion(player_period)
    else:
        render_player_changes(player_period)


def render_player_trend(player_period, player):
    chart_type = st.pills(
        "數據項目",
        ["旗幟戰", "地下水道", "公會城每周"],
        default="旗幟戰",
        required=True,
        width="stretch",
        key="player_chart_type",
    )

    settings = {
        "旗幟戰": ("#C94A4A", "分數"),
        "地下水道": ("#3D6D9C", "分數"),
        "公會城每周": ("#4F7C5E", "完成狀態 (1=有, 0=無)"),
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
                "達成": "#4F7C5E",
                "未達成": "#B85C5C",
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
                "升階": "#4F7C5E",
                "降階": "#B85C5C",
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
