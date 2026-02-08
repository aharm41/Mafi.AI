from Player import Player
from GPTPlayer import GPTPlayer
from PlayerRoles import PlayerRole
from GPTProfiles import PlayerType

class InputParams():
    def __init__(self, playerCount, playerTypes: list[PlayerType], mafiaCount = None):
        self.playerCount = playerCount
        self.players = playerTypes
        self.mafiaCount = mafiaCount if mafiaCount is not None else max(1, playerCount // 4)
        self.doctorCount = 1
        self.sheriffCount = 1

        
    def validate(self) -> None:
        totalSpecialRoles = self.mafiaCount + self.doctorCount + self.sheriffCount
        if totalSpecialRoles >= self.playerCount:
            raise ValueError("Total number of special roles must be less than the total number of players.")
        if self.playerCount < 4 or self.playerCount > 12:
            raise ValueError("Player count must be between 4 and 12.")
        if self.mafiaCount >= self.playerCount // 2:
            raise ValueError("Number of Mafia must be less than half of the total players.")
        if self.playerCount != len(self.players) + 1:
            # Must be add one becaus the WS players is added at the beginning
            raise ValueError("Player count does not match the number of player objects provided.")
