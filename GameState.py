from Player import Player
from PlayerRoles import Roles


class GameState:
    """
    Holds all information about the current state of the game including Players, who is the sheriff, who is the doctor,
    and day count etc.
    """

    def __init__(
        self,
        players: list[Player],
        innocents: list[Player],
        mafias: list[Player],
        sheriff: Player,
        doctor: Player,
    ) -> None:
        self.alivePlayers = players
        self.innocents = innocents
        self.mafias = mafias
        self.sheriff = sheriff
        self.doctor = doctor
        self.deadPlayers: dict[Player, int] = {}
        self.currentDay = 1
        self.protectedPlayer = None  # Might need to change this to a list at some point

    def getAlivePlayers(self) -> list[Player]:
        return self.alivePlayers.copy()

    def getInnocents(self) -> list[Player]:
        return self.innocents.copy()

    def getMafias(self) -> list[Player]:
        return self.mafias.copy()

    def getSheriff(self) -> Player:
        return self.sheriff

    def getDoctor(self) -> list[Player]:
        return self.doctor

    def getDeadPlayers(self) -> list[Player]:
        return self.deadPlayers.copy()

    def getDay(self) -> int:
        return self.currentDay

    def nextDay(self) -> None:
        self.currentDay += 1

    def killPlayer(self, player: Player) -> None:
        self.alivePlayers.remove(player)
        self.deadPlayers[player] = self.currentDay

    def revealPlayer(self, playerNo) -> Roles.PlayerRole:
        return self.players[playerNo - 1].role

    def protectPlayer(self, playerNo) -> None:
        self.protectedPlayer = self.players[playerNo - 1]

    def clearProtection(self) -> None:
        self.protectedPlayer = None
