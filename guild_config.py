import pandas as pd

CSV_FILENAME = "guild_data.csv"

REQUIRED_COLUMNS = [
    "周次", "暱稱", "職業", "旗幟戰", "地下水道", "公會城每周",
    "本周是否達成", "近兩周是否達成", "異動與否", "等級", "圖片",
]

NUMERIC_COLUMNS = ["旗幟戰", "地下水道", "公會城每周"]

SEARCH_COLUMNS = [
    "周次", "暱稱", "職業", "旗幟戰", "地下水道", "公會城每周",
    "本周是否達成", "近兩周是否達成", "異動與否", "等級",
]

PLOT_CONFIG = {
    "displayModeBar": True,
    "displaylogo": False,
    "modeBarButtonsToRemove": [
        "zoom2d", "pan2d", "select2d", "lasso2d", "zoomIn2d", "zoomOut2d",
        "autoScale2d", "resetScale2d", "hoverClosestCartesian", "hoverCompareCartesian",
    ],
    "toImageButtonOptions": {
        "format": "png",
        "filename": "chart_image",
        "height": 600,
        "width": 1000,
        "scale": 2,
    },
}

CUSTOM_CSS = """
<style>
:root {
    --guild-bg: #101318;
    --guild-surface: #191E25;
    --guild-surface-raised: #20262E;
    --guild-border: #343A43;
    --guild-gold: #C3A16A;
    --guild-gold-strong: #E0C18A;
    --guild-text: #F2F1ED;
    --guild-muted: #A6AEB9;
    --guild-faint: #818B98;
}

html, body, .stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
    background: var(--guild-bg) !important;
    color: var(--guild-text);
    color-scheme: dark;
}
body { font-family: "Noto Sans TC", "Microsoft JhengHei", system-ui, sans-serif; }
[data-testid="stHeader"], [data-testid="stToolbar"],
[data-testid="stDecoration"], [data-testid="stSidebarCollapsedControl"] {
    display: none !important;
}
#MainMenu { visibility: hidden !important; }
.block-container { max-width: 1200px; padding: 1.0rem 1.75rem 4.5rem; }
.st-key-mobile_nav { display: none !important; }

/* Navigation */
.st-key-site_nav {
    max-width: 770px;
    margin: 0 auto 2.1rem;
    padding: 5px;
    border: 1px solid var(--guild-border);
    border-radius: 11px;
    background: #171B21;
}
.st-key-site_nav [data-testid="stHorizontalBlock"] { gap: 5px !important; }
.st-key-site_nav [data-testid="stColumn"] { min-width: 0 !important; }
.st-key-site_nav [data-testid="stButton"] button {
    min-height: 43px !important;
    width: 100% !important;
    border-radius: 7px !important;
    white-space: nowrap !important;
    font-size: .87rem !important;
    font-weight: 650 !important;
    letter-spacing: .01em;
    box-shadow: none !important;
}
.st-key-site_nav [data-testid="stButton"] button,
.st-key-site_nav [data-testid="stButton"] button * {
    color: #C8CFD7 !important;
}
.st-key-site_nav [data-testid="stBaseButton-secondary"] {
    border: 1px solid transparent !important;
    background: transparent !important;
}
.st-key-site_nav [data-testid="stBaseButton-secondary"]:hover {
    border-color: #4C4F4E !important;
    background: #242931 !important;
}
.st-key-site_nav [data-testid="stBaseButton-primary"] {
    background: #302B23 !important;
    border: 1px solid #9B7B49 !important;
    box-shadow: inset 0 -2px 0 #B28E56 !important;
}
.st-key-site_nav [data-testid="stBaseButton-primary"],
.st-key-site_nav [data-testid="stBaseButton-primary"] * {
    color: var(--guild-gold-strong) !important;
}

/* Titles */
.site-kicker, .section-heading-kicker {
    color: var(--guild-gold);
    font-size: .70rem;
    font-weight: 700;
    letter-spacing: .13em;
}
.site-hero {
    position: relative;
    overflow: hidden;
    padding: 2.25rem 2.4rem;
    margin-bottom: 1.4rem;
    border: 1px solid #42413D;
    border-radius: 12px;
    background: linear-gradient(110deg, #20232A 0%, #181C23 64%, #161B22 100%);
}
.site-hero::before {
    content: "";
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 3px;
    background: #BB985E;
}
.site-hero::after {
    content: "";
    position: absolute;
    width: 200px;
    height: 200px;
    right: -45px;
    top: -100px;
    border: 1px solid rgba(195,161,106,.10);
    border-radius: 50%;
    pointer-events: none;
}
.site-hero h1, .page-heading h1, .login-heading h1 {
    color: #F6F4EF;
    margin: .38rem 0 .55rem;
    letter-spacing: -.035em;
    font-weight: 760;
}
.site-hero h1 { font-size: clamp(2rem, 3vw, 2.8rem); }
.site-hero p, .page-heading p, .login-heading p {
    max-width: 740px;
    margin: 0;
    color: var(--guild-muted);
    font-size: .93rem;
    line-height: 1.75;
}
.page-heading { margin: .4rem 0 1.45rem; padding: 0 0 .45rem; }
.page-heading h1 { font-size: clamp(1.8rem, 2.8vw, 2.25rem); }
.login-heading { max-width: 580px; text-align: center; margin: 8vh auto 1.8rem; }
.login-heading p { margin: 0 auto; }

.section-heading {
    display: flex;
    align-items: center;
    gap: .85rem;
    margin: 2rem 0 1rem;
    padding: .12rem 0;
}
.section-heading-line {
    width: 3px;
    height: 2.25rem;
    border-radius: 2px;
    flex-shrink: 0;
    background: #AC8A53;
}
.section-heading-title {
    color: var(--guild-text);
    font-size: 1.35rem;
    line-height: 1.25;
    font-weight: 740;
    letter-spacing: -.015em;
}
.section-heading span {
    display: block;
    margin-top: .3rem;
    color: var(--guild-muted);
    font-size: .83rem;
    line-height: 1.6;
}
.section-heading.focus-main { margin-top: 2.6rem; margin-bottom: 1.25rem; }
.section-heading.focus-main .section-heading-line { height: 3.25rem; }
.section-heading.focus-main .section-heading-title { font-size: 1.7rem; }
.section-heading.focus-main .section-heading-kicker {
    color: #B7A07A;
    font-size: .68rem;
    margin: 0 0 .18rem;
}

/* Metrics */
.stat-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: .85rem;
    margin: .55rem 0 1.35rem;
}
.stat-grid:has(.stat-card:nth-child(3):last-child) {
    grid-template-columns: repeat(3, minmax(0, 1fr));
}
.stat-card {
    min-width: 0;
    min-height: 146px;
    display: flex;
    flex-direction: column;
    padding: 1.18rem 1.15rem 1.0rem;
    border: 1px solid var(--guild-border);
    border-top: 2px solid #525A63;
    border-radius: 10px;
    background: var(--guild-surface);
}
.stat-card.range { border-top-color: #B89862; }
.stat-card.accent { border-top-color: #B89862; }
.stat-card.blue, .stat-card.green, .stat-card.neutral { border-top-color: #697581; }
.stat-label { color: #BBC3CC; font-weight: 600; font-size: .79rem; }
.stat-value {
    margin: .45rem 0 .5rem;
    color: #F7F3EB;
    font-size: clamp(1.5rem, 2.3vw, 2rem);
    font-weight: 760;
    line-height: 1.15;
    letter-spacing: -.024em;
    font-variant-numeric: tabular-nums;
    overflow-wrap: anywhere;
}
.stat-meta { color: #919BA9; font-size: .77rem; line-height: 1.55; margin-top: auto; }
.stat-period {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    column-gap: .42rem;
    row-gap: .1rem;
    font-size: clamp(1rem, 1.25vw, 1.21rem);
    letter-spacing: -.018em;
    line-height: 1.45;
}
.stat-period-divider { color: #9D875F; font-size: 1rem; }

/* Weekly highlights */
.focus-subheading { margin: .85rem 0 .75rem; }
.focus-subheading.growth-heading, .focus-subheading.ratio-heading { margin-top: 1.55rem; }
.focus-subheading span {
    display: block;
    color: #98A4B1;
    font-size: .73rem;
    font-weight: 650;
    letter-spacing: .045em;
}
.focus-subheading strong {
    display: block;
    color: #EAE9E5;
    font-size: 1.12rem;
    font-weight: 730;
    margin-top: .18rem;
}
.focus-card-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0,1fr));
    gap: .85rem;
    margin: 0 0 1rem;
}
.focus-rank-card {
    position: relative;
    overflow: hidden;
    min-width: 0;
    min-height: 188px;
    padding: 1.2rem 1.2rem 1rem;
    border: 1px solid var(--guild-border);
    border-radius: 10px;
    background: #1C2128;
}
.focus-rank-card.rank-1 { border-color: #746349; }
.focus-rank-card::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 2px;
    background: #7C8996;
}
.focus-rank-card.rank-1::before { background: var(--guild-gold); }
.focus-rank-card-top { position: relative; z-index: 1; }
.focus-rank-badge {
    display: inline-block;
    color: #CBB58F;
    font-size: .75rem;
    font-weight: 700;
    letter-spacing: .02em;
}
.focus-rank-card-name {
    position: relative;
    z-index: 1;
    margin-top: .85rem;
    color: #F4F1E9;
    font-size: 1.09rem;
    font-weight: 735;
    line-height: 1.4;
    overflow-wrap: anywhere;
}
.focus-rank-card-job { position: relative; z-index: 1; margin-top: .12rem; color: #A4ADBA; font-size: .77rem; }
.focus-rank-card-value {
    position: relative;
    z-index: 1;
    margin-top: 1.05rem;
    color: #F2F1ED;
    font-variant-numeric: tabular-nums;
    font-weight: 750;
    font-size: clamp(1.48rem, 2vw, 1.9rem);
    letter-spacing: -.026em;
}
.focus-rank-card-value small { font-size: .7rem; color: #9EA6B2; margin-left: .2rem; }
.focus-rank-card-meta { position: relative; z-index: 1; margin-top: .22rem; color: #9DA5B2; font-size: .77rem; }
.focus-rank-card.has-character .focus-rank-card-name,
.focus-rank-card.has-character .focus-rank-card-job,
.focus-rank-card.has-character .focus-rank-card-value,
.focus-rank-card.has-character .focus-rank-card-meta,
.focus-rank-card.has-character .focus-rank-card-top { max-width: calc(100% - 85px); }
.focus-character { position: absolute; right: 5px; bottom: 5px; width: 99px; height: 130px; display: flex; align-items: flex-end; justify-content: center; pointer-events: none; }
.focus-character img { max-width: 100%; max-height: 100%; object-fit: contain; }
.focus-empty-card { padding: 1rem; border: 1px solid var(--guild-border); border-radius: 9px; background: var(--guild-surface); color: var(--guild-muted); }
.focus-change-card {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1.5rem;
    padding: 1.1rem 1.25rem;
    margin: .1rem 0 1.6rem;
    border: 1px solid #575044;
    border-left: 3px solid #C4A573;
    border-radius: 11px;
    background: linear-gradient(105deg, #26231F 0%, #1D2229 100%);
}
.focus-change-label { color: #EEE9E0; font-size: 1rem; font-weight: 710; }
.focus-change-meta { margin-top: .22rem; color: #9E9B94; font-size: .75rem; }
.change-counts { display: flex; gap: .75rem; }
.change-counts > div { min-width: 90px; padding: .45rem .85rem; border: 1px solid #3B3934; border-radius: 7px; background: #292820; }
.change-counts span { display: block; font-size: 1.38rem; font-weight: 750; }
.change-counts small { display: block; color: #BBB3A6; font-size: .7rem; }
.change-up { color: #A3C5AB; }
.change-down { color: #DAA3A3; }
.home-note { display: none; }

/* Ranking list */
.guild-rank-list { display: flex; flex-direction: column; gap: 7px; margin: .35rem 0 1.15rem; }
.guild-rank-row {
    display: grid;
    grid-template-columns: 44px 73px minmax(0,1fr) minmax(190px,auto);
    gap: 15px;
    align-items: center;
    min-height: 97px;
    padding: 10px 19px 10px 14px;
    border: 1px solid #323943;
    border-radius: 9px;
    background: #1B2027;
}
.guild-rank-row:hover { border-color: #565246; background: #20252D; }
.guild-rank-row.is-top-1 { background: #24231E; border-color: #8A7145; }
.guild-rank-row.is-top-2 { border-color: #66707C; }
.guild-rank-row.is-top-3 { border-color: #766351; }
.guild-rank-position { color: #A9B2BE; text-align: center; font-weight: 740; font-size: 1.08rem; font-variant-numeric: tabular-nums; }
.guild-rank-row.is-top-1 .guild-rank-position { color: #E0BD78; }
.guild-rank-row.is-top-2 .guild-rank-position { color: #CBD0DB; }
.guild-rank-row.is-top-3 .guild-rank-position { color: #CEAA86; }
.guild-rank-avatar {
    position: relative;
    width: 72px;
    height: 73px;
    display: flex;
    justify-content: center;
    align-items: center;
    overflow: hidden;
    border: 1px solid #424852;
    border-radius: 8px;
    background: #282E37;
}
.guild-rank-avatar img { position: absolute; inset: 0; margin: auto; max-width: 100%; max-height: 100%; object-fit: contain; }
.guild-avatar-fallback { color: #858F9D; font-size: 1.55rem; }
.guild-rank-identity { min-width: 0; }
.guild-rank-identity strong { display: block; color: #F2F2F0; font-size: 1.07rem; font-weight: 730; overflow-wrap: anywhere; }
.guild-rank-detail { margin-top: .37rem; color: #A1ACB8; font-size: .8rem; line-height: 1.45; }
.guild-mid-dot { margin: 0 .5rem; color: #7D8793; }
.guild-rank-score { min-width: 0; text-align: right; font-variant-numeric: tabular-nums; }
.guild-rank-score strong { display: block; color: #F6F3EE; font-size: 1.32rem; font-weight: 780; line-height: 1.25; white-space: nowrap; }
.guild-rank-score strong span { margin-left: .35rem; font-size: .73rem; color: #AEB6C0; font-weight: 600; }
.guild-rank-score small { display: block; margin-top: .38rem; font-size: .73rem; color: #9AA5B3; }

/* Native, clickable detail links integrated into ranking cards */
[class*="st-key-guild_rank_card_"] {
    padding: 7px 11px 7px 10px;
    margin: 7px 0;
    border: 1px solid #39414B;
    border-radius: 12px;
    background: #1B2027;
    transition: border-color .18s ease, background-color .18s ease;
}
[class*="st-key-guild_rank_card_"]:hover {
    border-color: #766647;
    background: #20252C;
}
[class*="st-key-guild_rank_card_"] .guild-rank-list { margin: 0; }
[class*="st-key-guild_rank_card_"] .guild-rank-row {
    min-height: 76px;
    padding: 0;
    border: 0;
    background: none;
    grid-template-columns: 35px 60px minmax(0, 1fr) minmax(120px, auto);
    gap: 12px;
}
[class*="st-key-guild_rank_card_"] .guild-rank-row:hover,
[class*="st-key-guild_rank_card_"] .guild-rank-row.is-top-1 { background: none; }
[class*="st-key-guild_rank_card_"] .guild-rank-avatar { width: 60px; height: 65px; }
[class*="st-key-guild_rank_card_"] [data-testid="stButton"] button {
    background: #292A29 !important;
    color: #E8D3AD !important;
    border: 1px solid #756243 !important;
    border-radius: 9px !important;
    min-height: 39px;
    font-weight: 650;
    font-size: .81rem;
    white-space: nowrap;
}
[class*="st-key-guild_rank_card_"] [data-testid="stButton"] button:hover {
    background: #3B3328 !important;
    border-color: #B69A6A !important;
    color: #F5E0B6 !important;
}
[class*="st-key-guild_rank_card_"] [data-testid="stButton"] button * { color: inherit !important; }
.guild-rank-match {
    padding: .03em .12em;
    background: #635033;
    border-radius: 3px;
    color: #FFF2D6;
}
@media (max-width: 720px) {
    [class*="st-key-guild_rank_card_"] { padding: 8px; }
    [class*="st-key-guild_rank_card_"] .guild-rank-row {
        grid-template-columns: 24px 52px minmax(0, 1fr);
        gap: 7px;
        min-height: 76px;
    }
    [class*="st-key-guild_rank_card_"] .guild-rank-position,
    [class*="st-key-guild_rank_card_"] .guild-rank-avatar { grid-row: span 2; }
    [class*="st-key-guild_rank_card_"] .guild-rank-avatar { width: 51px; height: 57px; }
    [class*="st-key-guild_rank_card_"] .guild-rank-score { grid-column: 3; text-align: left; }
    [class*="st-key-guild_rank_card_"] .guild-rank-score strong { font-size: 1rem; }
    [class*="st-key-guild_rank_card_"] .guild-rank-score small { display: block; margin: 0; }
    [class*="st-key-guild_rank_card_"] [data-testid="stButton"] button {
        font-size: .72rem;
        min-height: 37px;
        padding: .35rem .4rem;
    }
}

/* Rank filters — quiet slate surfaces + warm brass selection */
.st-key-leaderboard_filters {
    margin: .75rem 0 1.65rem;
    padding: 1.3rem 1.5rem 1.15rem;
    border: 1px solid #3C4652;
    border-radius: 14px;
    background: linear-gradient(145deg, #1D242D, #191D24 75%);
    box-shadow: 0 12px 32px rgba(0,0,0,.12);
}
.guild-filter-heading { display: flex; align-items: center; gap: .6rem; margin: 0 0 .73rem; }
.guild-filter-heading::before {
    content: "";
    width: 3px;
    height: 15px;
    border-radius: 3px;
    background: #B89B6D;
}
.guild-filter-label { font-size: .87rem; color: #E9EAE8; font-weight: 690; letter-spacing: .025em; }
.guild-filter-separator { height: 1px; margin: 1.4rem 0 1.15rem; background: linear-gradient(90deg, #46505A, #303842); }
.guild-filter-summary {
    display: inline-flex;
    align-items: center;
    gap: .12rem;
    margin: .95rem 0 0;
    padding: .4rem .72rem;
    border: 1px solid #37434E;
    border-radius: 7px;
    background: #222A33;
    color: #B3C0CF;
    font-variant-numeric: tabular-nums;
    font-size: .78rem;
}
.guild-filter-separator-dot { margin: 0 .4rem; color: #8D9AA9; }

/* Streamlit 1.61+ (stButtonGroup / data-selected) and legacy widget support.
   This replaces the outdated selectors which let the default red active text show. */
.stApp [data-testid="stButtonGroup"] [data-variant="segmented_control"],
.stApp [data-testid="stBaseButton-segmented_control"],
.stApp [data-testid="stBaseButton-segmented_controlActive"] {
    min-height: 40px !important;
    height: auto !important;
    margin-right: 0 !important;
    padding: .48rem 1.02rem !important;
    border: 1px solid #414D5B !important;
    border-radius: 9px !important;
    background: #222A34 !important;
    color: #C7D0DA !important;
    font-size: .85rem !important;
    font-weight: 630 !important;
    letter-spacing: .012em;
    line-height: 1.35 !important;
    box-shadow: none !important;
    transition: background-color .16s ease, border-color .16s ease, color .16s ease, transform .16s ease;
}
/* Separate tiles instead of an old-fashioned joined red tab bar. */
.stApp [data-testid="stButtonGroup"] [role="group"],
.stApp [data-testid="stButtonGroup"] [role="radiogroup"],
.stApp [data-testid="stButtonGroup"] [aria-label] {
    column-gap: .5rem !important;
    row-gap: .5rem !important;
}
.stApp [data-testid="stButtonGroup"] [data-variant="segmented_control"] *,
.stApp [data-testid="stBaseButton-segmented_control"] *,
.stApp [data-testid="stBaseButton-segmented_controlActive"] * {
    color: inherit !important;
}
.stApp [data-testid="stButtonGroup"] [data-variant="segmented_control"]:is(:hover,[data-hovered]):not([data-selected]):not([data-disabled]),
.stApp [data-testid="stBaseButton-segmented_control"]:hover {
    background: #333D49 !important;
    border-color: #728092 !important;
    color: #F0F2F4 !important;
}
.stApp [data-testid="stButtonGroup"] [data-variant="segmented_control"][data-selected]:not([data-disabled]),
.stApp [data-testid="stButtonGroup"] [data-variant="segmented_control"][aria-pressed="true"],
.stApp [data-testid="stBaseButton-segmented_controlActive"],
.stApp [data-testid="stSegmentedControl"] button[aria-checked="true"] {
    background: linear-gradient(135deg, #5A4C38, #3F392F) !important;
    border: 1px solid #B99A69 !important;
    color: #FFF4E1 !important;
    box-shadow: 0 0 0 1px rgba(185,154,105,.10), inset 0 1px 0 rgba(255,255,255,.08) !important;
}
.stApp [data-testid="stButtonGroup"] [data-variant="segmented_control"][data-selected]:is(:hover,[data-hovered],[data-focus-visible]):not([data-disabled]),
.stApp [data-testid="stBaseButton-segmented_controlActive"]:hover {
    background: linear-gradient(135deg, #66563E, #4B4032) !important;
    border-color: #DBB980 !important;
    color: #FFF7EA !important;
}
.stApp [data-testid="stButtonGroup"] [data-variant="segmented_control"][data-focus-visible],
.stApp [data-testid^="stBaseButton-segmented_control"]:focus-visible {
    outline: 2px solid #DDBB86 !important;
    outline-offset: 3px !important;
}
.stApp [data-testid="stButtonGroup"] [data-variant="segmented_control"][data-disabled] {
    opacity: .4;
    cursor: not-allowed;
}
.st-key-leaderboard_filters [data-variant="segmented_control"],
.st-key-leaderboard_filters [data-testid^="stBaseButton-segmented_control"] {
    min-height: 42px !important;
}

/* Input and secondary action styles */
.stApp [data-testid="stTextInput"] input,
.stApp [data-testid="stSelectbox"] [data-baseweb="select"] > div,
.stApp [data-testid="stNumberInput"] input {
    background: #1F242C !important;
    border-color: #414953 !important;
    color: #F0F1F2 !important;
    border-radius: 7px !important;
}
.stApp [data-testid="stTextInput"] input:focus,
.stApp [data-testid="stNumberInput"] input:focus { border-color: #B08C53 !important; }
.stApp [data-testid="stBaseButton-secondary"]:not(.st-key-site_nav *) {
    border-color: #464E57;
    background: #222832;
    color: #D8DFE7;
}
.stApp [data-testid="stBaseButton-secondary"]:not(.st-key-site_nav *):hover {
    border-color: #AC8954;
    color: #F2E1C4;
}
.stApp [data-testid="stBaseButton-primary"]:not(.st-key-site_nav *) {
    border-color: #BC9B68;
    background: #8F7143;
    color: #FAF7F2;
}
.stApp [data-testid="stExpander"] { border-color: #3C434C; background: #181D24; border-radius: 8px; }
.stApp [data-testid="stDataFrame"] { border-radius: 8px; overflow: hidden; }
.stApp [data-testid="stVerticalBlockBorderWrapper"] { border-color: #3B434D; border-radius: 10px; }

.name-chip-wrap { display: flex; flex-wrap: wrap; gap: .45rem; margin: .75rem 0 1.1rem; }
.name-chip { color: #D8DCE2; padding: .3rem .55rem; border: 1px solid #454C55; border-radius: 5px; background: #1D232B; font-size: .85rem; }
.rank-context { display: grid; grid-template-columns: 1fr 1.4fr 1.4fr; gap: .75rem; padding: .95rem 1rem; margin: .75rem 0 1.1rem; border: 1px solid #36434F; border-radius: 8px; background: #1B222A; color: #AFBBC8; font-size: .82rem; }
.rank-context strong { color: #E0E5EA; }
.ranking-callout { padding: .95rem 1rem; margin: .8rem 0 1rem; border-left: 3px solid #AA8752; background: #222119; color: #E0D8C6; border-radius: 6px; }

/* Responsive layouts */
@media (max-width: 900px) {
    .stat-grid { grid-template-columns: repeat(2, minmax(0,1fr)); }
    .focus-rank-card.has-character .focus-rank-card-name,
    .focus-rank-card.has-character .focus-rank-card-job,
    .focus-rank-card.has-character .focus-rank-card-value,
    .focus-rank-card.has-character .focus-rank-card-meta,
    .focus-rank-card.has-character .focus-rank-card-top { max-width: calc(100% - 70px); }
    .focus-character { width: 82px; height: 111px; }
}
@media (max-width: 720px) {
    .block-container { padding: .55rem .95rem 3.5rem; }
    .st-key-site_nav { margin: .15rem auto 1.5rem; padding: 4px; }
    .st-key-site_nav [data-testid="HorizontalBlock"],
    .st-key-site_nav [data-testid="stHorizontalBlock"] { gap: 4px !important; }
    .st-key-site_nav [data-testid="stButton"] button {
        min-height: 42px !important;
        font-size: .77rem !important;
        padding: .35rem .15rem !important;
    }
    .st-key-site_nav [data-testid="stButton"] button svg { width: 1rem !important; height: 1rem !important; }
    .site-hero { padding: 1.6rem 1.35rem; }
    .page-heading h1 { font-size: 1.85rem; }
    .stat-grid:has(.stat-card:nth-child(3):last-child) { grid-template-columns: repeat(2, minmax(0,1fr)); }
    .focus-card-grid { grid-template-columns: 1fr; }
    .focus-rank-card { min-height: 170px; }
    .focus-character { width: 98px; height: 120px; }
    .focus-change-card { flex-wrap: wrap; }
    .rank-context { grid-template-columns: 1fr; }
    .guild-rank-row {
        grid-template-columns: 28px 60px minmax(0,1fr);
        column-gap: 11px;
        row-gap: 2px;
        min-height: 90px;
        padding: 10px 12px 10px 9px;
    }
    .guild-rank-position { grid-row: span 2; font-size: .95rem; }
    .guild-rank-avatar { width: 60px; height: 64px; grid-row: span 2; }
    .guild-rank-identity strong { font-size: .98rem; }
    .guild-rank-detail { font-size: .73rem; margin-top: .22rem; }
    .guild-mid-dot { margin: 0 .22rem; }
    .guild-rank-score { grid-column: 3; text-align: left; }
    .guild-rank-score strong { display: inline; font-size: 1.06rem; }
    .guild-rank-score small { display: inline; margin-left: .5rem; font-size: .69rem; }
    .st-key-leaderboard_filters { padding: 1.0rem .9rem; }
    .stApp [data-testid^="stBaseButton-segmented_control"],
    .stApp [data-testid="stButtonGroup"] [data-variant="segmented_control"] {
        padding: .43rem .72rem !important;
        font-size: .79rem !important;
    }
    .stApp [data-testid="stButtonGroup"] [role="group"],
    .stApp [data-testid="stButtonGroup"] [role="radiogroup"] {
        column-gap: .38rem !important;
    }
}
@media (max-width: 480px) {
    .stat-grid, .stat-grid:has(.stat-card:nth-child(3):last-child) { grid-template-columns: repeat(2, minmax(0,1fr)); gap: .55rem; }
    .stat-card { min-height: 138px; padding: .95rem .78rem; }
    .stat-value { font-size: 1.45rem; }
    .stat-period { font-size: .9rem; column-gap: .25rem; }
    .stat-period-divider { font-size: .9rem; }
    .stat-meta { font-size: .70rem; }
    .section-heading.focus-main .section-heading-title { font-size: 1.43rem; }
    .section-heading-title { font-size: 1.18rem; }
    .guild-rank-row { grid-template-columns: 24px 54px minmax(0,1fr); column-gap: 8px; padding: 9px 8px; }
    .guild-rank-avatar { width: 53px; height: 59px; }
    .guild-rank-score small { display: block; margin: .2rem 0 0; }
    .st-key-site_nav [data-testid="stButton"] button { min-height: 39px !important; font-size: .70rem !important; }
    .st-key-site_nav [data-testid="stButton"] button svg { width: .85rem !important; height: .85rem !important; }
    .guild-filter-summary { font-size: .73rem; }
    .change-counts { width: 100%; }
    .change-counts > div { flex: 1; }
}
@media (max-width: 350px) {
    .stat-grid { grid-template-columns: 1fr; }
    .st-key-site_nav [data-testid="stButton"] button { font-size: .63rem !important; }
}
@media (prefers-reduced-motion: reduce) {
    *, *::before, *::after { scroll-behavior: auto !important; transition-duration: 0s !important; }
}
</style>
"""


JOB_HIERARCHY_ROWS = [
    ('冒險家', '劍士', '英雄'),
    ('冒險家', '劍士', '聖騎士'),
    ('冒險家', '劍士', '黑騎士'),
    ('冒險家', '法師', '大魔導士(火、毒)'),
    ('冒險家', '法師', '大魔導士(冰、雷)'),
    ('冒險家', '法師', '主教'),
    ('冒險家', '弓箭手', '箭神'),
    ('冒險家', '弓箭手', '神射手'),
    ('冒險家', '弓箭手', '開拓者'),
    ('冒險家', '盜賊', '夜使者'),
    ('冒險家', '盜賊', '暗影神偷'),
    ('冒險家', '盜賊', '影武者'),
    ('冒險家', '海盜', '拳霸'),
    ('冒險家', '海盜', '槍神'),
    ('冒險家', '海盜', '重砲指揮官'),
    ('英雄團', '劍士', '狂狼勇士'),
    ('英雄團', '法師', '龍魔導士'),
    ('英雄團', '法師', '夜光'),
    ('英雄團', '弓箭手', '精靈遊俠'),
    ('英雄團', '盜賊', '幻影俠盜'),
    ('英雄團', '海盜', '隱月'),
    ('皇家騎士團', '劍士', '聖魂劍士'),
    ('皇家騎士團', '劍士', '米哈逸'),
    ('皇家騎士團', '法師', '烈焰巫師'),
    ('皇家騎士團', '弓箭手', '破風使者'),
    ('皇家騎士團', '盜賊', '暗夜行者'),
    ('皇家騎士團', '海盜', '閃雷悍將'),
    ('末日反抗軍', '劍士', '惡魔殺手'),
    ('末日反抗軍', '劍士', '惡魔復仇者'),
    ('末日反抗軍', '劍士', '爆拳槍神'),
    ('末日反抗軍', '法師', '煉獄巫師'),
    ('末日反抗軍', '弓箭手', '狂豹獵人'),
    ('末日反抗軍', '盜賊', '傑諾'),
    ('末日反抗軍', '海盜', '傑諾'),
    ('末日反抗軍', '海盜', '機甲戰神'),
    ('神之子', '劍士', '神之子'),
    ('超新星', '劍士', '凱撒'),
    ('超新星', '弓箭手', '凱殷'),
    ('超新星', '盜賊', '卡蒂娜'),
    ('超新星', '海盜', '天使破壞者'),
    ('雷普族', '劍士', '阿戴爾'),
    ('雷普族', '法師', '伊利恩'),
    ('雷普族', '盜賊', '卡莉'),
    ('雷普族', '海盜', '亞克'),
    ('阿尼瑪', '劍士', '蓮'),
    ('阿尼瑪', '法師', '菈菈'),
    ('阿尼瑪', '盜賊', '虎影'),
    ('朋友世界', '法師', '凱內西斯'),
    ('曉之陣', '劍士', '劍豪'),
    ('曉之陣', '法師', '陰陽師'),
    ('江湖', '法師', '琳恩'),
    ('江湖', '海盜', '墨玄'),
    ('其他', '劍士', '炭治郎'),
    ('其他', '劍士', '粉豆'),
    ('其他', '海盜', '雪吉拉'),
    ('其他', '其他', 'null'),
]

JOB_HIERARCHY = pd.DataFrame(
    JOB_HIERARCHY_ROWS,
    columns=["group", "category", "job"],
)
