from PlayerRoles import PlayerRole
from Player import Player
from GameState import GameState

import random


class GameManager:
    """
    Game Manager acts like that mayor would. They control the game,
      intitate day and night phases and assigns roles to players.
    Updates the GameState class if someone is killed. This is kind
      of like the 'mayor'.

    Init function:

    Args:
        playerCount (int): How many players will be playing?
    """

    def __init__(self, playerCount: int) -> None:
        # How many mafia?
        mafiaCount = playerCount // 4
        playerRolesList = [0] * playerCount
        playerRolesList[0:mafiaCount] = [PlayerRole.MAFIA] * mafiaCount
        playerRolesList[mafiaCount] = PlayerRole.SHERIFF
        playerRolesList[mafiaCount + 1] = PlayerRole.DOCTOR
        playerRolesList[mafiaCount + 2 :] = [PlayerRole.INNOCENT] * (
            playerCount - mafiaCount - 2
        )

        random.shuffle(playerRolesList)

        # Assign roles to players, keep track of each team
        for i in range(playerCount):
            self.playerList.append(
                Player(f"Player { i + 1 }", i + 1, playerRolesList[i])
            )
            if playerRolesList[i] == PlayerRole.MAFIA:
                self.mafiaList.append(self.playerList[i])
            else:
                self.innocentList.append(self.playerList[i])

            if playerRolesList[i] == PlayerRole.SHERIFF:
                self.sheriff = self.playerList[i]
            elif playerRolesList[i] == PlayerRole.DOCTOR:
                self.doctor = self.playerList[i]

        print(f"GameManager initialized with {playerCount} players.")

        alivePlayers = self.playerList.copy()

        self.gameState = GameState(
            alivePlayers, self.innocentList, self.mafiaList, self.sheriff, self.doctor
        )

    def nightPhase(self):
        """
        Night phase logic goes here.
            STEPS TO DO:
            1. Mayor wakes up mafia and they choose their target
            2. Doctor wakes up and chooses which player is immune
            3. Sheriff wakes up and investigates someone, returns if
            they are mafia or nah
            4. Updates the GameState class with the results
        """
        pass

    def dayPhase(self):
        """
        Day phase logic goes here.
            STEPS TO DO:
            1. Get the Game State from last night, ask about what
              happened last night
            2. Initiate a conversation with the players and start timer
              at same time
            3. After timer has finished, get the votes from the players
            4. Voted people have a chance to defend themselves
            5.
        """
        pass
