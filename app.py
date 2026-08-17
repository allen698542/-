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
    page_title="公會每周統計",
    page_icon="🍁",
    layout="wide",
)

BASE_DIR = Path(__file__).resolve().parent
CSV_PATH = BASE_DIR / CSV_FILENAME


def get_app_passwords():
    """
    密碼改放 Streamlit Secrets / 環境變數。
    不再直接寫在 app.py 裡。
    """
    passwords = []

    try:
        raw = st.secrets.get("APP_PASSWORDS", [])
        if isinstance(raw, str):
            passwords.append(raw)
        else:
            passwords.extend(
                str(value)
                for value in raw
                if str(value).strip()
            )

        for key in ("APP_PASSWORD", "APP_PASSWORD_2"):
            value = st.secrets.get(key, "")
            if value:
                passwords.append(str(value))
    except Exception:
        # 本機沒有 secrets.toml 時，
        # 還可以使用環境變數。
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
        st.error(
            "🔐 尚未設定網站密碼。"
            "請在 Streamlit Secrets 設定 APP_PASSWORDS。"
        )
        st.code(
            'APP_PASSWORDS = ["你的密碼1", "你的密碼2"]',
            language="toml",
        )
        return False

    if "password_correct" not in st.session_state:
        st.session_state.password_correct = False

    if st.session_state.password_correct:
        return True

    st.write("")
    st.write("")
    _, center, _ = st.columns([1, 1.5, 1])

    with center:
        with st.container(border=True):
            st.markdown(
                "<h3 style='text-align:center;'>🔐 請輸入密碼</h3>",
                unsafe_allow_html=True,
            )
            password = st.text_input(
                "密碼",
                type="password",
                label_visibility="collapsed",
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
                    st.error("❌ 密碼錯誤")

    return False


@st.cache_data(ttl=600, show_spinner=False)
def get_cached_data(csv_path, file_mtime_ns):
    # file_mtime_ns 只用來讓 CSV 更新時 cache 自動失效。
    del file_mtime_ns
    return load_data(csv_path)


def render_data_status(quality):
    with st.sidebar.expander("🧪 資料狀態", expanded=False):
        st.caption(
            f"目前資料：{quality['players']:,} 位玩家 / "
            f"{quality['weeks']:,} 個週次"
        )
        st.caption(
            f"最新週次：{quality['latest_week']}"
        )
        st.caption(
            f"CSV 原始 {quality['raw_rows']:,} 列 → "
            f"清理後 {quality['clean_rows']:,} 列"
        )

        if quality["duplicate_rows"] > 0:
            st.warning(
                f"偵測到 {quality['duplicate_groups']:,} 組"
                "「玩家＋週次」重複資料，"
                "網站已自動保留資料較完整的一筆。"
            )
        else:
            st.success("沒有偵測到玩家＋週次重複資料。")

        if quality["invalid_date_rows"] > 0:
            st.warning(
                f"另排除 {quality['invalid_date_rows']:,} "
                "筆無法辨識日期的資料。"
            )


def main():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    if not check_password():
        st.stop()

    try:
        file_mtime_ns = CSV_PATH.stat().st_mtime_ns
        df, quality = get_cached_data(
            str(CSV_PATH),
            file_mtime_ns,
        )
    except Exception as exc:
        st.error(f"讀取資料失敗：{exc}")
        st.stop()

    st.title("🍁 公會每周統計")
    st.sidebar.header("📅 日期區間設定")

    data_min_date = df["周次"].min().date()
    data_max_date = df["周次"].max().date()

    col_start, col_end = st.sidebar.columns(2)

    with col_start:
        start_date = st.date_input(
            "開始日期",
            value=data_min_date,
            min_value=data_min_date,
            max_value=data_max_date,
            format="YYYY-MM-DD",
        )

    with col_end:
        end_date = st.date_input(
            "結束日期",
            value=data_max_date,
            min_value=data_min_date,
            max_value=data_max_date,
            format="YYYY-MM-DD",
        )

    render_data_status(quality)

    if start_date > end_date:
        st.sidebar.error(
            "⚠️ 「開始日期」不能晚於「結束日期」"
        )
        st.stop()

    df_period = get_period_data(
        df,
        start_date,
        end_date,
    )

    st.markdown("### 🔍 功能面板")
    search_mode = st.radio(
        "請選擇功能：",
        [
            "個人查詢 (層級篩選)",
            "個人查詢 (直接搜尋)",
            "🏆 全公會排行榜",
            "📂 原始資料查詢",
        ],
        horizontal=True,
    )

    if search_mode == "🏆 全公會排行榜":
        render_leaderboard_page(
            df_period,
            start_date,
            end_date,
        )
    elif search_mode == "📂 原始資料查詢":
        render_raw_data_page(df_period)
    else:
        render_player_page(
            df,
            df_period,
            search_mode,
            start_date,
            end_date,
        )


if __name__ == "__main__":
    main()
