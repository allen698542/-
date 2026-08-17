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
    --guild-accent: #C79A52;
    --guild-text-soft: #AEB4BE;
    --guild-panel: rgba(255,255,255,0.035);
    --guild-border: rgba(255,255,255,0.10);
}

/*
 * 手機內嵌瀏覽器有時會以 light theme 開啟 Streamlit iframe。
 * 這個網站固定採深色視覺，因此讓主畫布與自訂元件自行帶背景，
 * 不再只依賴瀏覽器傳進來的 theme。
 */
html, body {
    background: #111318 !important;
    color-scheme: dark;
}
.stApp,
[data-testid="stAppViewContainer"],
[data-testid="stMain"] {
    background: #111318 !important;
    color: #F2F3F5 !important;
}
[data-testid="stHeader"] {
    background: rgba(17,19,24,0.97) !important;
}

/* 頁內手機導覽：桌機隱藏，手機再顯示。網站沒有使用 sidebar，隱藏其折疊按鈕。 */
.st-key-mobile_nav {
    display: none !important;
}
[data-testid="stSidebarCollapsedControl"] {
    display: none !important;
}

.block-container {
    max-width: 1180px;
    padding-top: 2.1rem;
    padding-bottom: 4rem;
}

/* 網站標題區：保留一點遊戲感，但避免發光、彩虹等過度效果。 */
.site-hero {
    position: relative;
    overflow: hidden;
    padding: 2.4rem 2.5rem;
    margin-bottom: 1.5rem;
    border: 1px solid var(--guild-border);
    border-radius: 18px;
    background:
        radial-gradient(circle at 85% 10%, rgba(199,154,82,0.20), transparent 34%),
        linear-gradient(135deg, #191D25 0%, #121419 68%);
}
.site-hero::after {
    content: "";
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    width: 4px;
    background: var(--guild-accent);
}
.site-hero h1,
.page-heading h1,
.login-heading h1 {
    margin: 0.15rem 0 0.55rem 0;
    letter-spacing: -0.025em;
}
.site-hero h1 { font-size: clamp(2rem, 4vw, 3.2rem); }
.site-hero p,
.page-heading p,
.login-heading p {
    margin: 0;
    color: var(--guild-text-soft);
}
.site-kicker {
    color: var(--guild-accent);
    font-size: 0.72rem;
    letter-spacing: 0.16em;
    font-weight: 700;
}

.page-heading {
    margin: 0.4rem 0 1.25rem 0;
}
.page-heading h1 { font-size: 2rem; }

.login-heading {
    max-width: 620px;
    text-align: center;
    margin: 8vh auto 1.5rem auto;
}

.home-note {
    color: var(--guild-text-soft);
    font-size: 0.92rem;
}


/* 首頁焦點：三張直向卡片為一列，水道與兩種成長排行共用同一套視覺。 */
.focus-subheading {
    margin: 0.75rem 0 0.65rem 0;
}
.focus-subheading span {
    display: block;
    color: #9BA9BC;
    font-size: 0.76rem;
    font-weight: 700;
    letter-spacing: 0.055em;
}
.focus-subheading strong {
    display: block;
    margin-top: 0.15rem;
    color: #F3F5F8;
    font-size: 1.2rem;
    font-weight: 760;
}
.focus-subheading.growth-heading { margin-top: 1.35rem; }
.focus-subheading.ratio-heading { margin-top: 1.35rem; }

.focus-card-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.9rem;
    margin: 0 0 1rem 0;
}
.focus-rank-card {
    position: relative;
    overflow: hidden;
    min-width: 0;
    min-height: 184px;
    padding: 1.05rem 1.1rem 1rem 1.1rem;
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 16px;
    background: linear-gradient(145deg, #1B1F27 0%, #15181E 100%);
    box-shadow: 0 10px 30px rgba(0,0,0,0.16);
    transition: transform 160ms ease, border-color 160ms ease, box-shadow 160ms ease;
}
.focus-rank-card:hover {
    transform: translateY(-2px);
}
.focus-rank-card.water {
    border-color: rgba(90,143,196,0.24);
    background:
        radial-gradient(circle at 88% 8%, rgba(90,143,196,0.21), transparent 34%),
        linear-gradient(145deg, #1B2230 0%, #15181E 72%);
}
.focus-rank-card.growth {
    border-color: rgba(101,165,122,0.24);
    background:
        radial-gradient(circle at 88% 8%, rgba(101,165,122,0.22), transparent 34%),
        linear-gradient(145deg, #1A2420 0%, #15191A 72%);
}
.focus-rank-card.ratio {
    border-color: rgba(124,143,208,0.25);
    background:
        radial-gradient(circle at 88% 8%, rgba(124,143,208,0.23), transparent 34%),
        linear-gradient(145deg, #1D2130 0%, #16181F 72%);
}
.focus-rank-card.rank-1 {
    box-shadow: 0 13px 34px rgba(0,0,0,0.20);
}
.focus-rank-card.water.rank-1 { border-color: rgba(90,143,196,0.38); }
.focus-rank-card.growth.rank-1 { border-color: rgba(101,165,122,0.38); }
.focus-rank-card.ratio.rank-1 { border-color: rgba(124,143,208,0.40); }
.focus-rank-card::before {
    content: "";
    position: absolute;
    left: 0;
    top: 0;
    right: 0;
    height: 3px;
    background: #5A8FC4;
}
.focus-rank-card.water::before { background: #5A8FC4; }
.focus-rank-card.growth::before { background: #65A57A; }
.focus-rank-card.ratio::before { background: #7C8FD0; }
.focus-rank-card-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    min-height: 1.6rem;
}
.focus-rank-badge {
    display: inline-flex;
    align-items: center;
    padding: 0.28rem 0.55rem;
    border-radius: 999px;
    background: linear-gradient(135deg, rgba(90,143,196,0.22), rgba(90,143,196,0.10));
    color: #C5D9EC;
    font-size: 0.73rem;
    font-weight: 750;
}
.focus-rank-card.growth .focus-rank-badge {
    background: linear-gradient(135deg, rgba(101,165,122,0.23), rgba(101,165,122,0.10));
    color: #B9DFC4;
}
.focus-rank-card.ratio .focus-rank-badge {
    background: linear-gradient(135deg, rgba(124,143,208,0.24), rgba(124,143,208,0.11));
    color: #CAD2F4;
}
.focus-rank-card-name {
    margin-top: 0.9rem;
    color: #F4F5F7;
    font-size: 1.12rem;
    font-weight: 760;
    line-height: 1.25;
    overflow-wrap: anywhere;
}
.focus-rank-card-job {
    min-height: 1.25rem;
    margin-top: 0.18rem;
    color: #8F98A6;
    font-size: 0.77rem;
}
.focus-rank-card-value {
    margin-top: 0.9rem;
    color: #EFF4FA;
    font-size: clamp(1.55rem, 2.5vw, 2rem);
    font-weight: 780;
    letter-spacing: -0.025em;
    line-height: 1.05;
}
.focus-rank-card.growth .focus-rank-card-value { color: #C9E7D1; }
.focus-rank-card.ratio .focus-rank-card-value { color: #D4DCF7; }
.focus-rank-card-value small {
    color: #929AA6;
    font-size: 0.72rem;
    font-weight: 650;
}
.focus-rank-card-meta {
    margin-top: 0.55rem;
    color: #929AA6;
    font-size: 0.78rem;
    line-height: 1.4;
}
.focus-empty-card {
    padding: 1rem 1.1rem;
    margin-bottom: 1rem;
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 13px;
    background: #171A20;
    color: #9DA4AF;
}

.focus-change-card {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    align-items: center;
    gap: 1.2rem;
    margin: 0.35rem 0 1rem 0;
    padding: 1rem 1.1rem;
    border: 1px solid rgba(199,154,82,0.25);
    border-left: 3px solid #C79A52;
    border-radius: 15px;
    background:
        radial-gradient(circle at 90% 18%, rgba(199,154,82,0.18), transparent 34%),
        linear-gradient(145deg, #211F1B 0%, #17191F 72%);
    box-shadow: 0 10px 28px rgba(0,0,0,0.14);
}
.focus-change-label {
    color: #F1F3F6;
    font-size: 1rem;
    font-weight: 740;
}
.focus-change-meta {
    margin-top: 0.22rem;
    color: #8F97A4;
    font-size: 0.77rem;
}
.change-counts {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.65rem;
    min-width: 220px;
}
.change-counts > div {
    padding: 0.58rem 0.72rem;
    border-radius: 10px;
    background: #20242C;
}
.change-counts span {
    display: block;
    font-size: 1.55rem;
    font-weight: 780;
    line-height: 1;
}
.change-counts small {
    display: block;
    margin-top: 0.25rem;
    color: #9299A5;
    font-size: 0.73rem;
}
.change-up { color: #7AC28E; }
.change-down { color: #D37B7B; }

.ranking-callout {
    padding: 1.15rem 1.3rem;
    margin: 0.8rem 0 1.2rem 0;
    border-left: 3px solid var(--guild-accent);
    border-radius: 8px;
    background: linear-gradient(90deg, rgba(199,154,82,0.11), rgba(199,154,82,0.035));
}
.ranking-callout strong {
    font-size: 1.15rem;
}
.name-chip-wrap {
    display: flex;
    flex-wrap: wrap;
    gap: 0.45rem;
    margin: 0.75rem 0 1.2rem 0;
}
.name-chip {
    display: inline-block;
    padding: 0.34rem 0.62rem;
    border-radius: 999px;
    border: 1px solid var(--guild-border);
    background: var(--guild-panel);
    font-size: 0.88rem;
}


/* 區塊標題：比原生 H3 更像一般網站區段，也避免過度空白。 */
.section-heading {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    margin: 1.8rem 0 0.9rem 0;
}
.section-heading-line {
    width: 4px;
    height: 2.1rem;
    border-radius: 999px;
    background: linear-gradient(180deg, #E1B86F, #9F7337);
    box-shadow: 0 0 18px rgba(199,154,82,0.18);
}
.section-heading h2 {
    margin: 0;
    font-size: 1.38rem;
    line-height: 1.15;
    letter-spacing: -0.015em;
}
.section-heading span {
    display: block;
    margin-top: 0.2rem;
    color: var(--guild-text-soft);
    font-size: 0.86rem;
}

/* 首頁「本週焦點」是主要內容區段，層級比一般小節再高一級。 */
.section-heading.focus-main {
    margin-top: 2.35rem;
    margin-bottom: 1.15rem;
    padding: 0.15rem 0;
}
.section-heading.focus-main .section-heading-line {
    width: 5px;
    height: 3rem;
    background: linear-gradient(180deg, #F0C777 0%, #C08A3E 100%);
    box-shadow: 0 0 22px rgba(199,154,82,0.24);
}
.section-heading.focus-main h2 {
    font-size: clamp(1.65rem, 2.5vw, 2rem);
    font-weight: 800;
    letter-spacing: -0.025em;
}
.section-heading.focus-main span {
    margin-top: 0.3rem;
    font-size: 0.9rem;
    color: #AEB6C2;
}

/* 統計摘要：CSS grid 自動適應桌機 / 平板 / 手機，避免固定寬度卡片截字。 */
.stat-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 0.9rem;
    margin: 0.7rem 0 1rem 0;
}
.stat-grid:has(.stat-card:nth-child(3):last-child) {
    grid-template-columns: repeat(3, minmax(0, 1fr));
}
.stat-card {
    position: relative;
    overflow: hidden;
    min-width: 0;
    padding: 1.05rem 1.1rem 1rem 1.1rem;
    border: 1px solid rgba(255,255,255,0.11);
    border-radius: 14px;
    background: linear-gradient(145deg, #1B1F27 0%, #171A20 100%);
}
.stat-card::before {
    content: "";
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 3px;
    background: #737B88;
}
.stat-card.accent::before { background: #C79A52; }
.stat-card.blue::before { background: #5A8FC4; }
.stat-card.green::before { background: #65A57A; }
.stat-card.neutral::before { background: #7D8490; }
.stat-label {
    color: #C8CDD5;
    font-size: 0.82rem;
    font-weight: 650;
    letter-spacing: 0.02em;
}
.stat-value {
    margin: 0.42rem 0 0.35rem 0;
    color: #F4F1EA;
    font-size: clamp(1.45rem, 2.15vw, 2.05rem);
    font-weight: 720;
    line-height: 1.08;
    letter-spacing: -0.025em;
    overflow-wrap: anywhere;
}
.stat-meta {
    color: #9299A5;
    font-size: 0.8rem;
    line-height: 1.45;
}

.rank-context {
    display: grid;
    grid-template-columns: 1.1fr 1.45fr 1.45fr;
    gap: 0.5rem 1rem;
    padding: 0.78rem 1rem;
    margin: 0.45rem 0 1.2rem 0;
    border: 1px solid rgba(90,143,196,0.18);
    border-radius: 10px;
    background: rgba(90,143,196,0.055);
    color: #AEB4BE;
    font-size: 0.82rem;
}
.rank-context strong { color: #D8DDE5; }

/* 表格自己滾動，不把整頁一起帶走。 */
div[data-testid="stDataFrame"],
div[data-testid="stDataFrame"] * {
    overscroll-behavior: none !important;
}

@media (max-width: 768px) {
    .block-container {
        padding-top: 0.8rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    .st-key-mobile_nav {
        display: block !important;
        position: sticky;
        top: 0.35rem;
        z-index: 999;
        margin: 0 0 0.9rem 0;
        padding: 0.42rem;
        border: 1px solid rgba(255,255,255,0.12);
        border-radius: 13px;
        background: rgba(20,23,29,0.98);
        box-shadow: 0 10px 28px rgba(0,0,0,0.28);
        backdrop-filter: blur(10px);
    }
    .st-key-mobile_nav [data-testid="stColumn"] {
        min-width: 0 !important;
    }
    .st-key-mobile_nav a,
    .st-key-mobile_nav a * {
        color: #F2F4F7 !important;
        opacity: 1 !important;
        text-decoration: none !important;
    }
    .st-key-mobile_nav a {
        min-height: 46px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        padding: 0.55rem 0.2rem !important;
        border: 1px solid rgba(255,255,255,0.09) !important;
        border-radius: 9px !important;
        background: linear-gradient(180deg, #20252E 0%, #1A1E25 100%) !important;
        font-weight: 720 !important;
        font-size: 0.88rem !important;
    }
    .st-key-mobile_nav a:hover {
        border-color: rgba(199,154,82,0.42) !important;
        background: linear-gradient(180deg, #29271F 0%, #1C1E23 100%) !important;
    }
    .st-key-mobile_nav a[aria-current="page"],
    .st-key-mobile_nav a[data-active="true"] {
        border-color: rgba(225,184,111,0.62) !important;
        background: linear-gradient(180deg, rgba(199,154,82,0.28) 0%, rgba(199,154,82,0.10) 100%) !important;
        box-shadow: inset 0 -2px 0 #D6A95D !important;
    }
    .site-hero {
        padding: 1.55rem 1.25rem;
        border-radius: 14px;
    }
    .page-heading h1 { font-size: 1.7rem; }
    .site-hero p,
    .page-heading p { font-size: 0.92rem; }
    .stat-grid,
    .stat-grid:has(.stat-card:nth-child(3):last-child) {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .rank-context {
        grid-template-columns: 1fr;
    }
    .focus-card-grid {
        grid-template-columns: 1fr;
    }
    .focus-rank-card {
        min-height: 0;
    }
    .focus-rank-card:hover {
        transform: none;
    }
    .section-heading.focus-main {
        margin-top: 1.8rem;
    }
    .section-heading.focus-main h2 {
        font-size: 1.7rem;
    }
    .focus-change-card {
        grid-template-columns: 1fr;
        gap: 0.8rem;
    }
    .change-counts {
        min-width: 0;
    }
}

@media (max-width: 520px) {
    .stat-grid,
    .stat-grid:has(.stat-card:nth-child(3):last-child) {
        grid-template-columns: 1fr;
    }
    .stat-card { padding: 0.95rem 1rem; }
    .stat-value { font-size: 1.65rem; }
    .section-heading { margin-top: 1.45rem; }
    .focus-rank-card-value { font-size: 1.75rem; }
    .st-key-mobile_nav {
        border-radius: 10px;
        padding: 0.32rem;
    }
    .st-key-mobile_nav a {
        min-height: 43px !important;
        font-size: 0.82rem !important;
    }
    .section-heading.focus-main h2 { font-size: 1.62rem; }
}


/* ============================================================
   v9：統一自訂導覽 + 焦點標題 + 進步卡角色圖片
   ============================================================ */

/* 不再使用 Streamlit 原生 top navigation，改成頁內四格導覽。 */
.st-key-site_nav {
    display: block !important;
    position: relative !important;
    top: auto !important;
    z-index: auto !important;
    max-width: 760px;
    margin: 0 auto 1.35rem auto;
    padding: 0.42rem;
    border: 1px solid rgba(255,255,255,0.11);
    border-radius: 14px;
    background:
        radial-gradient(circle at 50% -40%, rgba(199,154,82,0.10), transparent 52%),
        linear-gradient(180deg, #191D24 0%, #15181E 100%);
    box-shadow: 0 10px 28px rgba(0,0,0,0.16);
}
.st-key-site_nav [data-testid="stHorizontalBlock"] {
    gap: 0.42rem !important;
}
.st-key-site_nav [data-testid="stColumn"] {
    min-width: 0 !important;
}
.st-key-site_nav a,
.st-key-site_nav a * {
    color: #E8EBF0 !important;
    opacity: 1 !important;
    text-decoration: none !important;
}
.st-key-site_nav a {
    min-height: 46px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    padding: 0.55rem 0.55rem !important;
    border: 1px solid transparent !important;
    border-radius: 10px !important;
    background: rgba(255,255,255,0.025) !important;
    font-weight: 720 !important;
    font-size: 0.9rem !important;
    transition: border-color 140ms ease, background 140ms ease, transform 140ms ease !important;
}
.st-key-site_nav a:hover {
    border-color: rgba(199,154,82,0.28) !important;
    background: rgba(199,154,82,0.08) !important;
    transform: translateY(-1px);
}
.st-key-site_nav a[aria-current="page"],
.st-key-site_nav a[data-active="true"] {
    color: #F3D59C !important;
    border-color: rgba(225,184,111,0.38) !important;
    background:
        radial-gradient(circle at 50% 0%, rgba(199,154,82,0.20), transparent 65%),
        rgba(199,154,82,0.075) !important;
    box-shadow: inset 0 -2px 0 #D6A95D !important;
}

/* 泛用區塊標題改用 div，避開瀏覽器 / Streamlit 對 h2 的樣式干擾。 */
.section-heading-title {
    margin: 0;
    color: #F2F4F7;
    font-size: 1.38rem !important;
    font-weight: 780 !important;
    line-height: 1.15 !important;
    letter-spacing: -0.02em;
}
.section-heading-kicker {
    margin-bottom: 0.28rem;
    color: #D9AE66;
    font-size: 0.69rem;
    font-weight: 800;
    letter-spacing: 0.14em;
}
.section-heading.focus-main {
    position: relative;
    overflow: hidden;
    gap: 1rem;
    margin-top: 2.45rem;
    margin-bottom: 1.2rem;
    padding: 1.05rem 1.2rem;
    border: 1px solid rgba(199,154,82,0.20);
    border-radius: 15px;
    background:
        radial-gradient(circle at 92% 0%, rgba(199,154,82,0.16), transparent 36%),
        linear-gradient(135deg, rgba(32,31,28,0.94), rgba(21,24,30,0.94));
}
.section-heading.focus-main .section-heading-line {
    width: 5px;
    height: 4.2rem;
    flex: 0 0 5px;
    background: linear-gradient(180deg, #F0C777 0%, #C08A3E 100%);
}
.section-heading.focus-main .section-heading-title {
    color: #F7F3EA !important;
    font-size: clamp(2rem, 3vw, 2.45rem) !important;
    font-weight: 840 !important;
    line-height: 1.05 !important;
}
.section-heading.focus-main span {
    margin-top: 0.42rem;
    color: #AEB6C2;
    font-size: 0.9rem;
}

/* 進步卡：角色圖填補右側留白，仍以文字為主體。 */
.focus-rank-card.has-character {
    padding-right: 7.5rem;
}
.focus-character {
    position: absolute;
    right: 0.35rem;
    bottom: 0;
    width: 7rem;
    height: 9.2rem;
    display: flex;
    align-items: flex-end;
    justify-content: center;
    z-index: 1;
    pointer-events: none;
}
.focus-character::before {
    content: "";
    position: absolute;
    right: 0.45rem;
    bottom: 0.75rem;
    width: 5.8rem;
    height: 5.8rem;
    border-radius: 50%;
    filter: blur(18px);
    opacity: 0.48;
}
.focus-character.growth::before { background: rgba(101,165,122,0.42); }
.focus-character.ratio::before { background: rgba(124,143,208,0.44); }
.focus-character img {
    position: relative;
    z-index: 2;
    max-width: 6.8rem;
    max-height: 8.8rem;
    object-fit: contain;
    object-position: center bottom;
    filter: drop-shadow(0 8px 14px rgba(0,0,0,0.38));
}
.focus-rank-card.has-character .focus-rank-card-name,
.focus-rank-card.has-character .focus-rank-card-job,
.focus-rank-card.has-character .focus-rank-card-value,
.focus-rank-card.has-character .focus-rank-card-meta,
.focus-rank-card.has-character .focus-rank-card-top {
    position: relative;
    z-index: 3;
}

@media (max-width: 768px) {
    .block-container {
        padding-top: 0.65rem;
    }
    .st-key-site_nav {
        position: relative !important;
        top: auto !important;
        z-index: auto !important;
        max-width: none;
        margin: 0 0 0.9rem 0;
        padding: 0.34rem;
        border-radius: 11px;
        box-shadow: none;
    }
    .st-key-site_nav [data-testid="stHorizontalBlock"] {
        gap: 0.28rem !important;
    }
    .st-key-site_nav a {
        min-height: 44px !important;
        padding: 0.45rem 0.15rem !important;
        font-size: 0.79rem !important;
    }
    .section-heading.focus-main {
        margin-top: 1.8rem;
        padding: 0.95rem 1rem;
    }
    .section-heading.focus-main .section-heading-line {
        height: 3.7rem;
    }
    .section-heading.focus-main .section-heading-title {
        font-size: 1.9rem !important;
    }
    .focus-rank-card.has-character {
        padding-right: 6.7rem;
        min-height: 185px;
    }
    .focus-character {
        right: 0.25rem;
        width: 6.3rem;
        height: 8.5rem;
    }
    .focus-character img {
        max-width: 6rem;
        max-height: 8rem;
    }
}

@media (max-width: 520px) {
    .st-key-site_nav a {
        min-height: 42px !important;
        font-size: 0.72rem !important;
        gap: 0.15rem !important;
    }
    .section-heading.focus-main .section-heading-title {
        font-size: 1.78rem !important;
    }
    .section-heading.focus-main span {
        font-size: 0.8rem;
        line-height: 1.45;
    }
    .focus-rank-card.has-character {
        padding-right: 6.2rem;
    }
    .focus-character {
        width: 5.9rem;
        height: 8rem;
    }
    .focus-character img {
        max-width: 5.6rem;
        max-height: 7.5rem;
    }
}


/* v10：導覽改用原生 button，避免 page_link 在手機內嵌檢視中變成深色文字。 */
.st-key-site_nav [data-testid="stButton"] button {
    min-height: 48px !important;
    width: 100% !important;
    border-radius: 11px !important;
    font-weight: 760 !important;
    font-size: 0.90rem !important;
    color: #F4F5F7 !important;
    box-shadow: none !important;
}
.st-key-site_nav [data-testid="stButton"] button * {
    color: inherit !important;
    opacity: 1 !important;
}
.st-key-site_nav [data-testid="stBaseButton-secondary"] {
    background: #1A1E26 !important;
    border-color: rgba(255,255,255,0.13) !important;
}
.st-key-site_nav [data-testid="stBaseButton-secondary"]:hover {
    background: #20252E !important;
    border-color: rgba(199,154,82,0.34) !important;
}
.st-key-site_nav [data-testid="stBaseButton-primary"] {
    background: linear-gradient(135deg, #B9863E 0%, #8D632D 100%) !important;
    border-color: #D2A356 !important;
    color: #FFFFFF !important;
}

@media (max-width: 768px) {
    .st-key-site_nav {
        margin-top: 0 !important;
        margin-bottom: 0.85rem !important;
        padding: 0.32rem !important;
        background: #151820 !important;
        border: 1px solid rgba(255,255,255,0.12) !important;
    }
    .st-key-site_nav [data-testid="stButton"] button {
        min-height: 46px !important;
        padding: 0.42rem 0.18rem !important;
        font-size: 0.78rem !important;
    }
}

@media (max-width: 520px) {
    .st-key-site_nav [data-testid="stButton"] button {
        min-height: 44px !important;
        padding: 0.38rem 0.08rem !important;
        font-size: 0.72rem !important;
    }
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
