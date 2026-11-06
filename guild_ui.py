import hashlib
import html
import re
from datetime import timedelta

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from guild_config import PLOT_CONFIG
from guild_data import build_guild_stats, build_visual_profiles, get_latest_profile


CHART_CONFIG = {**PLOT_CONFIG, "displayModeBar": False, "scrollZoom": False, "responsive": True}
CHART_COLORS = {
    "旗幟戰": "#E0B979",
    "地下水道": "#6EAEDF",
    "公會城每周": "#76BE96",
}


def _style_plot(fig, *, height, mobile=False, left_margin=44, bottom_margin=30):
    """All Plotly figures share readable, non-interactive axes and a dark palette."""
    fig.update_layout(
        height=height,
        autosize=True,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Noto Sans TC, Microsoft JhengHei, sans-serif", color="#D7E0EB", size=11 if mobile else 12),
        margin=dict(l=left_margin, r=12, t=12, b=bottom_margin),
        hoverlabel=dict(bgcolor="#263240", bordercolor="#64788A", font=dict(color="#FFFFFF", size=12)),
        dragmode=False,
        showlegend=False,
    )
    fig.update_xaxes(showline=False, showgrid=False, zeroline=False, fixedrange=True,
                     tickfont=dict(color="#BEC8D5"), automargin=True)
    fig.update_yaxes(showline=False, showgrid=True, gridcolor="#34404D", zeroline=False,
                     fixedrange=True, tickfont=dict(color="#BEC8D5"), automargin=True)
    return fig


def _compact_chart_ticks(weeks, max_ticks, *, mobile=False):
    """Only simplify *labels*, never the underlying plotted data."""
    if not len(weeks):
        return [], []
    indices = sorted(set(np.linspace(0, len(weeks) - 1, num=min(max_ticks, len(weeks)), dtype=int)))
    selected = pd.to_datetime(pd.Series(weeks).iloc[indices])
    fmt = "%m/%d" if len(weeks) < 26 else "%Y/%m"
    return selected.tolist(), selected.dt.strftime(fmt).tolist()


def _short_chart_label(value, maximum=8):
    name = str(value)
    return name if len(name) <= maximum else name[:maximum - 1] + "…"


# 共用元件
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
    st.html(f'<div class="name-chip-wrap">{chips}</div>')



def render_section_title(title, subtitle=None, *, variant=None):
    subtitle_html = (
        f'<span>{html.escape(str(subtitle))}</span>' if subtitle else ''
    )
    extra_class = f' {html.escape(str(variant))}' if variant else ''
    kicker_html = ''
    st.html(
        f"""<div class="section-heading{extra_class}">
            <div class="section-heading-line"></div>
            <div>
                {kicker_html}
                <div class="section-heading-title">{html.escape(str(title))}</div>
                {subtitle_html}
            </div>
        </div>""",
    )


def render_stat_grid(cards):
    """輸出統計摘要卡片。日期區間採獨立欄位排版。"""
    content = []
    for css_class, label, value, meta in cards:
        value_html = html.escape(str(value))
        if css_class == "range" and " ～ " in str(value):
            start_date, end_date = str(value).split(" ～ ", maxsplit=1)
            value_html = (
                '<span class="stat-period">'
                f'<time>{html.escape(start_date)}</time>'
                '<span class="stat-period-divider">—</span>'
                f'<time>{html.escape(end_date)}</time>'
                '</span>'
            )

        content.append(
            f'<div class="stat-card {html.escape(str(css_class))}">'
            f'<div class="stat-label">{html.escape(str(label))}</div>'
            f'<div class="stat-value">{value_html}</div>'
            + (f'<div class="stat-meta">{html.escape(str(meta))}</div>' if meta else '')
            + '</div>'
        )
    st.html('<div class="stat-grid">' + ''.join(content) + '</div>')


# 首頁
def _build_weekly_water_growth(df, previous_week, latest_week):
    """計算地下水道分數增量與成長倍率前三名。

    僅比較連續兩個有效週次均有紀錄、前期分數大於零且本期成長的玩家。
    """
    previous_df = (
        df.loc[df["周次"] == previous_week, ["暱稱", "地下水道"]]
        .rename(columns={"地下水道": "上週分數"})
    )
    latest_df = (
        df.loc[df["周次"] == latest_week, ["暱稱", "職業", "地下水道"]]
        .rename(columns={"地下水道": "本週分數"})
    )

    comparison = previous_df.merge(latest_df, on="暱稱", how="inner")
    if comparison.empty:
        return None, None

    comparison["分數增加"] = comparison["本週分數"] - comparison["上週分數"]

    diff_top3 = None
    diff_candidates = comparison.loc[
        (comparison["上週分數"] > 0)
        & (comparison["本週分數"] > comparison["上週分數"])
    ].copy()
    if not diff_candidates.empty:
        diff_candidates["名次"] = diff_candidates["分數增加"].rank(
            ascending=False, method="min"
        ).astype(int)
        diff_top3 = (
            diff_candidates.sort_values(
                ["分數增加", "本週分數", "暱稱"],
                ascending=[False, False, True],
            )
            .head(3)
            .copy()
        )

    ratio_top3 = None
    ratio_candidates = comparison.loc[
        (comparison["上週分數"] > 0)
        & (comparison["本週分數"] > comparison["上週分數"])
    ].copy()
    if not ratio_candidates.empty:
        ratio_candidates["成長倍率"] = (
            ratio_candidates["本週分數"] / ratio_candidates["上週分數"]
        )
        ratio_candidates["名次"] = ratio_candidates["成長倍率"].rank(
            ascending=False, method="min"
        ).astype(int)
        ratio_top3 = (
            ratio_candidates.sort_values(
                ["成長倍率", "分數增加", "本週分數", "暱稱"],
                ascending=[False, False, False, True],
            )
            .head(3)
            .copy()
        )

    return diff_top3, ratio_top3


def _build_focus_image_lookup(df, *frames):
    """建立首頁焦點玩家的圖片索引。"""
    names = set()
    for frame in frames:
        if frame is None or frame.empty or "暱稱" not in frame.columns:
            continue
        names.update(frame["暱稱"].dropna().astype(str).tolist())

    lookup = {}
    for player in names:
        history = df.loc[df["暱稱"] == player]
        if history.empty:
            continue
        _, img_url, _ = get_latest_profile(history)
        if img_url:
            lookup[player] = str(img_url).strip()
    return lookup


def _safe_image_tag(player, image_lookup, css_class):
    if not image_lookup:
        return "", ""
    raw_url = str(image_lookup.get(player, "") or "").strip()
    if not raw_url.lower().startswith(("https://", "http://")):
        return "", ""
    safe_url = html.escape(raw_url, quote=True)
    safe_alt = html.escape(player, quote=True)
    return (
        " has-character",
        f"""<div class="focus-character {css_class}">
                <img src="{safe_url}" alt="{safe_alt}" loading="lazy">
            </div>""",
    )


def _render_focus_cards(rows, card_type, image_lookup=None):
    """繪製首頁前三名資料卡片。"""
    if rows is None or rows.empty:
        st.html(
            '<div class="focus-empty-card">本週沒有符合條件的成長紀錄。</div>',
            )
        return

    cards = []
    for _, row in rows.head(3).iterrows():
        rank = int(row.get("名次", 0))
        player_raw = str(row["暱稱"])
        player = html.escape(player_raw)
        job = html.escape(str(row.get("職業", "") or ""))

        if card_type == "water":
            value = f'{int(row["地下水道"]):,}<small> 分</small>'
            meta = "本週地下水道"
            css_class = "water"
            image_class, image_html = _safe_image_tag(
                player_raw, image_lookup, css_class
            )
        elif card_type == "growth":
            value = f'+{int(row["分數增加"]):,}<small> 分</small>'
            meta = f'{int(row["上週分數"]):,} → {int(row["本週分數"]):,}'
            css_class = "growth"
            image_class, image_html = _safe_image_tag(
                player_raw, image_lookup, css_class
            )
        else:
            ratio = float(row["成長倍率"])
            percent_gain = (ratio - 1) * 100
            value = f'{ratio:.2f}<small> 倍</small>'
            meta = (
                f'{int(row["上週分數"]):,} → {int(row["本週分數"]):,}'
                f' · +{percent_gain:.1f}%'
            )
            css_class = "ratio"
            image_class, image_html = _safe_image_tag(
                player_raw, image_lookup, css_class
            )

        cards.append(
            f"""<div class="focus-rank-card {css_class} rank-{rank}{image_class}">
                <div class="focus-rank-card-top">
                    <span class="focus-rank-badge">第 {rank} 名</span>
                </div>
                <div class="focus-rank-card-name">{player}</div>
                <div class="focus-rank-card-job">{job}</div>
                <div class="focus-rank-card-value">{value}</div>
                <div class="focus-rank-card-meta">{html.escape(meta)}</div>
                {image_html}
            </div>"""
        )

    st.html(
        '<div class="focus-card-grid">' + ''.join(cards) + '</div>',
    )


def render_home_page(df, quality):
    latest_week = df["周次"].max()
    latest_df = df.loc[df["周次"] == latest_week].copy()

    latest_players = int(latest_df["暱稱"].nunique())
    flag_participants = int((latest_df["旗幟戰"] > 0).sum())
    castle_participants = int((latest_df["公會城每周"] > 0).sum())
    week_end = latest_week + timedelta(days=6)

    water_top3 = latest_df.sort_values(
        ["地下水道", "暱稱"], ascending=[False, True]
    ).head(3).copy()
    if not water_top3.empty:
        water_top3["名次"] = latest_df["地下水道"].rank(
            ascending=False, method="min"
        ).loc[water_top3.index].astype(int)

    promotion_count = int((latest_df["異動與否"] == "升階").sum())
    demotion_count = int((latest_df["異動與否"] == "降階").sum())

    weeks = sorted(df["周次"].dropna().unique().tolist())
    previous_week = weeks[-2] if len(weeks) >= 2 else None
    diff_top3 = ratio_top3 = None
    if previous_week is not None:
        diff_top3, ratio_top3 = _build_weekly_water_growth(
            df, previous_week, latest_week
        )

    focus_image_lookup = _build_focus_image_lookup(
        df, water_top3, diff_top3, ratio_top3
    )

    st.html(
        f'''
        <div class="site-hero">
            <h1>本週概況</h1>
            <p>{latest_week:%Y-%m-%d} ～ {week_end:%Y-%m-%d}</p>
        </div>
        ''',
    )

    render_stat_grid([
        ("neutral", "記錄玩家", f"{latest_players} 人", ""),
        ("accent", "旗幟戰參與", f"{flag_participants} 人", ""),
        ("neutral", "公會城參與", f"{castle_participants} 人", ""),
    ])

    # 本週焦點先呈現職位異動，再依序顯示最高分與成長排行榜。
    render_section_title("本週焦點", variant="focus-main")

    st.html(
        f'''<div class="focus-change-card">
            <div>
                <div class="focus-change-label">本週職位異動</div>
            </div>
            <div class="change-counts">
                <div><span class="change-up">{promotion_count}</span><small>人升階</small></div>
                <div><span class="change-down">{demotion_count}</span><small>人降階</small></div>
            </div>
        </div>''',
    )

    st.html(
        '''<div class="focus-subheading">
            <strong>地下水道 TOP 3</strong>
        </div>''',
    )
    _render_focus_cards(water_top3, "water", focus_image_lookup)

    if previous_week is not None:
        st.html(
            '''<div class="focus-subheading growth-heading">
                <strong>分數增加 TOP 3</strong>
            </div>''',
            )
        _render_focus_cards(diff_top3, "growth", focus_image_lookup)

        st.html(
            '''<div class="focus-subheading ratio-heading">
                <strong>比例增加 TOP 3</strong>
            </div>''',
            )
        _render_focus_cards(ratio_top3, "ratio", focus_image_lookup)

        with st.expander("成長計算方式", expanded=False):
            st.caption("比較上週與本週，僅計算兩週都有紀錄、上週分數大於 0 且分數成長的玩家。")

# 排行榜
def _ranking_avatar(url, player):
    """產生角色圖片 HTML，無有效網址時使用佔位符號。"""
    image = str(url or "").strip()
    safe_player = html.escape(str(player), quote=True)
    fallback = '<span class="guild-avatar-fallback" aria-hidden="true">✦</span>'
    if not image.lower().startswith(("https://", "http://")):
        return f'<div class="guild-rank-avatar is-empty">{fallback}</div>'
    safe_url = html.escape(image, quote=True)
    return (
        '<div class="guild-rank-avatar">'
        + fallback
        + f'<img src="{safe_url}" alt="{safe_player} 的角色外觀" loading="lazy">'
        + '</div>'
    )


def _highlight_rank_name(value, search):
    """標出名稱中符合搜尋的片段，所有玩家文字皆以 HTML 安全輸出。"""
    name = str(value)
    if not search:
        return html.escape(name)
    match = re.search(re.escape(search), name, flags=re.IGNORECASE)
    if match is None:
        return html.escape(name)
    return (
        html.escape(name[:match.start()])
        + '<mark class="guild-rank-match">'
        + html.escape(name[match.start():match.end()])
        + '</mark>'
        + html.escape(name[match.end():])
    )


def _make_visual_rank_rows(data, metric, selected_week_count, search=""):
    """產生排行榜名單的 HTML。"""
    rows = []
    water = metric == "地下水道"
    for _, player in data.iterrows():
        outside_period = bool(player.get("_outside_period", False))
        rank = "—" if outside_period else str(int(player["名次"]))
        name = _highlight_rank_name(player["暱稱"], search)
        job = html.escape(str(player.get("最新職業") or player.get("職業") or "未知"))
        level = player.get("等級")
        level_text = f'Lv. {int(level)}' if level is not None and not np.isnan(level) and level > 0 else '等級未記錄'
        avatar = _ranking_avatar(player.get("角色圖片", ""), player["暱稱"])
        score = int(player[metric])
        if outside_period:
            main_value, unit, note = "—", "", "本期間無紀錄"
        elif water:
            weeks = int(player["周次"])
            average = round(score / weeks) if weeks else 0
            main_value = f'{score:,}'
            unit = '分'
            note = f'週均 {average:,} · {weeks} 週紀錄'
        else:
            main_value = f'{score:,}'
            unit = '分' if metric == '旗幟戰' else '次'
            rate = float(player["區間達成率"])
            note = f'週次參與率 {rate:.1f}% · {int(player["周次"])} / {selected_week_count} 週紀錄'
        rank_class = f' is-top-{rank}' if not outside_period and int(rank) in (1, 2, 3) else ''
        if outside_period:
            rank_class += ' is-outside-period'
        rows.append(
            f'<article class="guild-rank-row{rank_class}">'
            f'<div class="guild-rank-position"><span>{rank}</span></div>'
            f'{avatar}'
            f'<div class="guild-rank-identity"><strong>{name}</strong>'
            f'<div class="guild-rank-detail">{job}<span class="guild-mid-dot">·</span>{level_text}</div></div>'
            f'<div class="guild-rank-score"><strong>{main_value}<span>{unit}</span></strong>'
            f'<small>{html.escape(note)}</small></div>'
            '</article>'
        )
    return '<div class="guild-rank-list">' + ''.join(rows) + '</div>'


def build_historical_search_rows(period_df, all_profiles):
    """建立僅供 ID 搜尋的歷史玩家；不參與當期名次與統計。"""
    missing = all_profiles.loc[
        ~all_profiles["暱稱"].isin(period_df["暱稱"])
    ].copy()
    missing = missing.rename(columns={"圖片": "角色圖片"})
    missing["職業"] = missing["最新職業"]
    missing["周次"] = 0
    missing["名次"] = np.nan
    missing["旗幟戰"] = 0
    missing["地下水道"] = 0
    missing["公會城每周"] = 0
    missing["區間達成率"] = 0.0
    missing["_outside_period"] = True
    return missing.sort_values("暱稱", kind="stable").reset_index(drop=True)


# 僅存儲使用者自己的捲動座標，不含密碼、暱稱或歷史資料。
# 寫入發生在原生「查看詳細」按鈕送出之前；返回時才做一次性還原。
_RANKING_SCROLL_TRACKER = """<script>
(() => {
  if (window.__weeklyRankScrollTracker) return;
  window.__weeklyRankScrollTracker = true;
  document.addEventListener('click', (event) => {
    const button = event.target.closest && event.target.closest('button');
    const card = button && button.closest('[class*="st-key-guild_rank_card_"]');
    if (!card) return;
    try {
      const selectors = [
        '[data-testid="stMain"]',
        '[data-testid="stAppViewContainer"]',
        'html', 'body'
      ];
      const offsets = {};
      for (const selector of selectors) {
        const element = document.querySelector(selector);
        if (element) offsets[selector] = element.scrollTop || 0;
      }
      sessionStorage.setItem('weekly_rank_last_scroll', JSON.stringify({
        offsets, windowY: window.scrollY || 0,
        cardClass: Array.from(card.classList).find(cls => cls.startsWith('st-key-guild_rank_card_')) || ''
      }));
    } catch (_err) { /* Browsers with restricted storage use the anchor fallback. */ }
  }, true);
})();
</script>"""


def _ranking_restore_script(card_class):
    """定位回原名單中的那張卡片，優先還原離開時的像素座標。"""
    import json
    js_target = json.dumps(card_class)
    return """<script>
(() => {
  const cardClass = TARGET_CLASS;
  let snapshot = null;
  try {
    const raw = sessionStorage.getItem('weekly_rank_last_scroll');
    if (raw) snapshot = JSON.parse(raw);
    sessionStorage.removeItem('weekly_rank_last_scroll');
  } catch (_err) {}
  let frames = 0;
  function restore() {
    const target = document.getElementsByClassName(cardClass)[0];
    if (!target && ++frames < 90) return requestAnimationFrame(restore);
    if (!target) return;
    // Always make the selected player visible even if the list has changed.
    target.scrollIntoView({block: 'center', behavior: 'instant'});
    if (snapshot && snapshot.cardClass === cardClass) {
      for (const [selector, y] of Object.entries(snapshot.offsets || {})) {
        const el = document.querySelector(selector);
        if (el && Number.isFinite(y)) el.scrollTop = y;
      }
      if (Number.isFinite(snapshot.windowY)) {
        window.scrollTo({top: snapshot.windowY, behavior: 'instant'});
      }
    }
  }
  requestAnimationFrame(restore);
})();
</script>""".replace('TARGET_CLASS', js_target)


@st.fragment
def render_visual_rank_list(
    sorted_df, metric, selected_week_count, on_view_player=None, historical_only_df=None,
):
    """支援即時包含搜尋、分頁和每位玩家的個人詳細資料入口。"""
    prefix = {'地下水道': 'water', '旗幟戰': 'flag', '公會城每周': 'castle'}[metric]
    search_key = f'guild_rank_search_{prefix}'
    page_key = f'guild_rank_page_{prefix}'
    filter_key = f'guild_rank_active_{prefix}'
    if page_key not in st.session_state:
        st.session_state[page_key] = 0

    st.html(_RANKING_SCROLL_TRACKER, unsafe_allow_javascript=True)
    st.html('<div class="guild-list-heading">玩家排行</div>')
    with st.container(key=f'ranking_search_panel_{prefix}'):
        col_search, col_filter = st.columns([3, 1], gap='small', vertical_alignment='bottom')
        with col_search:
            # 保留即時包含搜尋，但不使用搜尋圖示，避免手機端出現白底圖示方塊。
            search = st.text_input(
                '搜尋 ID',
                type='search',
                placeholder='搜尋 ID',
                icon='',
                key=search_key,
                live='300ms',
                persist_state='session',
                on_change=lambda: st.session_state.update({page_key: 0}),
            ).strip()
        with col_filter:
            active_only = st.checkbox(
                '只看有參與',
                value=False,
                key=filter_key,
                persist_state='session',
                on_change=lambda: st.session_state.update({page_key: 0}),
            )

    filtered = sorted_df
    if search:
        # 唯有搜尋時才加入當期沒有紀錄的歷史玩家，且不改動當期排名。
        if historical_only_df is not None and not historical_only_df.empty:
            active_period_rows = sorted_df.assign(_outside_period=False)
            filtered = pd.concat(
                [active_period_rows, historical_only_df], ignore_index=True,
            )
        match = filtered['暱稱'].astype(str).str.contains(
            search, case=False, regex=False, na=False,
        )
        filtered = filtered.loc[match]
    if active_only:
        filtered = filtered.loc[filtered[metric] > 0]

    if filtered.empty:
        st.info('找不到符合的玩家 ID。若勾選「只看有參與」，可先取消勾選。')
        return

    page_size = 20
    page_count = (len(filtered) + page_size - 1) // page_size
    page = min(max(0, int(st.session_state[page_key])), page_count - 1)
    st.session_state[page_key] = page
    first = page * page_size
    current = filtered.iloc[first:first + page_size]

    if search:
        outside_count = int(filtered.get('_outside_period', pd.Series(False, index=filtered.index)).fillna(False).sum())
        missing_note = f' · {outside_count} 位本期間無紀錄' if outside_count else ''
        st.caption(f'找到 {len(filtered)} 位{missing_note} · 第 {page + 1} / {page_count} 頁')
    else:
        st.caption(f'{len(filtered)} 位玩家 · {first + 1}–{first + len(current)} 位')

    # st.html 不能嵌入可觸發 Python 的按鈕，因此逐筆以原生 Streamlit
    # container + button 組合，維持點擊可靠性與行動裝置的操作支援。
    with st.container(key=f'guild_rank_cards_{prefix}'):
        for offset, (_, player) in enumerate(current.iterrows()):
            player_name = str(player['暱稱'])
            stable_id = hashlib.sha1(player_name.encode('utf-8')).hexdigest()[:16]
            with st.container(key=f'guild_rank_card_{prefix}_{stable_id}'):
                profile_col, action_col = st.columns(
                    [8, 1.55], gap='small', vertical_alignment='center',
                )
                with profile_col:
                    st.html(_make_visual_rank_rows(
                        current.iloc[offset:offset + 1], metric, selected_week_count, search,
                    ))
                with action_col:
                    if st.button(
                        '查看詳細',
                        key=f'guild_rank_detail_{prefix}_{stable_id}',
                        icon=':material/arrow_forward:',
                        width='stretch',
                        type='secondary',
                    ):
                        if on_view_player is not None:
                            on_view_player(player_name, bool(player.get('_outside_period', False)))

    # 從詳細頁返回時才執行一次；搜尋、分頁狀態已由 session 保存。
    if st.session_state.get('ranking_scroll_restore_pending'):
        return_target = st.session_state.get('ranking_return_target')
        if isinstance(return_target, dict) and return_target.get('metric') == prefix:
            target_name = return_target.get('player', '')
            target_hash = hashlib.sha1(str(target_name).encode('utf-8')).hexdigest()[:16]
            card_class = f'st-key-guild_rank_card_{prefix}_{target_hash}'
            st.html(_ranking_restore_script(card_class), unsafe_allow_javascript=True)
            st.session_state['ranking_scroll_restore_pending'] = False

    if page_count > 1:
        left, center, right = st.columns([1, 2, 1], vertical_alignment='center')
        with left:
            if st.button('上一頁', key=f'rank_prev_{prefix}', disabled=page == 0, width='stretch'):
                st.session_state[page_key] = page - 1
                st.rerun()
        with center:
            st.markdown(
                f'<div style="text-align:center;color:#A8AEB9;padding:9px">第 {page + 1} / {page_count} 頁</div>',
                unsafe_allow_html=True,
            )
        with right:
            if st.button('下一頁', key=f'rank_next_{prefix}', disabled=page == page_count - 1, width='stretch'):
                st.session_state[page_key] = page + 1
                st.rerun()


def render_capped_metric_summary(data, metric, selected_week_count, on_view_player=None, historical_only_df=None):
    if data.empty:
        st.info('這個週次範圍沒有資料。')
        return

    is_flag = metric == '旗幟戰'
    max_per_week = 1000 if is_flag else 1
    theoretical_max = selected_week_count * max_per_week
    sorted_df = data.sort_values(
        [metric, '周次', '暱稱'], ascending=[False, False, True]
    ).reset_index(drop=True)
    sorted_df['名次'] = sorted_df[metric].rank(ascending=False, method='min').astype(int)
    sorted_df['區間達成率'] = (
        sorted_df[metric] / theoretical_max * 100 if theoretical_max else 0
    )
    sorted_df['區間達成率'] = sorted_df['區間達成率'].clip(0, 100).round(1)

    perfect_count = int((sorted_df[metric] >= theoretical_max).sum())
    active_mask = sorted_df[metric] > 0
    active_count = int(active_mask.sum())
    zero_count = int((~active_mask).sum())
    avg_rate = float(sorted_df.loc[active_mask, '區間達成率'].mean()) if active_count else 0

    render_visual_rank_list(
        sorted_df, metric, selected_week_count,
        on_view_player=on_view_player, historical_only_df=historical_only_df,
    )

    with st.expander('統計與圖表', expanded=False):
        render_stat_grid([
            ('accent', '全週參與玩家', f'{perfect_count} 人', ''),
            ('blue', '參與玩家', f'{active_count} 人', ''),
            ('neutral', '無參與紀錄', f'{zero_count} 人', ''),
            ('green', '平均參與率', f'{avg_rate:.1f}%', ''),
        ])
        active_df = sorted_df.loc[active_mask].copy()
        if not active_df.empty:
            rate = active_df['區間達成率']
            labels = ['100%', '75–99%', '50–74%', '1–49%']
            active_df['達成區間'] = np.select(
                [rate >= 100, rate >= 75, rate >= 50], labels[:-1], default='1–49%'
            )
            distribution = (
                active_df['達成區間'].value_counts().reindex(labels, fill_value=0)
                .rename_axis('達成區間').reset_index(name='玩家數')
            )
            fig = px.bar(
                distribution, x='玩家數', y='達成區間', orientation='h',
                text='玩家數', category_orders={'達成區間': list(reversed(labels))},
                color_discrete_sequence=['#6EAEDF'],
            )
            _style_plot(fig, height=245, left_margin=70, bottom_margin=20)
            largest = max(int(distribution['玩家數'].max()), 1)
            fig.update_layout(bargap=.32)
            fig.update_xaxes(title=None, range=[0, largest * 1.22], dtick=max(1, int(np.ceil(largest / 4))))
            fig.update_yaxes(title=None, showgrid=False)
            fig.update_traces(textposition='outside', cliponaxis=False,
                              hovertemplate='%{y}：%{x:,} 位玩家<extra></extra>')
            st.plotly_chart(fig, width='stretch', theme=None, config=CHART_CONFIG)
        st.dataframe(
            sorted_df[['名次', '暱稱', '職業', '周次', metric, '區間達成率']],
            width='stretch', hide_index=True, height=450,
        )


def draw_water_leaderboard(data, selected_week_count, on_view_player=None, historical_only_df=None):
    if data.empty:
        st.info('這個週次範圍沒有資料。')
        return

    metric = '地下水道'
    sorted_df = data.sort_values(
        [metric, '周次', '暱稱'], ascending=[False, False, True]
    ).reset_index(drop=True)
    sorted_df['名次'] = sorted_df[metric].rank(ascending=False, method='min').astype(int)
    top_score = int(sorted_df.iloc[0][metric])
    top_ties = int((sorted_df[metric] == top_score).sum())

    render_visual_rank_list(
        sorted_df, metric, selected_week_count,
        on_view_player=on_view_player, historical_only_df=historical_only_df,
    )

    with st.expander('統計與圖表', expanded=False):
        render_stat_grid([
            ('accent', '最高累積分數', f'{top_score:,}', f'{top_ties} 人並列第一' if top_ties > 1 else ''),
            ('blue', '參與玩家', f'{int((sorted_df[metric] > 0).sum())} 人', ''),
            ('neutral', '計算區間', f'{selected_week_count} 週', ''),
        ])
        top15_df = sorted_df.head(15).copy()
        # Short tick labels leave room on phones; hovering still reveals the full ID.
        top15_df['簡短暱稱'] = [f'{i + 1:02d}  {_short_chart_label(name, 7)}'
                            for i, name in enumerate(top15_df['暱稱'])]
        fig = px.bar(
            top15_df, x=metric, y='簡短暱稱', orientation='h',
            custom_data=['暱稱'], color_discrete_sequence=['#6EAEDF'],
        )
        _style_plot(fig, height=470, left_margin=100, bottom_margin=26)
        fig.update_yaxes(categoryorder='array', categoryarray=top15_df['簡短暱稱'].iloc[::-1].tolist(),
                         title=None, showgrid=False)
        fig.update_xaxes(title=None, tickformat='~s', range=[0, max(top_score, 1) * 1.29])
        # Rounded, compact on-chart labels; exact scores remain in the tooltip and table.
        fig.update_traces(
            text=[f'{float(value) / 1_000_000:.1f}M' if value >= 1_000_000
                  else f'{value / 1000:.0f}k' if value >= 1000 else f'{value:.0f}'
                  for value in top15_df[metric]],
            textposition='outside', cliponaxis=False,
            textfont=dict(color='#E0E6EE', size=11),
            hovertemplate='%{customdata[0]}<br>累積 %{x:,.0f} 分<extra></extra>',
        )
        st.plotly_chart(fig, width='stretch', theme=None, config=CHART_CONFIG)
        st.dataframe(
            sorted_df[['名次', '暱稱', '職業', '周次', metric]],
            width='stretch', hide_index=True, height=450,
        )


def render_leaderboard_page(
    df_period, start_date, end_date, selected_week_count,
    full_df=None, metric="地下水道", on_view_player=None,
):
    leaderboard_df = build_guild_stats(df_period).reset_index()
    source = full_df if full_df is not None else df_period
    visuals = build_visual_profiles(source)
    leaderboard_df = leaderboard_df.drop(columns=['圖片'], errors='ignore')
    leaderboard_df = leaderboard_df.merge(visuals, on='暱稱', how='left')
    leaderboard_df = leaderboard_df.rename(columns={'圖片': '角色圖片'})
    historical_only_df = build_historical_search_rows(leaderboard_df, visuals)

    if metric == '地下水道':
        draw_water_leaderboard(
            leaderboard_df, selected_week_count, on_view_player, historical_only_df,
        )
    elif metric == '旗幟戰':
        render_capped_metric_summary(
            leaderboard_df, '旗幟戰', selected_week_count, on_view_player, historical_only_df,
        )
    else:
        render_capped_metric_summary(
            leaderboard_df, '公會城每周', selected_week_count, on_view_player, historical_only_df,
        )


# 歷史資料查詢
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


# 玩家資料
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
    info.markdown(f"### {player}")
    info.markdown(f"**{job_display}**　Lv. {display_level}")


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

    render_section_title("區間摘要")

    water_rank = rank_label(guild_stats, player, "地下水道")
    castle_status = "全勤" if castle_pct >= 100 else rank_label(guild_stats, player, "公會城每周")
    flag_status = "全週參與" if flag_pct >= 100 else f"參與率 {flag_pct}%"

    render_stat_grid([
        ("neutral", "記錄週數", f"{my_weeks} / {selected_week_count} 週", "區間內有留下紀錄的週數"),
        ("accent", "旗幟戰", f"{p_flag:,} 分", f"{flag_status} · 區間參與程度"),
        ("blue", "地下水道", f"{p_water:,} 分", f"{water_rank} · 週均 {avg_water:,}"),
        ("green", "公會城", f"{p_castle} / {selected_week_count} 次", f"{castle_status} · {castle_pct}%"),
    ])

    prev_text, next_text = get_detailed_neighbors(
        guild_stats, player, "地下水道", mode="avg"
    )
    st.html(
        f'''        <div class="rank-context">
            <span><strong>地下水道排名位置</strong></span>
            <span>{html.escape(prev_text)}</span>
            <span>{html.escape(next_text)}</span>
        </div>
        ''',
    )


def render_player_details(df, df_period, player, start_date, end_date, selected_week_count):
    """呈現從排行榜選定玩家的完整歷史資訊。"""
    player_period = df_period.loc[df_period["暱稱"] == player].copy()
    if player_period.empty:
        st.warning(f"{player} 在目前週次範圍內沒有資料。")
        return

    player_history = df.loc[df["暱稱"] == player].copy()
    display_level, img_url, job_display = get_latest_profile(player_history)

    render_player_profile(player, display_level, img_url, job_display)

    render_section_title("詳細紀錄")
    detail_view = st.segmented_control(
        "內容",
        ["走勢", "每週記錄", "達成狀況", "升降階"],
        default="走勢",
        selection_mode="single",
        key="player_detail_view",
        label_visibility="collapsed",
        width="stretch",
    ) or "走勢"

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

    if detail_view == "走勢":
        render_player_trend(player_period, player, known_weeks=df_period["周次"])
    elif detail_view == "每週記錄":
        render_player_detail(player_period)
    elif detail_view == "達成狀況":
        render_player_completion(player_period)
    else:
        render_player_changes(player_period)


def _prepare_trend_data(player_period, metric, all_weeks, window):
    """Use real weeks as the X axis, leaving missing player weeks as gaps."""
    weeks = pd.DatetimeIndex(pd.to_datetime(pd.Series(all_weeks).dropna().unique())).sort_values()
    if not len(weeks):
        weeks = pd.DatetimeIndex(player_period["周次"].dropna().unique()).sort_values()
    count = {"近 12 週": 12, "近 52 週": 52}.get(window)
    if count is not None:
        weeks = weeks[-count:]

    actual = (player_period.sort_values("周次")
              .drop_duplicates("周次", keep="last")
              .set_index("周次")[metric].astype(float))
    # Reindex adds NaN (not zero) for weeks with no player record.
    values = actual.reindex(weeks)
    return pd.DataFrame({"周次": weeks, "分數": values.to_numpy()})


def _trend_stats(chart_df, metric):
    recorded = chart_df.dropna(subset=["分數"])
    if recorded.empty:
        return {"count": 0, "latest": None, "average": None, "slope": None, "trend": None}

    scores = recorded["分數"].astype(float)
    stats = {
        "count": len(recorded),
        "latest": (recorded.iloc[-1]["周次"], float(scores.iloc[-1])),
        "average": float(scores.mean()),
        "slope": None,
        "trend": None,
    }
    if metric == "地下水道" and len(recorded) > 1:
        x_days = (recorded["周次"] - recorded["周次"].min()).dt.days.astype(float).to_numpy()
        if len(np.unique(x_days)) > 1:
            slope, intercept = np.polyfit(x_days, scores.to_numpy(), 1)
            stats["slope"] = float(slope * 7.0)
            stats["trend"] = (recorded["周次"], slope * x_days + intercept)
    return stats


def _build_player_trend_figure(chart_df, metric, *, mobile=False, show_average=False, show_trend=False):
    """A pure Plotly builder, independently testable with real history."""
    stats = _trend_stats(chart_df, metric)
    color = CHART_COLORS[metric]
    fig = go.Figure()
    if metric == "公會城每周":
        # Status values are discrete; do not draw a misleading continuous slope.
        colors = ["#76BE96" if val == 1 else "#8694A4" for val in chart_df["分數"]]
        fig.add_trace(go.Scatter(
            x=chart_df["周次"], y=chart_df["分數"], mode="markers",
            marker=dict(symbol="square", size=10 if mobile else 9, color=colors),
            name="完成狀況", connectgaps=False,
            hovertemplate="%{x|%Y-%m-%d}<br>完成狀態：%{customdata}<extra></extra>",
            customdata=["已完成" if v == 1 else "未完成" if pd.notna(v) else "無紀錄"
                        for v in chart_df["分數"]],
        ))
    else:
        fig.add_trace(go.Scatter(
            x=chart_df["周次"], y=chart_df["分數"],
            mode="lines+markers" if stats["count"] <= 20 else "lines",
            line=dict(color=color, width=2.6 if mobile else 2.4, shape="linear"),
            marker=dict(size=5, color=color),
            connectgaps=False,
            name="每週實際分數",
            hovertemplate="%{x|%Y-%m-%d}<br>%{y:,.0f} 分<extra></extra>",
        ))
        if mobile and stats["count"] > 20:
            # Invisible larger hit targets keep individual weeks tappable on phones.
            fig.add_trace(go.Scatter(
                x=chart_df["周次"], y=chart_df["分數"], mode="markers",
                marker=dict(size=13, color="rgba(110,174,223,0.015)"),
                showlegend=False,
                hovertemplate="%{x|%Y-%m-%d}<br>%{y:,.0f} 分<extra></extra>",
            ))
        if stats["latest"] is not None:
            latest_date, latest_score = stats["latest"]
            fig.add_trace(go.Scatter(
                x=[latest_date], y=[latest_score], mode="markers", name="最新紀錄",
                marker=dict(size=9, color=color, line=dict(color="#12161C", width=2)),
                hovertemplate="%{x|%Y-%m-%d}<br>%{y:,.0f} 分<extra></extra>",
            ))
        if show_average and stats["average"] is not None:
            fig.add_hline(y=stats["average"], line=dict(color="#ABB7C5", dash="dot", width=1.5))
        if show_trend and stats["trend"] is not None:
            x, y = stats["trend"]
            fig.add_trace(go.Scatter(
                x=x, y=y, mode="lines", name="線性趨勢",
                line=dict(color="#DCB97F", dash="dash", width=1.6),
                hovertemplate="線性趨勢：%{y:,.0f} 分<extra></extra>",
            ))

    _style_plot(fig, height=306 if mobile else 395, mobile=mobile,
                left_margin=38 if mobile else 52, bottom_margin=24 if mobile else 30)
    tickvals, ticktext = _compact_chart_ticks(chart_df["周次"], 3 if mobile else 6, mobile=mobile)
    fig.update_xaxes(tickmode="array", tickvals=tickvals, ticktext=ticktext,
                     tickangle=0, ticks="", title=None, showgrid=False)
    if metric == "公會城每周":
        fig.update_yaxes(tickmode="array", tickvals=[0, 1], ticktext=["未完成", "已完成"],
                         range=[-0.20, 1.22], title=None, showgrid=True)
    else:
        fig.update_yaxes(tickformat="~s", rangemode="tozero", title=None, nticks=5)
    fig.update_layout(hovermode="closest", hoverdistance=30)
    return fig, stats


def _render_trend_summary(stats, metric, chart_df):
    if not stats["count"]:
        st.info("所選期間沒有這位玩家的紀錄。")
        return
    last_date, last_value = stats["latest"]
    if metric == "公會城每周":
        panels = [
            ("最新紀錄", "已完成" if last_value == 1 else "未完成"),
            ("完成週數", f'{int(chart_df["分數"].eq(1).sum()):,} 週'),
            ("有紀錄", f'{stats["count"]:,} 週'),
        ]
    else:
        third_label = "線性趨勢／週" if metric == "地下水道" and stats["slope"] is not None else "有紀錄"
        third_value = (f'{stats["slope"]:+,.0f}' if third_label == "線性趨勢／週"
                       else f'{stats["count"]:,} 週')
        panels = [
            ("最新分數", f'{last_value:,.0f}'),
            ("區間平均", f'{stats["average"]:,.0f}'),
            (third_label, third_value),
        ]
    content = "".join(
        '<div class="guild-trend-stat">'
        f'<span>{html.escape(label)}</span><strong>{html.escape(value)}</strong>'
        '</div>' for label, value in panels
    )
    st.html('<div class="guild-trend-summary">' + content + '</div>')


def _render_trend_view(player_period, all_weeks, metric, *, mobile):
    viewport = "mobile" if mobile else "desktop"
    with st.container(key=f"player_trend_{viewport}"):
        window = st.segmented_control(
            "顯示期間", ["近 12 週", "近 52 週", "全部紀錄"],
            default="近 52 週" if mobile else "全部紀錄",
            key=f"player_trend_window_{viewport}",
            selection_mode="single", width="stretch",
        ) or ("近 52 週" if mobile else "全部紀錄")
        chart_df = _prepare_trend_data(player_period, metric, all_weeks, window)
        if chart_df.empty:
            st.info("這段期間沒有週次資料。")
            return
        with st.container(key=f"player_trend_options_{viewport}"):
            if metric != "公會城每周":
                left, right = st.columns(2, gap="small")
                with left:
                    show_average = st.toggle("顯示平均線", value=not mobile,
                                             key=f"player_trend_avg_{viewport}")
                with right:
                    show_trend = (st.toggle("顯示趨勢線", value=not mobile,
                                            key=f"player_trend_fit_{viewport}")
                                  if metric == "地下水道" else False)
            else:
                show_average = show_trend = False

        fig, stats = _build_player_trend_figure(
            chart_df, metric, mobile=mobile,
            show_average=show_average, show_trend=show_trend,
        )
        _render_trend_summary(stats, metric, chart_df)
        if not stats["count"]:
            return
        st.caption(f'{chart_df["周次"].iloc[0]:%Y-%m-%d} ～ {chart_df["周次"].iloc[-1]:%Y-%m-%d} · {stats["count"]} 週紀錄')
        st.plotly_chart(fig, width="stretch", theme=None, config=CHART_CONFIG,
                        key=f"player_trend_plot_{viewport}")


def render_player_trend(player_period, player, known_weeks=None):
    chart_type = st.segmented_control(
        "數據項目", ["旗幟戰", "地下水道", "公會城每周"],
        default="旗幟戰", selection_mode="single", key="player_chart_type",
    ) or "旗幟戰"
    if known_weeks is None:
        known_weeks = player_period["周次"]

    # Streamlit doesn't expose viewport width to Python. Both variants are
    # controlled by CSS media queries; mobile sees 52 weeks, desktop sees all.
    _render_trend_view(player_period, known_weeks, chart_type, mobile=False)
    _render_trend_view(player_period, known_weeks, chart_type, mobile=True)


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


def _status_card_markup(title, values, status_colors):
    """Compact responsive alternative to 500px donuts, with all counts visible."""
    counts = values.value_counts(dropna=False)
    total = int(counts.sum())
    if not total:
        return ""
    segments, items = [], []
    ordered = [name for name in status_colors if name in counts.index]
    ordered.extend(str(name) for name in counts.index if name not in status_colors)
    for status in ordered:
        amount = int(counts.get(status, 0))
        if amount == 0:
            continue
        percent = amount * 100 / total
        color = status_colors.get(status, "#A1ACB9")
        safe_label = html.escape(str(status))
        segments.append(
            f'<span style="width:{percent:.6f}%;background:{color}" '
            f'title="{safe_label}：{amount:,} 週"></span>'
        )
        items.append(
            '<div class="guild-status-item">'
            f'<span class="guild-status-name"><i style="background:{color}"></i>{safe_label}</span>'
            f'<strong>{amount:,} 週</strong><small>{percent:.1f}%</small>'
            '</div>'
        )
    return (
        '<section class="guild-status-card">'
        f'<div class="guild-status-title">{html.escape(str(title))}<span>{total:,} 週</span></div>'
        f'<div class="guild-status-track" role="img" aria-label="{html.escape(str(title))}分布">'
        + ''.join(segments) + '</div>'
        + ''.join(items) + '</section>'
    )


def render_player_completion(player_period):
    achieved = _status_card_markup(
        "每週達成狀況", player_period["本周是否達成"],
        {"達成": "#76BE96", "未達成": "#D28181", "NA": "#8694A4"},
    )
    actual_changes = player_period.loc[player_period["異動與否"] != "NA", "異動與否"]
    changes = _status_card_markup(
        "職位異動分布", actual_changes,
        {"升階": "#76BE96", "降階": "#D28181", "否": "#6EAEDF"},
    )
    if achieved or changes:
        st.html('<div class="guild-status-grid">' + achieved + changes + '</div>')
    else:
        st.info("所選期間沒有達成狀況紀錄。")


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
