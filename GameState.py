from Player import Player
import logging

logger = logging.getLogger('game')

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
        wsPlayers: list[Player] = None,
    ) -> None:

        self.alivePlayers = players
        self.playerCount = len(players)
        self.innocents = innocents
        self.mafias = mafias
        self.sheriff = sheriff
        self.sheriffDead = False
        self.doctor = doctor
        self.doctorDead = False
        self.deadPlayers: dict[Player, int] = {}  # Trackes date of death
        self.currentDay = 1
        self.protectedPlayer = None  # Might need to change this to a list at some point
        self.winningRole = None
        self.wsPlayers = wsPlayers if wsPlayers is not None else []
        self.gptPlayers = [player for player in players if player not in self.wsPlayers] # Just anti-ws Players lowk

    def getAllPlayers(self) -> list[Player]:
        totalList = self.alivePlayers.copy()
        totalList.extend(list(self.deadPlayers.keys()))
        return totalList

    def getPlayerCount(self) -> int:
        return self.playerCount

    def getAlivePlayers(self) -> list[Player]:
        return self.alivePlayers.copy()

    def getInnocents(self) -> list[Player]:
        return self.innocents.copy()

    def getWsPlayers(self) -> list[Player]:
        return self.wsPlayers.copy()
    
    def getGptPlayers(self) -> list[Player]:
        return self.gptPlayers.copy()

    def getMafias(self) -> list[Player]:
        return self.mafias.copy()

    def getSheriff(self) -> Player:
        return self.sheriff

    def getDoctor(self) -> list[Player]:
        return self.doctor

    def getDeadPlayers(self) -> list[Player]:
        return list(self.deadPlayers.keys()).copy()

    def getDay(self) -> int:
        return self.currentDay

    def nextDay(self) -> None:
        self.currentDay += 1

    def isSheriffDead(self) -> bool:
        return self.sheriffDead

    def isDoctorDead(self) -> bool:
        return self.doctorDead

    def killPlayer(self, player: Player | None) -> None:
        if player == None:
            return
        if player not in self.alivePlayers:
            raise PlayerNotFoundError(
                f"Tried to kill Player {player} but player is not in alive players"
            )
        logger.info(f"Player {player} has been killed on day {self.currentDay}")
        self.alivePlayers.remove(player)
        if player in self.innocents:
            self.innocents.remove(player)
        elif player in self.mafias:
            self.mafias.remove(player)
        self.deadPlayers[player] = self.currentDay
        if player == self.sheriff:
            self.sheriffDead = True
        if player == self.doctor:
            self.doctorDead = True

    def revealPlayer(self, player: Player) -> str:
        return "Mafia" if player in self.mafias else "Innocent"

    def protectPlayer(self, player: Player) -> None:
        self.protectedPlayer = player

    def clearProtection(self) -> None:
        self.protectedPlayer = None

    def __str__(self) -> str:
        state = "---------------\n"
        state += "GAME STATE \n"
        state += f"Day: {self.currentDay}\n"
        state += f"Alive Players ({len(self.alivePlayers)}): {[str(player) for player in self.alivePlayers]}\n"
        state += f"Innocents ({len(self.innocents)}): {[str(player) for player in self.innocents]}\n"
        state += (
            f"Mafias ({len(self.mafias)}): {[str(player) for player in self.mafias]}\n"
        )
        state += f"Sheriff: {self.sheriff}\n"
        state += f"Doctor: {self.doctor}\n"
        state += f"Dead Players ({len(self.deadPlayers)}): {[str(player) + ' (Day ' + str(day) + ')' for player, day in self.deadPlayers.items()]}\n"
        state += "---------------"

        return state

    def checkPlayerWin(self) -> bool:
        if len(self.mafias) == 0:
            logger.info("Zero mafias left, innocents win!")
            self.setWinningRole("Innocent")
            return True
        return False

    def checkMafiaWin(self) -> bool:
        if len(self.mafias) >= len(self.innocents):
            logger.info(
                "The mafias are at least equal in number to innocents, mafias win!"
            )
            self.setWinningRole("Mafia")
            return True
        return False

    def setWinningRole(self, role: str) -> None:
        self.winningRole = role

    def getWinningRole(self) -> str:
        return self.winningRole


class PlayerNotFoundError(Exception):
    pass
