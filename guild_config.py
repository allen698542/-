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

/* 頁內手機導覽：桌機隱藏，手機再顯示。 */
.st-key-mobile_nav {
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
    border-radius: 15px;
    background: linear-gradient(145deg, #1B1F27 0%, #15181E 100%);
    box-shadow: 0 8px 28px rgba(0,0,0,0.14);
}
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
    background: rgba(90,143,196,0.13);
    color: #B6CEE6;
    font-size: 0.73rem;
    font-weight: 750;
}
.focus-rank-card.growth .focus-rank-badge {
    background: rgba(101,165,122,0.13);
    color: #A9D4B6;
}
.focus-rank-card.ratio .focus-rank-badge {
    background: rgba(124,143,208,0.14);
    color: #BDC7EC;
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
    border: 1px solid rgba(199,154,82,0.18);
    border-left: 3px solid #C79A52;
    border-radius: 14px;
    background: linear-gradient(145deg, #1B1E24, #16191F);
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
        padding: 0.4rem 0.45rem;
        border: 1px solid rgba(255,255,255,0.10);
        border-radius: 12px;
        background: rgba(23,26,32,0.96);
        box-shadow: 0 8px 26px rgba(0,0,0,0.24);
        backdrop-filter: blur(8px);
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
        padding: 0.32rem 0.35rem;
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
