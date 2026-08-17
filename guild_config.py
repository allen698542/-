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

.ranking-callout {
    padding: 1.15rem 1.3rem;
    margin: 0.8rem 0 1.2rem 0;
    border-left: 3px solid var(--guild-accent);
    border-radius: 8px;
    background: rgba(199,154,82,0.08);
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

/* 表格自己滾動，不把整頁一起帶走。 */
div[data-testid="stDataFrame"],
div[data-testid="stDataFrame"] * {
    overscroll-behavior: none !important;
}

/* 不顯示空的 sidebar；主選單改由 st.navigation(position="top") 負責。 */
section[data-testid="stSidebar"] {
    display: none;
}

@media (max-width: 768px) {
    .block-container {
        padding-top: 1.2rem;
        padding-left: 1rem;
        padding-right: 1rem;
    }
    .site-hero {
        padding: 1.55rem 1.25rem;
        border-radius: 14px;
    }
    .page-heading h1 { font-size: 1.7rem; }
    .site-hero p,
    .page-heading p { font-size: 0.92rem; }
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
