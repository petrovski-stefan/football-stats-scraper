"""Scraper-internal constants: nowgoal26 DOM selectors, user agents, and the
team-name transliteration table.

The CSV output schema that used to live here alongside these now sits in
`domain/columns.py` — it is a contract shared with the feature layer, whereas
nothing outside `scrapers/` has any business knowing a CSS selector.
"""

AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.1 Safari/605.1.15",
]


# --- nowgoal26 league page selectors -----------------------------------------
# Schedule section
ROUND_SPANS = "div#schedule div.round span[round]"
ROUND_SPAN = "div#schedule div.round span[round='{round}']"
ROUND_ACTIVE_CLASS = "on"  # clicked round gets 'on'; the live round is 'current on'
ROUND_CURRENT_CLASS = "current"
SCHEDULE_ROWS = "div#schedule div.list div.schedulis"

# Odds-type selector in the schedule header (AH / 1X2 / OU). We switch it to 1X2.
ODDS_SELECTBOX = "#schedule > div.list > div.title > span.odds.selectbox"
ODDS_LABEL = ODDS_SELECTBOX + " > text"
ODDS_1X2_ITEM = ODDS_SELECTBOX + " li[type='O']"  # 1X2 option
ODDS_1X2_LABEL = "1X2"
ROW_ODDS_CELLS = "span.odds > span"  # relative to a schedule row: home / draw / away

# Standings section
STANDING_BOX_LABEL = "div#standingPlates #standingBox > text"
STANDING_ROUND_ITEM = "div#standingPlates #standingBox li[data-st-r='{round}']"
STANDING_ROWS = "div#standingPlates ul#standingList li.standlis"


# --- Detail page (live10.nowgoal26.com/match/h2h-<id>) ------------------------
# Detail page uses the same match id as the schedule row's @matchid.
DETAIL_URL = "https://live10.nowgoal26.com/match/h2h-{match_id}"
# Head-to-head widget tables: v1 = home team's recent, v2 = away team's recent, v3 = H2H.
DETAIL_HOME_RECENT_ROWS = "tr[id^='tr1_']"
DETAIL_AWAY_RECENT_ROWS = "tr[id^='tr2_']"
DETAIL_H2H_ROWS = "tr[id^='tr3_']"
DETAIL_V3_TABLE = "table#table_v3"  # presence marks the widget as rendered
# History-row cells (shared by v1/v2/v3 rows). Positional layout: 0=league 1=date
# 2=home 3=score"FT (HT)" 4=away 5=corner"FT (HT)" 6/7/8 = 1X2 home/draw/away odds.
HIST_LEAGUE_TD = 0
HIST_CORNER_TD = 5
HIST_ODDS_TDS = (6, 7, 8)
HIST_DATE = "span[name='timeData']"
HIST_TEAM_LINKS = "a[onclick^='soccerDbPage.team']"  # [0]=home, [1]=away
# Score span class is indexed per table (fscore_1/_2/_3), so match on prefix.
HIST_FT_SCORE = "span[class^='fscore']"  # e.g. "3-2"
HIST_HT_SCORE = "span[class^='hscore']"  # e.g. "(1-2)"
# Live Odds Comparison: one bookmaker spans Initial/Live/In-Play rows; 1X2 cells carry data-e="1".
DETAIL_ODDS_TABLE_CANDIDATES = "table.team-table-other"
DETAIL_ODDS_1X2_CELLS = "td[data-e='1']"  # 3 per row: home / draw / away
PREFERRED_BOOKMAKER = "Bet365"
# Other analysis blocks.
DETAIL_STRENGTH_BLOCK = "[class*='strength']"
DETAIL_H2H_COMPARE_BAR = ".fx-tb-title"
DETAIL_GUESS_BOX = "div.guessingbox"
# The "Fixture" widget holds two tables inside one div.team-div: the home team's
# upcoming matches (table.team-table-home) and the away team's (table.team-table-guest),
# each ordered soonest-first with a "N Days" countdown column.
DETAIL_FIXTURE_HOME = "table.team-table-home"
DETAIL_FIXTURE_AWAY = "table.team-table-guest"


# Portuguese (and other accented) letters -> ASCII, for clean CSV/team names.
PORTUGUESE_TO_ENGLISH_LETTERS = {
    # uppercase
    "Á": "A",
    "É": "E",
    "Í": "I",
    "Ó": "O",
    "Ú": "U",
    "Â": "A",
    "Ê": "E",
    "Ô": "O",
    "Ã": "A",
    "Õ": "O",
    "À": "A",
    "Ü": "U",
    "Ç": "C",
    # lowercase
    "ç": "c",
    "á": "a",
    "é": "e",
    "í": "i",
    "ó": "o",
    "ú": "u",
    "â": "a",
    "ê": "e",
    "ô": "o",
    "ã": "a",
    "õ": "o",
    "à": "a",
    "ò": "o",
    "è": "e",
    "ì": "i",
    "ù": "u",
}
