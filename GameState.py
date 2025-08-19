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
        self.playerCount = len(players)
        self.innocents = innocents
        self.mafias = mafias
        self.sheriff = sheriff
        self.doctor = doctor
        self.deadPlayers: dict[Player, int] = {}
        self.currentDay = 1
        self.protectedPlayer = None  # Might need to change this to a list at some point

    def getPlayerCount(self) -> int:
        return self.playerCount

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
        if player in self.innocents:
            self.innocents.remove(player)
        elif player in self.mafias:
            self.mafias.remove(player)
        self.deadPlayers[player] = self.currentDay

    def revealPlayer(self, player: Player) -> str:
        return "Mafia" if player in self.mafias else "Innocent"

    def protectPlayer(self, player: Player) -> None:
        self.protectedPlayer = player

    def clearProtection(self) -> None:
        self.protectedPlayer = None
