import pytest
from PlayerRoles import PlayerRole
from Player import Player
from GameManager import GameManager

@pytest.fixture
def gameManager9():
    return GameManager(9)

@pytest.fixture
def gameManager15():
    return GameManager(15)

def test_playerCount(gameManager9):
    assert gameManager9.getGameState().getPlayerCount() == 9
    assert len(gameManager9.getGameState().getAllPlayers()) == 9


def test_allValidPlayers(gameManager9):
    for player in gameManager9.getGameState().getAllPlayers():
        assert isinstance(player, Player)

def testAliveList(gameManager9, gameManager15):
    assert len(gameManager9.getGameState().getAlivePlayers()) == 9
    assert len(gameManager15.getGameState().getAlivePlayers()) == 15

def testDeadList(gameManager9, gameManager15):
    assert len(gameManager9.getGameState().getDeadPlayers()) == 0
    assert len(gameManager15.getGameState().getDeadPlayers()) == 0

def testValidMafiaPlayers(gameManager9):  # SHOULD BE 2 MAFIA
    mafiaCount = sum(
        1 for player in gameManager9.getGameState().getAllPlayers() if player.role == PlayerRole.MAFIA
    )
    assert mafiaCount == 2

def testValidMafiaPlayers2(gameManager15):
    mafiaCount = sum(1 for player in gameManager15.getGameState().getAllPlayers() if player.role == PlayerRole.MAFIA)
    assert mafiaCount == 3

def killPlayer(gameManager9):
    gameState = gameManager9.getGameState()
    player1 = gameState.getAlivePlayers()[0]
    gameState.killPlayer(player1)
    assert len(gameState.getAlivePlayers()) == 8
    assert len(gameState.getDeadPlayers()) == 1
    assert sum([x for x in gameState.getAlivePlayers() if x == player1]) == 0