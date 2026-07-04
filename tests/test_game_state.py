import pytest

from GameState import GameState, PlayerNotFoundError
from Player import Player
from PlayerRoles import PlayerRole


def _build_state() -> tuple[GameState, dict[str, Player]]:
    mafia = Player("Mafia One", role=PlayerRole.MAFIA)
    sheriff = Player("Sheriff Sue", role=PlayerRole.SHERIFF)
    doctor = Player("Doctor Dan", role=PlayerRole.DOCTOR)
    innocent = Player("Innocent Ivy", role=PlayerRole.INNOCENT)

    players = [mafia, sheriff, doctor, innocent]
    state = GameState(
        players=players,
        innocents=[sheriff, doctor, innocent],
        mafias=[mafia],
        sheriff=sheriff,
        doctor=doctor,
        wsPlayers=[],
    )
    return state, {
        "mafia": mafia,
        "sheriff": sheriff,
        "doctor": doctor,
        "innocent": innocent,
    }


def test_kill_player_updates_role_lists_and_death_flags() -> None:
    state, players = _build_state()

    state.killPlayer(players["sheriff"])

    assert players["sheriff"] not in state.getAlivePlayers()
    assert players["sheriff"] in state.getDeadPlayers()
    assert players["sheriff"] not in state.getInnocents()
    assert state.isSheriffDead() is True
    assert state.isDoctorDead() is False


def test_kill_same_player_twice_raises() -> None:
    state, players = _build_state()
    state.killPlayer(players["innocent"])

    with pytest.raises(PlayerNotFoundError):
        state.killPlayer(players["innocent"])


def test_check_player_win_when_no_mafias_left() -> None:
    state, players = _build_state()
    state.killPlayer(players["mafia"])

    assert state.checkPlayerWin() is True
    assert state.getWinningRole() == "Innocent"


def test_check_mafia_win_when_mafia_count_meets_or_exceeds_innocents() -> None:
    state, players = _build_state()
    state.killPlayer(players["innocent"])
    state.killPlayer(players["doctor"])

    assert state.checkMafiaWin() is True
    assert state.getWinningRole() == "Mafia"


def test_protect_and_clear_player() -> None:
    state, players = _build_state()
    state.protectPlayer(players["doctor"])
    assert state.protectedPlayer == players["doctor"]

    state.clearProtection()
    assert state.protectedPlayer is None
