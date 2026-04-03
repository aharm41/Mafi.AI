import asyncio

import pytest
from PlayerRoles import PlayerRole
from Player import Player
from GameState import PlayerNotFoundError
from GameManager import GameManager
from InputParams import InputParams
from GPTProfiles import PlayerType
from unittest.mock import AsyncMock, patch, Mock

class DummyWS:
    async def send_text(self, message):
        pass

@pytest.fixture
def gameManager5():
    dummy1 = AsyncMock()
    dummy1.name='Player 1'
    dummy2 = AsyncMock()
    dummy2.name='Player 2'
    dummy3 = AsyncMock()
    dummy3.name='Player 3'
    dummy4 = AsyncMock()
    dummy4.name = 'Player 4'
    inputParams = InputParams(5, [dummy1, dummy2, dummy3, dummy4])
    return GameManager(inputParams=inputParams, ws=AsyncMock())

@pytest.fixture
def gameManager9():
    # inputParams = InputParams(9, [])
    return GameManager(9)

@pytest.fixture
def gameManager15():
    return GameManager(15)

@pytest.fixture
def inputParamsInvalid():
    return InputParams(5, [PlayerRole.MAFIA, PlayerRole.DOCTOR, PlayerRole.SHERIFF, PlayerRole.INNOCENT])


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

def testKillPlayer(gameManager9):
    gameState = gameManager9.getGameState()
    player1 = gameState.getAlivePlayers()[0]
    gameState.killPlayer(player1)
    assert len(gameState.getAlivePlayers()) == 8
    assert len(gameState.getDeadPlayers()) == 1
    assert sum([x for x in gameState.getAlivePlayers() if x == player1]) == 0
    assert gameState.getDeadPlayers()[0] == player1

def testKillMultiplePlayers(gameManager9):
    gameState = gameManager9.getGameState()
    players = gameState.getAlivePlayers()[:3]  # kill first 3 players
    for p in players:
        gameState.killPlayer(p)
    assert len(gameState.getAlivePlayers()) == 6
    assert len(gameState.getDeadPlayers()) == 3
    for p in players:
        assert p in gameState.getDeadPlayers()
        assert p not in gameState.getAlivePlayers()

def testKillSamePlayerTwice(gameManager9):
    gameState = gameManager9.getGameState()
    player = gameState.getAlivePlayers()[0]
    gameState.killPlayer(player)
    beforeDeadCount = len(gameState.getDeadPlayers())
    with pytest.raises(PlayerNotFoundError):
        gameState.killPlayer(player)

def testProtectAndClear(gameManager9):
    gameState = gameManager9.getGameState()
    player = gameState.getAlivePlayers()[0]
    gameState.protectPlayer(player)
    assert gameState.protectedPlayer == player
    gameState.clearProtection()
    assert gameState.protectedPlayer == None

def testDay(gameManager9):
    gameState = gameManager9.getGameState()
    gameState.nextDay()
    gameState.nextDay()
    gameState.nextDay()
    assert(gameState.getDay() == 4)

def testNightPhase(gameManager9):
    gameState = gameManager9.getGameState()
    gameManager9.nightPhase()

def testDayPhase(gameManager9):
    gameState = gameManager9.getGameState()

    for _ in range(3):
        currNum = len(gameManager9.getGameState().getAlivePlayers())
        gameManager9.dayPhase()
        assert len(gameManager9.getGameState().getAlivePlayers()) <= currNum
        assert len(gameManager9.getGameState().getAlivePlayers()) >= currNum - 2

def testDeadDoctor(gameManager9, monkeypatch):
    gameState = gameManager9.getGameState()
    doctor = gameState.getDoctor()
    gameState.killPlayer(doctor)
    assert gameState.isDoctorDead() == True

def testDeadSheriff(gameManager9, monkeypatch):
    gameState = gameManager9.getGameState()
    sherrif = gameState.getSheriff()
    gameState.killPlayer(sherrif)
    assert gameState.isSheriffDead() == True

def testDayPhaseVoteCount(gameManager9, monkeypatch):
    player1 = gameManager9.getGameState().getAlivePlayers()[0]
    def votePlayer1LOL(self, alivePlayers=None):
        return player1
    def alwaysSayPlayer1(self, votedPlayers):
        return player1
    
    monkeypatch.setattr(Player, 'castSecondVote', alwaysSayPlayer1)
    monkeypatch.setattr(Player, "castVote", votePlayer1LOL)

    gameManager9.dayPhase()
    gameState9 = gameManager9.getGameState()
    assert len(gameState9.getDeadPlayers()) == 1
    assert len(gameState9.getAlivePlayers()) == 8
    assert gameState9.getDeadPlayers()[0] == player1

def testSecondVoteCancels(gameManager9, monkeypatch):
    player1 = gameManager9.getGameState().getAlivePlayers()[0]
    def votePlayer1LOL(self, alivePlayers=None):
        return player1
    def alwaysSayNone(self, votedPlayers):
        return None
    
    monkeypatch.setattr(Player, 'castSecondVote', alwaysSayNone)
    monkeypatch.setattr(Player, "castVote", votePlayer1LOL)

    gameManager9.dayPhase()
    gameState9 = gameManager9.getGameState()
    assert len(gameState9.getDeadPlayers()) == 0
    assert len(gameState9.getAlivePlayers()) == 9

@pytest.mark.asyncio
async def testDayPhaseTie(gameManager5, monkeypatch):
    def votingMyself(self, alivePlayers=None, convo=['AaaaaA', 'AaaaaA']):
        return alivePlayers[0]
    def alwaysSayNone(self, votedPlayers=None, convo=['AaaaaA', 'AaaaaA']):
        return None
    
    monkeypatch.setattr(Player, 'castSecondVote', alwaysSayNone)
    monkeypatch.setattr(Player, 'castVote', votingMyself)

    await gameManager5.dayPhase()
    gameState5 = gameManager5.getGameState()
    assert len(gameState5.getDeadPlayers()) == 0
    assert len(gameState5.getAlivePlayers()) == 5

def testInvalidInputParams(inputParamsInvalid):
    with pytest.raises(ValueError):
        inputParamsInvalid.validate()