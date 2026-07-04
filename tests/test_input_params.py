import pytest

from GPTProfiles import PlayerType
from InputParams import InputParams


def _player_types(count: int) -> list[PlayerType]:
    return list(PlayerType)[:count]


def test_validate_accepts_valid_input() -> None:
    params = InputParams(5, _player_types(4), mafiaCount=1)
    params.validate()


def test_validate_rejects_duplicate_player_types() -> None:
    duplicate_types = [
        PlayerType.Default_Derrick,
        PlayerType.Refined_Reginald,
        PlayerType.Default_Derrick,
        PlayerType.Shifty_Shelby,
    ]
    params = InputParams(5, duplicate_types, mafiaCount=1)

    with pytest.raises(ValueError, match="Duplicate player types"):
        params.validate()


def test_validate_rejects_player_count_mismatch() -> None:
    params = InputParams(6, _player_types(4), mafiaCount=1)

    with pytest.raises(ValueError, match="Player count does not match"):
        params.validate()


def test_validate_rejects_when_mafia_is_half_or_more() -> None:
    params = InputParams(7, _player_types(6), mafiaCount=3)

    with pytest.raises(ValueError, match="Number of Mafia must be less than half"):
        params.validate()


def test_validate_rejects_when_special_roles_not_less_than_players() -> None:
    params = InputParams(4, _player_types(3), mafiaCount=2)

    with pytest.raises(
        ValueError,
        match="Total number of special roles must be less than the total number of players",
    ):
        params.validate()
