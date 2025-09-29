import pytest
from PlayerRoles import PlayerRole
from Player import Player
from GameState import PlayerNotFoundError
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
    def alwaysSayYes(self, nominatedPlayers=None):
        return (True, True)
    
    monkeypatch.setattr(Player, 'castSecondVote', alwaysSayYes)
    monkeypatch.setattr(Player, "castVote", votePlayer1LOL)

    gameManager9.dayPhase()
    gameState9 = gameManager9.getGameState()
    assert len(gameState9.getDeadPlayers()) == 1
    assert len(gameState9.getAlivePlayers()) == 8
    assert gameState9.getDeadPlayers()[0] == player1

def testDayPhaseTie(gameManager9, monkeypatch):
    def votingMyself(self, alivePlayers=None):
        return self
    def alwaysSayYes(self, nominatedPlayers=None):
        return (True, True)