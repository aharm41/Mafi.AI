import pytest
from PlayerRoles import PlayerRole
from Player import Player
from GameManager import GameManager

@pytest.fixture
def gameManager():
    return GameManager(9)

def test_playerCount(gameManager):
    assert len(gameManager.getAllPlayers()) == 9

def test_allValidPlayers(gameManager):
    for player in gameManager.getAllPlayers():
        assert isinstance(player, Player)