import pytest
from PlayerRoles import PlayerRole
from Player import Player
from GameManager import GameManager


@pytest.fixture
def gameManager9():
    return GameManager(9)


def test_playerCount(gameManager9):
    assert len(gameManager9.getAllPlayers()) == 9


def test_allValidPlayers(gameManager9):
    for player in gameManager9.getAllPlayers():
        assert isinstance(player, Player)


def test_validMafiaPlayers(gameManager9):  # SHOULD BE 2 MAFIA
    mafiaCount = sum(
        1 for player in gameManager9.getAllPlayers() if player.role == PlayerRole.MAFIA
    )
    assert mafiaCount == 2
