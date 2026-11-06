import hmac
import os
from pathlib import Path

import streamlit as st

from guild_config import CSV_FILENAME, CUSTOM_CSS
from guild_data import get_period_data, load_data
from guild_ui import (
    render_home_page,
    render_leaderboard_page,
    render_player_details,
    render_raw_data_page,
)


st.set_page_config(
    page_title="每週紀錄",
    page_icon="🍁",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "About": "每週紀錄",
    },
)

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / CSV_FILENAME


def get_app_passwords():
    """讀取 Streamlit Secrets 與環境變數中的存取密碼。"""
    passwords = []

    try:
        raw = st.secrets.get("APP_PASSWORDS", [])
        if isinstance(raw, str):
            passwords.append(raw)
        else:
            passwords.extend(str(value) for value in raw if str(value).strip())

        for key in ("APP_PASSWORD", "APP_PASSWORD_2"):
            value = st.secrets.get(key, "")
            if value:
                passwords.append(str(value))
    except Exception:
        pass

    for key in ("APP_PASSWORD", "APP_PASSWORD_2"):
        value = os.getenv(key)
        if value:
            passwords.append(value)

    return list(
        dict.fromkeys(
            password.strip()
            for password in passwords
            if password and password.strip()
        )
    )


def check_password():
    """密碼表單僅在未通過驗證時顯示；通過後直接切換至載入畫面。"""
    passwords = get_app_passwords()
    if not passwords:
        st.error("尚未設定網站密碼，請在 Streamlit Secrets 設定 APP_PASSWORDS。")
        st.code('APP_PASSWORDS = ["你的密碼1", "你的密碼2"]', language="toml")
        return False

    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    if "login_error" not in st.session_state:
        st.session_state.login_error = False

    # 已驗證的工作階段不再繪製密碼框；資料載入期間也無法再次送出。
    if st.session_state.password_correct:
        return True

    def submit_password():
        # 伺服器端防重入：已通過驗證或正在轉換畫面時忽略重複送出。
        if st.session_state.get("password_correct") or st.session_state.get("login_pending"):
            return
        entered = st.session_state.get("login_password", "")
        valid = any(hmac.compare_digest(entered, expected) for expected in passwords)
        st.session_state.login_error = not valid
        if valid:
            st.session_state.password_correct = True
            st.session_state.login_pending = True
            # 回呼在頁面重繪之前執行；成功後不在 Session State 留存明文密碼。
            st.session_state.pop("login_password", None)

    st.html('<div class="login-heading"><h1>每週紀錄</h1></div>')
    login_row = st.container(horizontal=True, horizontal_alignment="center")
    login_card = login_row.container(border=True, width=420)
    with login_card.form("login_form", border=False):
        st.text_input(
            "輸入密碼",
            type="password",
            label_visibility="collapsed",
            placeholder="輸入密碼",
            key="login_password",
            disabled=st.session_state.get("login_pending", False),
        )
        st.form_submit_button(
            "進入",
            type="primary",
            width="stretch",
            disabled=st.session_state.get("login_pending", False),
            on_click=submit_password,
        )

    if st.session_state.login_error:
        login_card.error("密碼錯誤，請再試一次")
    return False


@st.cache_data(show_spinner=False)
def get_cached_data(csv_path, file_mtime_ns):
    # 檔案修改時間用於快取失效判斷。
    del file_mtime_ns
    return load_data(csv_path)


def select_week_period(
    df, *, key_prefix, default="最近 8 週", show_label=True, show_caption=True, control="tabs"
):
    """依資料中存在的週次解析統計期間。"""
    weeks = sorted(df["周次"].dt.date.unique().tolist())
    if not weeks:
        raise ValueError("CSV 中沒有可用的週次。")

    options = ["最新一週", "最近 4 週", "最近 8 週", "最近 12 週", "全部", "自訂"]
    if default not in options:
        default = "最近 8 週"

    if control == "dropdown":
        period_mode = st.selectbox(
            "統計期間",
            options,
            index=options.index(default),
            key=f"{key_prefix}_period_mode",
            persist_state="session",
            label_visibility="visible" if show_label else "collapsed",
            width="stretch",
        )
    else:
        period_mode = st.segmented_control(
            "統計期間",
            options,
            default=default,
            selection_mode="single",
            key=f"{key_prefix}_period_mode",
            persist_state="session",
            label_visibility="visible" if show_label else "collapsed",
            wrap=True,
        )
    period_mode = period_mode or default

    if period_mode == "最新一週":
        start_date = end_date = weeks[-1]
    elif period_mode == "最近 4 週":
        start_date, end_date = weeks[max(0, len(weeks) - 4)], weeks[-1]
    elif period_mode == "最近 8 週":
        start_date, end_date = weeks[max(0, len(weeks) - 8)], weeks[-1]
    elif period_mode == "最近 12 週":
        start_date, end_date = weeks[max(0, len(weeks) - 12)], weeks[-1]
    elif period_mode == "全部":
        start_date, end_date = weeks[0], weeks[-1]
    else:
        if len(weeks) == 1:
            start_date = end_date = weeks[0]
        elif control == "dropdown":
            # 手機上以起訖日期取代長滑桿，避免在 184 週刻度間反覆拖曳。
            left, right = st.columns(2, gap="small")
            with left:
                start_date = st.selectbox(
                    "起始週",
                    weeks,
                    index=max(0, len(weeks) - 8),
                    format_func=lambda d: d.strftime("%Y-%m-%d"),
                    key=f"{key_prefix}_custom_start",
                    persist_state="session",
                )
            with right:
                end_options = [week for week in weeks if week >= start_date]
                end_date = st.selectbox(
                    "結束週",
                    end_options,
                    index=len(end_options) - 1,
                    format_func=lambda d: d.strftime("%Y-%m-%d"),
                    key=f"{key_prefix}_custom_end",
                    persist_state="session",
                )
        else:
            start_date, end_date = st.select_slider(
                "選擇週次範圍",
                options=weeks,
                value=(weeks[max(0, len(weeks) - 8)], weeks[-1]),
                format_func=lambda value: value.strftime("%Y-%m-%d"),
                key=f"{key_prefix}_custom_week_range",
                persist_state="session",
            )

    selected_week_count = sum(start_date <= week <= end_date for week in weeks)
    if show_caption:
        st.caption(
            f"{start_date:%Y-%m-%d} ～ {end_date:%Y-%m-%d} · {selected_week_count} 週"
        )
    return start_date, end_date, selected_week_count


RANKING_METRIC_KEYS = {
    "地下水道": "water",
    "旗幟戰": "flag",
    "公會城": "castle",
}


def select_leaderboard_filters(df):
    """排行類別為主分頁；每個類別各自保存統計期間。"""
    with st.container(key="leaderboard_filters"):
        metric = st.segmented_control(
            "排行項目",
            list(RANKING_METRIC_KEYS),
            default="地下水道",
            selection_mode="single",
            required=True,
            label_visibility="collapsed",
            key="leaderboard_metric",
            persist_state="session",
            width="stretch",
            wrap=False,
        ) or "地下水道"

        with st.container(key="leaderboard_period_filter"):
            st.html(
                '<div class="guild-period-current">'
                f'<strong>{metric}</strong><span>統計期間</span>'
                '</div>'
            )
            start_date, end_date, count = select_week_period(
                df,
                key_prefix=f"leaderboard_{RANKING_METRIC_KEYS[metric]}",
                default="全部",
                show_label=False,
                show_caption=False,
                control="dropdown",
            )
            st.html(
                '<div class="guild-filter-summary">'
                f'{start_date:%Y-%m-%d} ～ {end_date:%Y-%m-%d}'
                f'<span aria-hidden="true">·</span> {count} 週'
                '</div>'
            )
    return metric, start_date, end_date, count


def main():
    st.html(CUSTOM_CSS)

    if not check_password():
        st.stop()

    # 提交成功後先完成一次快速重繪，讓可互動的密碼表單立即離開畫面，
    # 再開始較耗時的 CSV 載入；避免舊表單停留而被連續點擊、修改。
    if st.session_state.pop("login_pending", False):
        st.html('<div class="guild-loading">正在載入資料…</div>')
        st.rerun()

    try:
        file_mtime_ns = CSV_PATH.stat().st_mtime_ns
        with st.spinner("正在載入公會資料…"):
            df, quality = get_cached_data(str(CSV_PATH), file_mtime_ns)
    except Exception as exc:
        st.error(f"讀取資料失敗：{exc}")
        st.stop()

    # 導覽函式在路由註冊後引用 Page 物件。
    page_refs = {}

    def render_site_navigation(current_page):
        """繪製站內導覽列並切換至指定頁面。"""
        with st.container(key="site_nav"):
            nav_cols = st.columns(3, gap="small")
            nav_items = [
                ("home", "首頁", ":material/home:"),
                ("ranking", "排行", ":material/leaderboard:"),
                ("archive", "資料", ":material/database:"),
            ]
            for column, (page_key, label, icon) in zip(nav_cols, nav_items):
                with column:
                    clicked = st.button(
                        label,
                        key=f"nav_{current_page}_{page_key}",
                        icon=icon,
                        type="primary" if page_key == current_page else "secondary",
                        width="stretch",
                    )
                    if clicked and page_key != current_page:
                        st.switch_page(page_refs[page_key])
        # 導覽列採 fixed，不佔文件高度；保留空間避免遮住頁面標題。
        st.html('<div class="guild-nav-spacer" aria-hidden="true"></div>')

    def home_page():
        render_site_navigation("home")
        render_home_page(df, quality)

    def open_player_details(player_name, ranking_metric, outside_period=False):
        """從排行榜前往玩家詳細資料，並沿用目前的排名統計期間。"""
        metric_key = RANKING_METRIC_KEYS[ranking_metric]
        st.session_state["ranking_return_target"] = {
            "metric": metric_key, "player": player_name,
        }
        period_prefix = f"leaderboard_{metric_key}"
        # 當期沒有紀錄的舊玩家，詳細頁直接顯示完整歷史。
        period_mode = (
            "全部" if outside_period
            else st.session_state.get(f"{period_prefix}_period_mode", "全部")
        )
        st.session_state["profile_period_mode"] = period_mode
        if period_mode == "自訂":
            for part in ("custom_start", "custom_end"):
                key = f"{period_prefix}_{part}"
                if key in st.session_state:
                    st.session_state[f"profile_{part}"] = st.session_state[key]
        st.switch_page(page_refs["profile"], query_params={"player": player_name})

    def profile_page():
        """排名的內部詳細頁，保留原玩家頁的統計及圖表，但不佔用導覽位置。"""
        render_site_navigation("ranking")
        if st.button("返回公會排行", icon=":material/arrow_back:", key="back_to_ranking"):
            st.session_state["ranking_scroll_restore_pending"] = True
            st.switch_page(page_refs["ranking"])

        player = st.query_params.get("player", "")
        known_players = set(df["暱稱"].unique())
        if not player or player not in known_players:
            st.warning("找不到這位玩家的資料，請回到排行榜重新選擇。")
            return

        st.html(
            """
            <div class="page-heading">
                <h1>玩家詳細</h1>
            </div>
            """,
        )
        start_date, end_date, selected_week_count = select_week_period(
            df,
            key_prefix="profile",
            default="全部",
            control="dropdown",
        )
        df_period = get_period_data(df, start_date, end_date)
        render_player_details(
            df, df_period, player, start_date, end_date, selected_week_count,
        )

    def leaderboard_page():
        render_site_navigation("ranking")
        st.html(
            """
            <div class="page-heading">
                <h1>公會排行</h1>
            </div>
            """,
        )
        metric, start_date, end_date, selected_week_count = select_leaderboard_filters(df)
        df_period = get_period_data(df, start_date, end_date)
        render_leaderboard_page(
            df_period,
            start_date,
            end_date,
            selected_week_count,
            full_df=df,
            metric=metric,
            on_view_player=lambda name: open_player_details(name, metric),
        )

    def raw_data_page():
        render_site_navigation("archive")
        st.html(
            """
            <div class="page-heading">
                <h1>資料查詢</h1>
            </div>
            """,
        )
        start_date, end_date, _ = select_week_period(
            df,
            key_prefix="raw",
            default="最近 4 週",
            control="dropdown",
        )
        df_period = get_period_data(df, start_date, end_date)
        render_raw_data_page(df_period, quality)

    home_ref = st.Page(
        home_page,
        title="首頁",
        icon=":material/home:",
        default=True,
    )
    profile_ref = st.Page(
        profile_page,
        title="玩家詳細資料",
        icon=":material/person_search:",
        url_path="profile",
        visibility="hidden",
    )
    ranking_ref = st.Page(
        leaderboard_page,
        title="公會排行",
        icon=":material/leaderboard:",
        url_path="ranking",
    )
    archive_ref = st.Page(
        raw_data_page,
        title="資料查詢",
        icon=":material/database:",
        url_path="archive",
    )

    page_refs.update(
        home=home_ref,
        profile=profile_ref,
        ranking=ranking_ref,
        archive=archive_ref,
    )

    navigation = st.navigation(
        [home_ref, ranking_ref, archive_ref, profile_ref],
        position="hidden",
    )
    navigation.run()


if __name__ == "__main__":
    main()
