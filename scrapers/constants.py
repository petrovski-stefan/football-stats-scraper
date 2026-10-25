"""Scraper-internal constants: nowgoal DOM selectors, page URLs, robots.txt rules, and
the team-name transliteration table.

The CSV column order is a contract shared with the feature layer, so it sits in
`domain/columns.py`; nothing outside `scrapers/` needs a CSS selector.
"""

from datetime import timedelta, timezone

# nowgoal often moves to a new domain or subdomain, and the old host answers 301 to the new
# one; the paths, the ids and the page structure stay the same (scrapers/CLAUDE.md). So the
# hosts live here only: a move changes these three lines and the URLs of config/leagues.json.
SITE = "nowgoal50.com"
LEAGUE_HOST = f"football.{SITE}"  # the league pages
MATCH_HOST = f"live.{SITE}"  # the h2h and live pages of a match

# The robots.txt `Disallow` rules of every host the scraper may open, copied from the files
# the user read in a browser on 2026-10-02, and confirmed unchanged on the new hosts by the
# user on 2026-10-20 (the reason for the rule: scrapers/CLAUDE.md). Each rule is a
# case-sensitive path prefix, as in robots.txt. `scrapers.driver.open_page` refuses a URL on
# any host missing here, and any path that starts with one of its host's rules.
ROBOTS_DISALLOW: dict[str, tuple[str, ...]] = {
    LEAGUE_HOST: ("/Scripts/", "/en/"),
    MATCH_HOST: (
        "/bin/",
        "/ajax/",
        "/Ajax/",
        "/home/ajax/",
        "/Home/Ajax/",
        "/gf/",
        "/soccer/flashLive/",
        "/textlive/",
        "/Scripts/",
        "/scripts/",
        "/match/information-",
    ),
}


# --- nowgoal league page selectors -------------------------------------------
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
# The row's other cells, relative to it.
ROW_FT_SCORE = "span.score"
ROW_HT_SCORE = "span.ht"
ROW_HOME_TEAM = "span.home span[onclick]"
ROW_AWAY_TEAM = "span.away span[onclick]"
ROW_DATE = "span.date"
# The clock of the row's `span.date[data-t]` kickoff: UTC+8 (China time), no offset written.
# Verified 2026-10-05 on two EPL kickoffs, one in winter and one in summer (UK clocks
# differ, the +8 does not). `parsers.parse_kickoff` converts it to Berlin time.
LEAGUE_PAGE_CLOCK = timezone(timedelta(hours=8))

# Standings section
# The standings table has its own sub-table picker, one entry per stage
# (`data-s-sub` = the stage tab's `stage` id). It does NOT follow the stage tabs and
# defaults to the latest sub-table, so it is synced per stage. `#standingBox` carries the
# shown sub-table's id in `data-st-sub`; picking a sub-table resets its round to "Total".
SUB_STANDING_ITEM = "div#standingPlates #subStandingBox li[data-s-sub='{stage}']"
STANDING_BOX = "div#standingPlates #standingBox"
STANDING_BOX_LABEL = "div#standingPlates #standingBox > text"
# The dropdown's `Total` entry: the table as it stands now. Matched by its text, since the
# round entries carry `data-st-r=<n>` and `Total` is the one that reads "Total".
STANDING_TOTAL_LABEL = "Total"
STANDING_TOTAL_ITEM = (
    "//div[@id='standingPlates']//*[@id='standingBox']//li[normalize-space(.)='Total']"
)
STANDING_ROWS = "div#standingPlates ul#standingList li.standlis"
# The title row above them: R, Team, P, W, D, L, GD, PTS (measured 2026-10-06).
STANDING_TITLE_ROW = "div#standingPlates ul#standingList li.title"
# A standings row's team name, inside its team cell.
STANDING_TEAM_NAME = "span.name"


# --- Detail page (MATCH_HOST/match/h2h-<id>) ----------------------------------
# Detail page uses the same match id as the schedule row's @matchid.
DETAIL_URL = f"https://{MATCH_HOST}/match/h2h-{{match_id}}"
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
# --- Live page (MATCH_HOST/match/live-<id>) -----------------------------------
# Goal timings live here, NOT on the h2h detail page. Same match id.
LIVE_URL = f"https://{MATCH_HOST}/match/live-{{match_id}}"
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
