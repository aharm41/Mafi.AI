import pytest

from GPTProfiles import PlayerType
from InputParams import InputParams


def _player_types(count: int) -> list[PlayerType]:
    return list(PlayerType)[:count]


def _params(
    player_count: int,
    player_types: list[PlayerType],
    mafia_count: int,
) -> InputParams:
    return InputParams(
        playerCount=player_count,
        humanPlayers={"player:test:host": "Host"},
        playerTypes=player_types,
        mafiaCount=mafia_count,
        broadcastDest="game:test",
    )


def test_validate_accepts_valid_input() -> None:
    _params(5, _player_types(4), mafia_count=1).validate()


def test_validate_rejects_duplicate_player_types() -> None:
    duplicate_types = [
        PlayerType.Default_Derrick,
        PlayerType.Refined_Reginald,
        PlayerType.Default_Derrick,
        PlayerType.Shifty_Shelby,
    ]
    params = _params(5, duplicate_types, mafia_count=1)

    with pytest.raises(ValueError, match="Duplicate player types"):
        params.validate()


def test_validate_rejects_player_count_mismatch() -> None:
    params = _params(6, _player_types(4), mafia_count=1)

    with pytest.raises(ValueError, match="Player count does not match"):
        params.validate()


def test_validate_rejects_when_mafia_is_half_or_more() -> None:
    params = _params(7, _player_types(6), mafia_count=3)

    with pytest.raises(ValueError, match="Number of Mafia must be less than half"):
        params.validate()


def test_validate_rejects_when_special_roles_not_less_than_players() -> None:
    params = _params(4, _player_types(3), mafia_count=2)

    with pytest.raises(
        ValueError,
        match="Total number of special roles must be less than the total number of players",
    ):
        params.validate()
