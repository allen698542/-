import hmac
import os
from pathlib import Path

import streamlit as st

from guild_config import CSV_FILENAME, CUSTOM_CSS
from guild_data import get_period_data, load_data
from guild_ui import (
    render_leaderboard_page,
    render_player_page,
    render_raw_data_page,
)


st.set_page_config(
    page_title="公會每週統計",
    page_icon="🍁",
    layout="wide",
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
    passwords = get_app_passwords()

    if not passwords:
        st.error("尚未設定網站密碼，請在 Streamlit Secrets 設定 APP_PASSWORDS。")
        st.code('APP_PASSWORDS = ["你的密碼1", "你的密碼2"]', language="toml")
        return False

    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if st.session_state.password_correct:
        return True

    login_row = st.container(horizontal=True, horizontal_alignment="center")
    login_card = login_row.container(border=True, width=420)
    login_card.markdown("### 公會統計登入")
    login_card.caption("請輸入存取密碼")

    password = login_card.text_input(
        "密碼",
        type="password",
        label_visibility="collapsed",
        placeholder="密碼",
    )

    if password:
        is_correct = any(
            hmac.compare_digest(password, expected)
            for expected in passwords
        )

        if is_correct:
            st.session_state.password_correct = True
            st.rerun()
        else:
            login_card.error("密碼錯誤")

    return False


@st.cache_data(ttl=600, show_spinner=False)
def get_cached_data(csv_path, file_mtime_ns):
    # file_mtime_ns 只用來讓 CSV 更新時 cache 自動失效。
    del file_mtime_ns
    return load_data(csv_path)


def render_data_status(quality):
    with st.sidebar.expander("資料狀態", expanded=False):
        st.caption(
            f"{quality['players']:,} 位玩家 · "
            f"{quality['weeks']:,} 個週次"
        )
        st.caption(f"最新週次：{quality['latest_week']}")
        st.caption(
            f"CSV {quality['raw_rows']:,} 列 → "
            f"清理後 {quality['clean_rows']:,} 列"
        )

        if quality["duplicate_rows"] > 0:
            st.warning(
                f"偵測到 {quality['duplicate_groups']:,} 組玩家＋週次重複資料，"
                "已自動保留資料較完整的一筆。"
            )
        else:
            st.success("沒有偵測到玩家＋週次重複資料。")

        if quality["invalid_date_rows"] > 0:
            st.warning(
                f"另排除 {quality['invalid_date_rows']:,} 筆無法辨識日期的資料。"
            )


def select_week_period(df):
    """只使用 CSV 真正存在的週次，不再讓使用者任選日曆日期。"""
    weeks = sorted(df["周次"].dt.date.unique().tolist())
    if not weeks:
        raise ValueError("CSV 中沒有可用的週次。")

    period_mode = st.pills(
        "統計期間",
        ["最新一週", "最近 4 週", "最近 8 週", "最近 12 週", "全部", "自訂"],
        default="最近 8 週",
        required=True,
        width="stretch",
        key="period_mode",
    )

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
                key="custom_week_range",
            )

    selected_weeks = sum(start_date <= week <= end_date for week in weeks)
    st.caption(
        f"目前範圍：{start_date:%Y-%m-%d} ～ {end_date:%Y-%m-%d} · "
        f"{selected_weeks} 週"
    )
    return start_date, end_date


def main():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    if not check_password():
        st.stop()

    try:
        file_mtime_ns = CSV_PATH.stat().st_mtime_ns
        df, quality = get_cached_data(str(CSV_PATH), file_mtime_ns)
    except Exception as exc:
        st.error(f"讀取資料失敗：{exc}")
        st.stop()

    st.title("公會每週統計")
    st.caption(
        f"每週戰績、參與與職位異動紀錄 · 最新資料 {quality['latest_week']}"
    )

    section = st.pills(
        "主要功能",
        ["個人資料", "公會排行", "原始資料"],
        default="個人資料",
        required=True,
        width="stretch",
        key="main_section",
        format_func=lambda value: {
            "個人資料": ":material/person: 個人資料",
            "公會排行": ":material/leaderboard: 公會排行",
            "原始資料": ":material/table_view: 原始資料",
        }[value],
    )

    st.divider()
    start_date, end_date = select_week_period(df)
    df_period = get_period_data(df, start_date, end_date)

    render_data_status(quality)

    st.divider()

    if section == "公會排行":
        render_leaderboard_page(df_period, start_date, end_date)
    elif section == "原始資料":
        render_raw_data_page(df_period)
    else:
        render_player_page(df, df_period, start_date, end_date)


if __name__ == "__main__":
    main()
