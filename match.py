from pydantic import BaseModel, computed_field, field_validator, model_validator
from typing_extensions import Self


class Match(BaseModel):
    # Match metadata
    league_name: str
    year: int
    period: str
    stage: str
    round: int
    id: str
    date: str
    first_team_name: str
    second_team_name: str

    # Match position in round
    is_first_match_in_round: bool
    is_before_last_match_in_round: bool
    is_last_match_in_round: bool

    # Odds
    odds_company: str
    home_team_win_initial_odds: float | None
    draw_initial_odds: float | None
    away_team_win_initial_odds: float | None

    @computed_field
    @property
    def has_odds(self) -> bool:
        return all(
            [
                bool(self.home_team_win_initial_odds),
                bool(self.draw_initial_odds),
                bool(self.away_team_win_initial_odds),
            ]
        )

    # Teams positions
    first_team_position: int | str
    second_team_position: int | str

    # Goals statistics
    first_team_final_goals: int
    second_team_final_goals: int
    first_team_first_half_goals: int
    second_team_first_half_goals: int

    @field_validator(
        "league_name",
        "period",
        "stage",
        "id",
        "date",
        "first_team_name",
        "second_team_name",
        "odds_company",
        "first_team_position",
        "second_team_position",
        mode="before",
    )
    @classmethod
    def strip_strings(cls, v) -> str:
        return v.strip() if isinstance(v, str) else v

    @field_validator("id")
    @classmethod
    def check_id_length(cls, v) -> str:
        if len(v) != 7:
            raise ValueError("id is not 7 characters long")

        return v

    @model_validator(mode="after")
    def check_match_position(self) -> Self:
        if (
            sum(
                [
                    self.is_first_match_in_round,
                    self.is_before_last_match_in_round,
                    self.is_last_match_in_round,
                ]
            )
            <= 1
        ):
            raise ValueError

        return self

    @computed_field
    @property
    def is_match_7plus(self) -> bool:
        return self.first_team_final_goals + self.second_team_final_goals >= 7

    @computed_field
    @property
    def is_match_transition(self) -> bool:
        first_team_win_by_transition = (
            self.first_team_first_half_goals < self.second_team_first_half_goals
            and self.first_team_final_goals > self.second_team_final_goals
        )
        second_team_win_by_transition = (
            self.first_team_first_half_goals > self.second_team_first_half_goals
            and self.first_team_final_goals < self.second_team_final_goals
        )
        return first_team_win_by_transition or second_team_win_by_transition
