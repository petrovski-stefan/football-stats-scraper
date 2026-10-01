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
# Stage tabs ("League", "Group A", "Apertura"...). Absent on single-table pages. Every
# round-bearing stage's round spans sit in the DOM at once, tagged `stage=<id>`, with the
# inactive stages' spans hidden — so a round selector must be scoped to its stage.
STAGE_SPANS = "div#schedule div.stage span[stage]"
STAGE_SPAN = "div#schedule div.stage span[stage='{stage}']"
STAGE_ACTIVE_CLASS = "on"  # the shown stage gets 'on'; the live one is 'current on'
ROUND_SPANS = "div#schedule div.round span[round]"
ROUND_SPAN = "div#schedule div.round span[round='{round}']"
STAGE_ROUND_SPANS = "div#schedule div.round span[stage='{stage}'][round]"
STAGE_ROUND_SPAN = "div#schedule div.round span[stage='{stage}'][round='{round}']"
ROUND_ACTIVE_CLASS = "on"  # clicked round gets 'on'; the live round is 'current on'
ROUND_CURRENT_CLASS = "current"
SCHEDULE_ROWS = "div#schedule div.list div.schedulis"

# Odds-type selector in the schedule header. Three types share one three-cell column;
# only the header label and the middle cell's meaning change. The page defaults to AH.
ODDS_SELECTBOX = "#schedule > div.list > div.title > span.odds.selectbox"
ODDS_LABEL = ODDS_SELECTBOX + " > text"
ODDS_TYPE_ITEM = ODDS_SELECTBOX + " li[type='{kind}']"
# our name -> (DOM `type` attribute, header label once the switch lands)
ODDS_TYPES = {
    "1x2": ("O", "1X2"),  # cells: home / draw / away
    "ah": ("L", "AH"),  # cells: home / handicap line / away
    "ou": ("T", "OU"),  # cells: over / goal line / under
}
ROW_ODDS_CELLS = "span.odds > span"  # relative to a schedule row; always three cells

# Standings section
# The standings table has its own sub-table picker, one entry per stage
# (`data-s-sub` = the stage tab's `stage` id). It does NOT follow the stage tabs and
# defaults to the latest sub-table, so it is synced per stage. `#standingBox` carries the
# shown sub-table's id in `data-st-sub`; picking a sub-table resets its round to "Total".
SUB_STANDING_ITEM = "div#standingPlates #subStandingBox li[data-s-sub='{stage}']"
STANDING_BOX = "div#standingPlates #standingBox"
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
# Each history row carries the referenced match's own id and league id as attributes.
# These are what make the `*_lastN_*` blocks joinable to anything else — without them a
# history row is an orphan, which is why goal timings could not be fetched for it.
HIST_MATCH_ID_ATTR = "index"  # e.g. index="2789495"
HIST_LEAGUE_ID_ATTR = "name"  # e.g. name="36" (36 = EPL, 90 = FA Cup)
HIST_TEAM_LINKS = "a[onclick^='soccerDbPage.team']"  # [0]=home, [1]=away
# Score span class is indexed per table (fscore_1/_2/_3), so match on prefix.
HIST_FT_SCORE = "span[class^='fscore']"  # e.g. "3-2"
HIST_HT_SCORE = "span[class^='hscore']"  # e.g. "(1-2)"
# Live Odds Comparison: one bookmaker spans Initial/Live/In-Play rows; 1X2 cells carry data-e="1".
DETAIL_ODDS_TABLE_CANDIDATES = "table.team-table-other"
DETAIL_ODDS_1X2_CELLS = "td[data-e='1']"  # 3 per row: home / draw / away
PREFERRED_BOOKMAKER = "Bet365"
# --- Live page (live10.nowgoal26.com/match/live-<id>) -------------------------
# Goal timings live here, NOT on the h2h detail page. Same match id.
LIVE_URL = "https://live10.nowgoal26.com/match/live-{match_id}"
# Events are table rows; the minute sits in a `b.score` cell as "33'", "45+3'", "90+8'".
LIVE_EVENT_MINUTE = "b.score"
LIVE_EVENT_ROW = "tr"
# Icons label the event via their `alt`, which is authoritative: "Goal",
# "Penalty Scored", "VAR", "Yellow Card", "Red Card", "Substitution"...
# Goals are NOT detected by icon — a penalty carries a different one and would be missed.
# They are detected by the running score in the row text; VAR rows never carry one.
LIVE_EVENT_ICON = "img"

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
