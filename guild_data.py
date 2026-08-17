import numpy as np
import pandas as pd

from guild_config import NUMERIC_COLUMNS, REQUIRED_COLUMNS, SEARCH_COLUMNS


def _clean_text_series(series, default="NA"):
    cleaned = series.fillna(default).astype(str).str.strip()
    return cleaned.replace({
        "": default,
        "nan": default,
        "None": default,
        "NaN": default,
    })


def _deduplicate_weekly_records(df):
    """
    同一位玩家同一週只保留一筆。

    CSV 偶爾會出現「空白佔位列 + 後來補上的有效紀錄」。
    這裡會優先保留有分數、有達成紀錄、資料較完整的那一列，
    避免平均、折線圖、達成率把同一週算兩次。
    """
    key_columns = ["周次", "暱稱"]
    duplicate_mask = df.duplicated(key_columns, keep=False)
    duplicate_rows = int(duplicate_mask.sum())
    duplicate_groups = int(
        df.loc[duplicate_mask, key_columns].drop_duplicates().shape[0]
    )

    if duplicate_rows == 0:
        return df, duplicate_rows, duplicate_groups

    work = df.copy()
    work["_row_order"] = np.arange(len(work))
    quality_score = pd.Series(0, index=work.index, dtype="int64")

    for col in NUMERIC_COLUMNS:
        numeric = pd.to_numeric(work[col], errors="coerce")
        quality_score += numeric.notna().astype(int)
        quality_score += numeric.fillna(0).gt(0).astype(int) * 4

    status_this = work["本周是否達成"].fillna("").astype(str).str.strip()
    status_two = work["近兩周是否達成"].fillna("").astype(str).str.strip()
    change = work["異動與否"].fillna("").astype(str).str.strip()
    level = pd.to_numeric(work["等級"], errors="coerce")
    image = work["圖片"].fillna("").astype(str).str.strip()

    quality_score += status_this.eq("達成").astype(int) * 3
    quality_score += status_two.eq("達成").astype(int) * 2
    quality_score += change.isin(["升階", "降階"]).astype(int)
    quality_score += level.fillna(0).gt(0).astype(int)
    quality_score += image.ne("").astype(int)

    work["_record_quality"] = quality_score

    work = work.sort_values(
        key_columns + ["_record_quality", "_row_order"]
    )
    work = work.drop_duplicates(key_columns, keep="last")
    work = work.sort_values("_row_order")
    work = work.drop(columns=["_row_order", "_record_quality"])

    return work, duplicate_rows, duplicate_groups


def load_data(csv_path):
    raw = pd.read_csv(csv_path)
    raw_rows = len(raw)

    missing_columns = [
        col for col in REQUIRED_COLUMNS
        if col not in raw.columns
    ]
    if missing_columns:
        raise ValueError(
            "CSV 缺少必要欄位：" + "、".join(missing_columns)
        )

    df = raw.copy()
    df = df.dropna(how="all")
    df = df.dropna(subset=["職業", "暱稱"])

    df["周次"] = pd.to_datetime(df["周次"], errors="coerce")
    invalid_date_rows = int(df["周次"].isna().sum())
    df = df.dropna(subset=["周次"])

    df["暱稱"] = df["暱稱"].astype(str).str.strip()
    df["職業"] = df["職業"].astype(str).str.strip()

    # 必須在 fillna(0) 前先處理重複資料，
    # 才能分辨「真的 0 分」和「原本是空白」。
    df, duplicate_rows, duplicate_groups = _deduplicate_weekly_records(df)

    for col in NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(
            df[col], errors="coerce"
        ).fillna(0)

    df["等級"] = pd.to_numeric(
        df["等級"], errors="coerce"
    ).fillna(0)

    for col in ["本周是否達成", "近兩周是否達成", "異動與否"]:
        df[col] = _clean_text_series(df[col])

    # 預先建立搜尋字串，搜尋時不用反覆把整張表轉字串。
    search_cols = [
        col for col in SEARCH_COLUMNS
        if col in df.columns
    ]
    search_frame = df[search_cols].copy()
    search_frame["周次"] = search_frame["周次"].dt.strftime("%Y-%m-%d")

    df["_search_text"] = (
        search_frame
        .fillna("")
        .astype(str)
        .agg(" ".join, axis=1)
        .str.lower()
    )

    df = df.sort_values(
        ["周次", "暱稱"]
    ).reset_index(drop=True)

    quality = {
        "raw_rows": raw_rows,
        "clean_rows": len(df),
        "invalid_date_rows": invalid_date_rows,
        "duplicate_rows": duplicate_rows,
        "duplicate_groups": duplicate_groups,
        "weeks": int(df["周次"].nunique()),
        "players": int(df["暱稱"].nunique()),
        "latest_week": df["周次"].max().strftime("%Y-%m-%d"),
    }

    return df, quality


def get_period_data(df, start_date, end_date):
    mask = (
        (df["周次"].dt.date >= start_date)
        & (df["周次"].dt.date <= end_date)
    )
    return df.loc[mask].copy()


def build_guild_stats(df_period):
    stats = (
        df_period
        .groupby("暱稱", as_index=True)
        .agg({
            "旗幟戰": "sum",
            "地下水道": "sum",
            "公會城每周": "sum",
            "周次": "nunique",
            "職業": "first",
            "圖片": "first",
        })
    )

    rank_mapping = [
        ("旗幟戰", "flag_rank"),
        ("地下水道", "water_rank"),
        ("公會城每周", "castle_rank"),
    ]

    for metric, rank_col in rank_mapping:
        stats[rank_col] = stats[metric].rank(
            ascending=False,
            method="min",
        )

    return stats


def get_latest_profile(player_history):
    """
    圖片與等級使用玩家「完整歷史」回溯，
    不受目前畫面選擇的日期區間影響。
    """
    history = player_history.sort_values(
        "周次",
        ascending=False,
    )

    valid_levels = history.loc[history["等級"] > 0]
    display_level = (
        int(valid_levels.iloc[0]["等級"])
        if not valid_levels.empty
        else "???"
    )

    image_text = (
        history["圖片"]
        .fillna("")
        .astype(str)
        .str.strip()
    )
    valid_images = history.loc[
        (image_text != "")
        & (image_text.str.lower() != "nan")
    ]
    img_url = (
        valid_images.iloc[0]["圖片"]
        if not valid_images.empty
        else None
    )

    job_text = (
        history["職業"]
        .fillna("")
        .astype(str)
        .str.strip()
    )
    valid_jobs = job_text.loc[
        (job_text != "")
        & (job_text.str.lower() != "nan")
    ]
    job_display = (
        valid_jobs.iloc[0]
        if not valid_jobs.empty
        else "未知"
    )

    return display_level, img_url, job_display
