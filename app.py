import hmac
import os
from pathlib import Path

import streamlit as st

from guild_config import CSV_FILENAME, CUSTOM_CSS
from guild_data import get_period_data, load_data
from guild_ui import (
    render_home_page,
    render_leaderboard_page,
    render_player_page,
    render_raw_data_page,
)


st.set_page_config(
    page_title="公會每週統計",
    page_icon="🍁",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        "About": "公會每週統計 · Weekly Guild Records",
    },
)

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / CSV_FILENAME


def get_app_passwords():
    """從 Streamlit Secrets 或環境變數讀取網站密碼。"""
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
    """
    使用 form 驗證密碼。

    form 內輸入文字時不會因為離開欄位就反覆 rerun；只有按「登入」
    或在輸入框按 Enter 才會送出，手機操作會比一般 text_input 穩定。
    """
    passwords = get_app_passwords()

    if not passwords:
        st.error("尚未設定網站密碼，請在 Streamlit Secrets 設定 APP_PASSWORDS。")
        st.code('APP_PASSWORDS = ["你的密碼1", "你的密碼2"]', language="toml")
        return False

    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False
    if "login_error" not in st.session_state:
        st.session_state.login_error = False

    if st.session_state.password_correct:
        return True

    st.markdown(
        """
        <div class="login-heading">
            <div class="site-kicker">WEEKLY GUILD RECORDS</div>
            <h1>公會每週統計</h1>
            <p>輸入存取密碼後進入資料網站</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    login_row = st.container(horizontal=True, horizontal_alignment="center")
    login_card = login_row.container(border=True, width=420)

    with login_card.form("login_form", border=False):
        password = st.text_input(
            "密碼",
            type="password",
            label_visibility="collapsed",
            placeholder="存取密碼",
        )
        submitted = st.form_submit_button(
            "登入",
            type="primary",
            width="stretch",
        )

    if submitted:
        is_correct = any(
            hmac.compare_digest(password, expected)
            for expected in passwords
        )

        if is_correct:
            st.session_state.password_correct = True
            st.session_state.login_error = False
            st.rerun()

        st.session_state.login_error = True

    if st.session_state.login_error:
        login_card.error("密碼錯誤")

    return False


@st.cache_data(show_spinner=False)
def get_cached_data(csv_path, file_mtime_ns):
    # file_mtime_ns 只用來讓 CSV 更新時 cache 自動失效。
    # 不再使用固定 TTL，避免網站使用中每 10 分鐘又重新讀一次 CSV。
    del file_mtime_ns
    return load_data(csv_path)


def select_week_period(df, *, key_prefix, default="最近 8 週"):
    """只選擇 CSV 中實際存在的週次。每個頁面各自保存自己的區間。"""
    weeks = sorted(df["周次"].dt.date.unique().tolist())
    if not weeks:
        raise ValueError("CSV 中沒有可用的週次。")

    options = ["最新一週", "最近 4 週", "最近 8 週", "最近 12 週", "全部", "自訂"]
    if default not in options:
        default = "最近 8 週"

    period_mode = st.segmented_control(
        "統計期間",
        options,
        default=default,
        selection_mode="single",
        key=f"{key_prefix}_period_mode",
        persist_state="session",
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
        else:
            custom_default = (
                weeks[max(0, len(weeks) - 8)],
                weeks[-1],
            )
            start_date, end_date = st.select_slider(
                "選擇週次範圍",
                options=weeks,
                value=custom_default,
                format_func=lambda value: value.strftime("%Y-%m-%d"),
                key=f"{key_prefix}_custom_week_range",
                persist_state="session",
            )

    selected_week_count = sum(start_date <= week <= end_date for week in weeks)
    st.caption(
        f"{start_date:%Y-%m-%d} ～ {end_date:%Y-%m-%d} · {selected_week_count} 週"
    )
    return start_date, end_date, selected_week_count


def main():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    if not check_password():
        st.stop()

    try:
        file_mtime_ns = CSV_PATH.stat().st_mtime_ns
        with st.spinner("正在載入公會資料…"):
            df, quality = get_cached_data(str(CSV_PATH), file_mtime_ns)
    except Exception as exc:
        st.error(f"讀取資料失敗：{exc}")
        st.stop()

    # 先建立容器，Page 物件會在 closures 真正執行前填入。
    page_refs = {}

    def render_mobile_navigation():
        """
        Streamlit 的 top navigation 位在 app header；某些手機內嵌瀏覽器會把
        header 隱藏，因此另外提供只在窄螢幕顯示的四等分頁內導覽。
        """
        with st.container(key="mobile_nav"):
            nav_cols = st.columns(4, gap="small")
            nav_items = [
                ("home", "首頁"),
                ("player", "玩家"),
                ("ranking", "排行"),
                ("archive", "資料"),
            ]
            for column, (page_key, label) in zip(nav_cols, nav_items):
                with column:
                    st.page_link(
                        page_refs[page_key],
                        label=label,
                        width="stretch",
                    )

    def home_page():
        render_mobile_navigation()
        render_home_page(df, quality)

    def player_page():
        render_mobile_navigation()
        st.markdown(
            """
            <div class="page-heading">
                <div class="site-kicker">PLAYER PROFILE</div>
                <h1>玩家資料</h1>
                <p>查詢個人週次紀錄、趨勢、達成狀況與職位異動。</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        start_date, end_date, selected_week_count = select_week_period(
            df,
            key_prefix="player",
            default="最近 8 週",
        )
        df_period = get_period_data(df, start_date, end_date)
        render_player_page(
            df,
            df_period,
            start_date,
            end_date,
            selected_week_count,
        )

    def leaderboard_page():
        render_mobile_navigation()
        st.markdown(
            """
            <div class="page-heading">
                <div class="site-kicker">GUILD RANKING</div>
                <h1>公會排行</h1>
                <p>依週次區間查看旗幟戰、地下水道與公會城表現。</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        start_date, end_date, selected_week_count = select_week_period(
            df,
            key_prefix="leaderboard",
            default="最近 8 週",
        )
        df_period = get_period_data(df, start_date, end_date)
        render_leaderboard_page(
            df_period,
            start_date,
            end_date,
            selected_week_count,
        )

    def raw_data_page():
        render_mobile_navigation()
        st.markdown(
            """
            <div class="page-heading">
                <div class="site-kicker">DATA ARCHIVE</div>
                <h1>資料查詢</h1>
                <p>搜尋歷史週次、玩家、職業、分數與達成狀態。</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        start_date, end_date, _ = select_week_period(
            df,
            key_prefix="raw",
            default="最近 4 週",
        )
        df_period = get_period_data(df, start_date, end_date)
        render_raw_data_page(df_period, quality)

    home_ref = st.Page(
        home_page,
        title="首頁",
        icon=":material/home:",
        default=True,
    )
    player_ref = st.Page(
        player_page,
        title="玩家資料",
        icon=":material/person_search:",
        url_path="player",
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
        player=player_ref,
        ranking=ranking_ref,
        archive=archive_ref,
    )

    navigation = st.navigation(
        [home_ref, player_ref, ranking_ref, archive_ref],
        position="top",
    )
    navigation.run()


if __name__ == "__main__":
    main()
