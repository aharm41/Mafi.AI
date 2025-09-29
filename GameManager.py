from PlayerRoles import PlayerRole
from Player import Player
from ConvoManager import ConvoManager
from GameState import GameState
import logging

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
        logger = logging.getLogger("__name__")
        logging.basicConfig(filename="game.log", level=logging.DEBUG)
        logger.setLevel(logging.DEBUG)

        fh = logging.FileHandler("game.log")
        fh.setLevel(logging.DEBUG)

        logger.addHandler(fh)

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
            5. Increment day
        """
        self.convoManager.addConvo(f"Night {str(self.gameState.getDay())}:")
        alivePlayers = self.gameState.getAlivePlayers()
        nominatedPlayer = self.getMafiaVotes()
        protectedPlayer = None

        if not self.gameState.isDoctorDead():
            protectedPlayer = self.gameState.getDoctor().getDoctorPick(alivePlayers)
        
        
        logging.debug(f"Protected Player: {protectedPlayer}")
        logging.debug(f"Nominated Player: {nominatedPlayer}")

        if nominatedPlayer != protectedPlayer:
            self.gameState.killPlayer(nominatedPlayer)
            self.convoManager.addConvo(f"{nominatedPlayer} was killed by the Mafia.\n")
        else:
            self.convoManager.addConvo(
                f"The mafia tried to kill {protectedPlayer}, but the doctor saved him.\n"
            )

        if not self.getGameState().isSheriffDead():
            sheriffTarget = self.gameState.getSheriff().investigatePlayer(alivePlayers)
            if sheriffTarget in self.gameState.getMafias():
                self.gameState.getSheriff().updatePrivSumm(
                    f"{sheriffTarget} is a Mafia member.\n"
                )
            else:
                self.gameState.getSheriff().updatePrivSumm(
                    f"{sheriffTarget} is an Innocent member.\n"
                )
        self.gameState.clearProtection()
        self.gameState.nextDay()

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

        self.convoManager.addConvo(f"Day {str(self.gameState.getDay())}:")

        logging.info(self.convoManager.getLastConvo())

        logging.debug("Initiating conversation with players...")

        votes = []
        all_votes = self.countVotes(votes)

        votedPlayers = [votes[0]]
        maxCount = all_votes[votes[0]]

        if len(votes) > 1:
            for player in votes[1:]:
                if all_votes[player] == maxCount:
                    votedPlayers.append(player)
                else:
                    break

        for player in votedPlayers:
            self.convoManager.addConvo(
                f"{player} makes his/her defense: " + player.makeDefense()
            )

        nominatedPlayer = self.countSecondVotes(votedPlayers)

        if nominatedPlayer == None:
            logging.info("No one could be decided! No one has been voted out")
        else:
            logging.info(f"The village has spoken! {nominatedPlayer} has been lynched.")
            self.gameState.killPlayer(nominatedPlayer)

        self.convoManager.clearConvo()

    """
    Counts the votes from all the players currenttly alive.
    @param votes: should be an empty list when invoking the function.
    Then votes will be filled with a sorted list.
    @returns: dictionary that maps players to their vote count.
    """

    def countVotes(self, votes: list[Player]) -> dict[Player, int]:
        alivePlayers = self.gameState.getAlivePlayers()

        all_votes = {}
        for player in alivePlayers:
            votedPlayer = player.castVote(alivePlayers)
            if votedPlayer in all_votes:
                all_votes[votedPlayer] += 1
            else:
                all_votes[votedPlayer] = 1
        votes.extend(sorted(all_votes, key=all_votes.get, reverse=True))

        logging.debug(f"All Votes: {all_votes}")

        return all_votes

    def countSecondVotes(self, votedPlayers: list[Player]) -> Player:
        alivePlayers = self.getGameState().getAlivePlayers()

        secondVotes = {}
        for player in votedPlayers:
            secondVotes[player] = 0
        secondVotes[None] = 0
        votedPlayers.append(None)

        for player in alivePlayers:
            if player in votedPlayers:
                continue

            votedPlayer = player.castSecondVote(votedPlayers)
            secondVotes[votedPlayer] += 1

        logging.debug(f"Second Votes: {secondVotes}")

        sortedSecondVotes = sorted(secondVotes, key=secondVotes.get, reverse=True)
        nominatedPlayer = sortedSecondVotes[0]
        if (
            len(secondVotes) > 1
            and secondVotes[nominatedPlayer] == secondVotes[sortedSecondVotes[1]]
        ):
            logging.info("Theres been a tie in the votes!")
            return None

        return nominatedPlayer

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
        alivePlayers = self.gameState.getInnocents()

        votes = [mafia.pickTarget(alivePlayers) for mafia in self.gameState.getMafias()]
        return max(set(votes), key=votes.count)

    def checkWin(self) -> bool:
        if self.gameState.checkPlayerWin():
            logging.info("Game Over! Innocents Win!")
            return True
        if self.gameState.checkMafiaWin():
            logging.info("Game Over! Mafias Win!")
            return True

        return False

    """
    Keep going until the game is over.
    """

    def gameLoop(self) -> None:
        logging.debug(self.gameState)

        while not self.checkWin():
            self.nightPhase()
            logging.debug(self.gameState)
            if self.checkWin():
                break
            self.dayPhase()
            logging.debug(self.gameState)

        logging.info("Game is finished")
        logging.debug(f"Game state:\n {self.gameState}")

    def __str__(self):
        stringRep = f"GameManager with {self.gameState.getPlayerCount()} players, current day: {self.gameState.getDay()}\n"
        stringRep += f"List of current alive players:\n"
        for player in self.gameState.getInnocents():
            stringRep += f"{player}\n"

        return stringRep


gameManager9 = GameManager(9)

funnyFile = open("funnyFile.txt", "w")



gameManager9.gameLoop()

print(gameManager9.convoManager.getConvoSummary(), file=funnyFile)

funnyFile.close()