import re
from typing import Literal

from bs4 import BeautifulSoup, Tag

from constants import ODDS_REGEX
from exceptions import (
    InvalidOddsFormatException,
    InvalidScoreSumError,
    SoupNoSuchElementException,
)

# Input: bs object or a tag and match_id for exception logging
# Validation of scraped data
# Output: dictionary
# Functions' name: get_<something>


def get_initial_odds(el: BeautifulSoup | Tag, match_id: str) -> dict:
    """
    Returns a dict of initial odds for both teams to win in format:

    Raises:

    SoupNoSuchElementError - if element containing the odds cannot be found
    InvalidOddsFormatError - if odds do not follow XX.XX format

    """

    home_team_win_initial_odds = el.select_one("#sp_2_8_1_1")
    away_team_win_initial_odds = el.select_one("#sp_2_8_3_1")

    if home_team_win_initial_odds is None or away_team_win_initial_odds is None:
        raise SoupNoSuchElementException(
            f"Couldn't find the initial odds for match {match_id} ."
        )

    home_team_win_initial_odds = home_team_win_initial_odds.text.strip()
    away_team_win_initial_odds = away_team_win_initial_odds.text.strip()

    if (
        re.match(ODDS_REGEX, home_team_win_initial_odds) is None
        or re.match(ODDS_REGEX, away_team_win_initial_odds) is None
    ):
        raise InvalidOddsFormatException(
            f"Couldn't find the initial odds for match {match_id} ."
        )

    return {
        "home_team_win_initial_odds": home_team_win_initial_odds,
        "away_team_win_initial_odds": away_team_win_initial_odds,
    }


def get_updated_odds(el: BeautifulSoup | Tag, match_id: str) -> dict:
    """
    Returns a dict of updated (final) odds for both teams to win in format:

    Raises:

    SoupNoSuchElementError - if element containing the odds cannot be found
    InvalidOddsFormatError - if odds do not follow XX.XX format

    """

    home_team_win_updated_odds = el.select_one("#sp_2_8_1_2")
    away_team_win_updated_odds = el.select_one("#sp_2_8_3_2")

    if home_team_win_updated_odds is None or away_team_win_updated_odds is None:
        raise SoupNoSuchElementException(
            f"Couldn't find the updated odds for match {match_id} ."
        )

    home_team_win_updated_odds = home_team_win_updated_odds.text.strip()
    away_team_win_updated_odds = away_team_win_updated_odds.text.strip()

    if (
        re.match(ODDS_REGEX, home_team_win_updated_odds) is None
        or re.match(ODDS_REGEX, away_team_win_updated_odds) is None
    ):
        raise ValueError(f"Couldn't find the updated odds for match {match_id} .")

    return {
        "home_team_win_updated_odds": home_team_win_updated_odds,
        "away_team_win_updated_odds": away_team_win_updated_odds,
    }


def get_current_match_goals(el: BeautifulSoup, match_id: str) -> dict:
    first_half_score = el.select_one(
        "#mScore > div > div:nth-child(2) > span > span:nth-child(1)"
    )
    second_half_score = el.select_one(
        "#mScore > div > div:nth-child(2) > span > span:nth-child(2)"
    )
    if first_half_score is None or second_half_score is None:
        raise SoupNoSuchElementException(
            f"Couldn't find the score for match {match_id}."
        )

    first_half_score = first_half_score.text.strip()
    second_half_score = second_half_score.text.strip()

    score_regex = r"\d{1,2}-\d{1,2}"

    if (
        re.match(score_regex, first_half_score) is None
        or re.match(score_regex, second_half_score) is None
    ):
        raise ValueError(f"Couldn't find the score for match {match_id} .")

    first_team_first_half_goals, second_team_first_half_goals = map(
        int, first_half_score.split("-")
    )
    first_team_second_half_goals, second_team_second_half_goals = map(
        int, second_half_score.split("-")
    )

    first_team_final_goals = el.select_one("#mScore > div > div:nth-child(1)")
    second_team_final_goals = el.select_one("#mScore > div > div:nth-child(3)")

    if first_team_final_goals is None or second_team_final_goals is None:
        raise SoupNoSuchElementException(
            f"Couldn't find the score for match {match_id} ."
        )

    first_team_final_goals = int(first_team_final_goals.text.strip())
    second_team_final_goals = int(second_team_final_goals.text.strip())

    if (
        first_team_first_half_goals + first_team_second_half_goals
    ) != first_team_final_goals or (
        second_team_first_half_goals + second_team_second_half_goals
    ) != second_team_final_goals:
        raise InvalidScoreSumError(f"Scores are wrong for match {match_id} .")

    return {
        "first_team_final_goals": first_team_final_goals,
        "second_team_final_goals": second_team_final_goals,
        "first_team_first_half_goals": first_team_first_half_goals,
        "second_team_first_half_goals": second_team_first_half_goals,
        "first_team_second_half_goals": first_team_second_half_goals,
        "second_team_second_half_goals": second_team_second_half_goals,
    }


def get_teams_names(el: BeautifulSoup, match_id: str) -> dict:

    # TODO: When getting the names directly from the match page itself we CANNOT retrieve the
    # information is first team playing at neutral enviorment (N).

    first_team_name = el.select_one("#fbheader > div:nth-child(2) > div.home > div")
    second_team_name = el.select_one("#fbheader > div:nth-child(2) > div.guest > div")

    if first_team_name is None or second_team_name is None:
        raise SoupNoSuchElementException(
            f"Cannot find teams' names for match {match_id} ."
        )

    first_team_name = first_team_name.text.strip()
    second_team_name = second_team_name.text.strip()

    return {
        "first_team_name": first_team_name,
        "second_team_name": second_team_name,
    }


def get_head_to_head_information(el: BeautifulSoup, match_id: str) -> dict:

    head_to_head_matches_divs = el.select("#dv_head_to_head tr")[
        1:7
    ]  # TODO: Fix bug when removing [1:7], duplicate first match

    head_to_head_matches: list[dict[str, str]] = []
    for div in head_to_head_matches_divs:

        date_el = div.select_one(".txt-l-pl.time > span")
        half_time_score_el = div.select_one(".htScore")
        full_time_score_el = div.select_one(".glove.ftScore")

        if date_el is None or half_time_score_el is None or full_time_score_el is None:
            # TODO: They all should exists. Should raise exception
            continue

        match_data = {
            "date": date_el.text.strip(),
            "half_time_score": "-".join(
                [
                    score.strip("\n").strip()
                    for score in (half_time_score_el.text.strip().split("-"))
                ]
            ),
            "full_time_score": "-".join(
                [
                    score.strip("\n").strip()
                    for score in (full_time_score_el.text.strip().split("-"))
                ]
            ),
        }

        head_to_head_matches.append(match_data)

    filtered_head_to_head_matches = [
        match for match in head_to_head_matches if match["date"][-2:] >= "22"
    ]

    last5_head_to_head_matches = filtered_head_to_head_matches[:5]
    last5_head_to_head_matches_scores = dict()
    last5_head_to_head_matches_len = len(last5_head_to_head_matches)

    for i in range(0, 5):
        match = (
            last5_head_to_head_matches[i] if i < last5_head_to_head_matches_len else {}
        )

        last5_head_to_head_matches_scores[
            f"last{i+1}_head_to_head_match_half_time_score"
        ] = match.get("half_time_score")

        last5_head_to_head_matches_scores[
            f"last{i+1}_head_to_head_match_full_time_score"
        ] = match.get("full_time_score")

    return last5_head_to_head_matches_scores


def get_team_games_information(
    el: BeautifulSoup, match_id: str, mode: Literal["home", "away"]
) -> dict:

    if mode == "home":
        selector = "#tb_home_recent div.corteam"
    elif mode == "away":
        selector = "#tb_guest_recent div.corteam"

    last10_matches_divs = el.select(selector)
    last5_matches_divs = last10_matches_divs[:5]

    result = dict()

    for i, match_div in enumerate(last5_matches_divs):

        full_time_score_div = match_div.select_one("div:nth-child(3)")
        half_time_score_div = match_div.select_one("div:nth-child(4)")

        if not full_time_score_div or not half_time_score_div:

            raise SoupNoSuchElementException(
                f"No half/full time score found for match {match_id} last {i+1}th {mode} match."
            )

        half_time_score = "-".join(
            [span.text for span in half_time_score_div.select("span.htScore")]
        )
        full_time_score = "-".join(
            [span.text for span in full_time_score_div.select("span.ftScore")]
        )

        result[f"last{i+1}_{mode}_match_half_time_score"] = half_time_score
        result[f"last{i+1}_{mode}_match_full_time_score"] = full_time_score

    return result
