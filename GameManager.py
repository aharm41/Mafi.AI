from PlayerRoles import PlayerRole
from Player import Player
from ConvoManager import ConvoManager
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
        playerList = []
        mafiaList = []
        innocentList = []
        doctor = None
        sheriff = None

        # Assign roles to players, keep track of each team
        for i in range(playerCount):
            playerList.append(Player(f"Player { i + 1 }", i + 1, playerRolesList[i]))
            if playerRolesList[i] == PlayerRole.MAFIA:
                mafiaList.append(playerList[i])
            else:
                innocentList.append(playerList[i])

            if playerRolesList[i] == PlayerRole.SHERIFF:
                sheriff = playerList[i]
            elif playerRolesList[i] == PlayerRole.DOCTOR:
                doctor = playerList[i]

        print(f"GameManager initialized with {playerCount} players.")

        self.gameState = GameState(playerList, innocentList, mafiaList, sheriff, doctor)
        self.convoManager = ConvoManager()

    def getGameState(self):
        return self.gameState

    def nightPhase(self):
        """
        Night phase logic goes here.
            STEPS TO DO:
            1. Update convo manager with "Night [i]:"
            2. Mayor wakes up mafia and they choose their target
            3. Doctor wakes up and chooses which player is immune
            4. Sheriff wakes up and investigates someone, returns if
            they are mafia or nah
            4. Updates the GameState class with the results
        """
        self.convoManager.addToSummary(f"Night {str(self.gameState.getDay())}:")
        nominatedPlayer = self.getMafiaVotes()
        protectedPlayer = self.doctor.getDoctorPick()
        if nominatedPlayer != protectedPlayer:
            self.gameState.killPlayer(nominatedPlayer)
            self.convoManager.addToSummary(
                f"{nominatedPlayer} was killed by the Mafia.\n"
            )
        else:
            self.convoManager.addToSummary(
                f"The mafia tried to kill {protectedPlayer}, but the doctor saved him.\n"
            )

        sheriffTarget = self.gameState.getSheriff().investigatePlayer()
        if sheriffTarget in self.gameState.getMafias():
            self.gameState.getSheriff().updatePrivSumm(
                f"{sheriffTarget} is a Mafia member.\n"
            )
        else:
            self.gameState.getSheriff().updatePrivSumm(
                f"{sheriffTarget} is an Innocent member.\n"
            )

    def dayPhase(self):
        """
        Day phase logic goes here.
            STEPS TO DO:
            1. Update convo manager with "Day [i]:"
            2. Get the Game State from last night, ask about what
              happened last night
            3. Initiate a conversation with the players and start timer
              at same time
            4. After timer has finished, get the votes from the players
            5. Voted people have a chance to defend themselves
        """
        pass

    def getMafiaVotes(self) -> Player:
        """
        Get the votes from the mafia players, and return the player
        that they want to vote out.

        change it so the it does the following:

        1. Start Time
        2. Query all mafia players for their first suggested vote
        3. Update convo manager with suggested votes
        4. Query all mafia players for their final decision given the suggested votes,
        going one at a time
        5. Return the player that received the most votes
        6. If there is a tie, randomly select one of the tied players.
        7. If timer runs out, pick the suggested votes from each Mafia player,
        if didn't make a suggestion, just fucking pick any random motherfucker
        8. Update the GameState with the final votes.

        Returns: Player to be voted out
        """
        votes = [mafia.castVote() for mafia in self.gameState.getMafias()]
        return max(set(votes), key=votes.count)

    def __str__(self):
        stringRep = f"GameManager with {self.gameState.getPlayerCount()} players, current day: {self.gameState.getDay()}\n"
        stringRep += f"List of current alive players:\n"
        for player in self.gameState.getAlivePlayers():
            stringRep += f"{player}\n"

        return stringRep