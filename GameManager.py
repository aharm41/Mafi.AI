import asyncio
from ClientRelay import ClientRelay
from PlayerRoles import PlayerRole
from Player import Player
from GPTPlayer import GPTPlayer
from ConvoManager import ConvoManager
from GameState import GameState
from InputParams import InputParams
from GPTProfiles import *

import logging
import threading
import random
from collections import deque

from WSPlayer import WSPlayer

logger = logging.getLogger("game")
logger.setLevel(logging.DEBUG)

fh = logging.FileHandler("sys.stderr")
fh.setLevel(logging.DEBUG)

logger.addHandler(fh)


class GameManager:
    """
    Game Manager acts like how mayor would. They control the game,
      intitate day and night phases and assigns roles to players.
    Updates the GameState class if someone is killed.
    Validates input params and creates the player list with the correct roles.

    Init function:

    Args:
        playerCount (int): How many players will be playing?
    """

    def __init__(self, inputParams: InputParams) -> None:
        inputParams.validate()

        mafiaCount = inputParams.mafiaCount
        sheriffCount = inputParams.sheriffCount
        doctorCount = inputParams.doctorCount

        playerRolesList = [0] * inputParams.playerCount
        playerRolesList[0:mafiaCount] = [PlayerRole.MAFIA] * mafiaCount
        playerRolesList[mafiaCount : mafiaCount + sheriffCount] = [
            PlayerRole.SHERIFF
        ] * sheriffCount
        playerRolesList[
            mafiaCount + sheriffCount : mafiaCount + sheriffCount + doctorCount
        ] = [PlayerRole.DOCTOR] * doctorCount
        playerRolesList[mafiaCount + sheriffCount + doctorCount :] = [
            PlayerRole.INNOCENT
        ] * (inputParams.playerCount - mafiaCount - sheriffCount - doctorCount)

        random.shuffle(playerRolesList)
        playerList = []
        humanPlayerList = []
        mafiaList = []
        innocentList = []
        doctor = None
        sheriff = None

        ind = 0
        for i in range(inputParams.playerCount - len(inputParams.humanPlayers)):
            playerType = inputParams.players[ind]
            playerList.append(
                GPTPlayer(
                    inputParams.players[ind].value.name,
                    ind,
                    playerRolesList[i],
                    playerType.value(),
                )
            )
            ind += 1

            if playerRolesList[i] == PlayerRole.MAFIA:
                mafiaList.append(playerList[i])
            else:
                innocentList.append(playerList[i])

            if playerRolesList[i] == PlayerRole.SHERIFF:
                sheriff = playerList[i]
            elif playerRolesList[i] == PlayerRole.DOCTOR:
                doctor = playerList[i]

        for relay_dest, name in inputParams.humanPlayers.items():
            next_player = WSPlayer(
                name,
                ind,
                playerRolesList[ind]
            )
            playerList.append(next_player)
            humanPlayerList.append(next_player)
            next_player.attach_frontend(ClientRelay(relay_dest))
            if playerRolesList[ind] == PlayerRole.MAFIA:
                mafiaList.append(next_player)
            else:
                innocentList.append(next_player)

            if playerRolesList[ind] == PlayerRole.SHERIFF:
                sheriff = next_player
            elif playerRolesList[ind] == PlayerRole.DOCTOR:
                doctor = next_player

            ind += 1

        logger.info(f"GameManager initialized with {inputParams.playerCount} players.")
        logger.debug(f"Player List: {playerList}")
        logger.debug(f"Innocent List: {innocentList}")
        logger.debug(f"Mafia List: {mafiaList}")

        self.gameState = GameState(
            playerList, innocentList, mafiaList, sheriff, doctor, humanPlayerList
        )
        self.convoManager = ConvoManager(ClientRelay(inputParams.broadcastDest))

    def getGameState(self):
        return self.gameState

    async def nightPhase(self):
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
        await self.convoManager.addConvo(f"Night {str(self.gameState.getDay())}:")
        alivePlayers = self.gameState.getAlivePlayers()
        
        async def skip():
            return None
        
        nightTasks = [self.getMafiaVotes()]
        if not self.gameState.isDoctorDead():
            nightTasks.append(self.gameState.getDoctor().getDoctorPick(alivePlayers, self.convoManager.getConvoSummary()))
        else:
            nightTasks.append(skip())
        if not self.gameState.isSheriffDead():
            nightTasks.append(self.gameState.getSheriff().investigatePlayer(alivePlayers, self.convoManager.getConvoSummary()))
        else:
            nightTasks.append(skip())
        
        protectedPlayer = None

        results = await asyncio.gather(*nightTasks)
        nominatedPlayer = results[0]
        if not self.gameState.isDoctorDead():
            protectedPlayer = results[1]
        

        logger.debug(f"Protected Player: {protectedPlayer}")
        logger.debug(f"Nominated Player: {nominatedPlayer}")

        if not self.getGameState().isSheriffDead():
            sheriffTarget = results[2]
            if sheriffTarget in self.gameState.getMafias():
                await self.gameState.getSheriff().updatePrivSumm(
                    f"You investigated {sheriffTarget.getName()} on Day {self.gameState.getDay()} and found"
                    f" that {sheriffTarget.getName()} is a Mafia member.\n"
                )
            else:
                await self.gameState.getSheriff().updatePrivSumm(
                    f"You investigated {sheriffTarget.getName()} on Day {self.gameState.getDay()} and found"
                    f" that {sheriffTarget.getName()} is an innocent.\n"
                )

        if nominatedPlayer != protectedPlayer:
            await self.murderPlayer(nominatedPlayer)
        else:
            await self.convoManager.addConvo(
                f"The mafia tried to kill {protectedPlayer.getName()}, but the doctor saved him.\n"
            )

        self.gameState.clearProtection()
        self.gameState.nextDay()

    async def dayPhase(self):
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

        await self.convoManager.addConvo(f"Day {str(self.gameState.getDay())}:")

        logger.debug("Initiating conversation with players...")
        await self.initConversation()

        votes = []
        all_votes = await self.countVotes(votes)

        if len(votes) == 0:
            await self.convoManager.addConvo(
                "No one could be decided! No one has been voted out."
            )
            return

        votedPlayers = [votes[0]]
        maxCount = all_votes[votes[0]]

        if len(votes) > 1:
            for player in votes[1:]:
                if all_votes[player] == maxCount and player is not None:
                    votedPlayers.append(player)
                else:
                    break
        
        if len(votedPlayers) == 1 and votedPlayers[0] is None:
            await self.convoManager.addConvo(
                "The village has decided not to lynch anyone today."
            )
            return
        if votedPlayers[0] is None:
            votedPlayers = votedPlayers[1:] # In case None is put at the front

        votedPlayersConvo = (
            "These players have been voted by the village to be lynched: "
        )
        for player in votedPlayers:
            votedPlayersConvo += f"{player.getName()}, "
        votedPlayersConvo += "they make their defense:"
        await self.convoManager.addConvo(votedPlayersConvo)

        for player in votedPlayers:
            await self.convoManager.addConvo(
                f"{player.getName()} makes his/her defense: "
            )
             
            await self.convoManager.addChatConvo(
                await player.makeDefense(
                    self.gameState.getAlivePlayers(),
                    self.convoManager.getConvoSummary(),
                ), player.getName()
            )

        await self.convoManager.addConvo("Players now cast their second vote")
        nominatedPlayer = await self.countSecondVotes(votedPlayers)

        if nominatedPlayer == None:
            await self.convoManager.addConvo(
                "No one could be decided! No one has been voted out."
            )
        else:
            await self.lynchPlayer(nominatedPlayer)

        self.convoManager.clearConvo()

    """
    Counts the votes from all the players currenttly alive.
    @param votes: should be an empty list when invoking the function.
    Then votes will be filled with a sorted list.
    @returns: dictionary that maps players to their vote count.
    """

    async def countVotes(self, votes: list[Player]) -> dict[Player, int]:
        alivePlayers = self.gameState.getAlivePlayers()

        all_votes = {}
        tasks = [
            player.castVote(alivePlayers, self.convoManager.getConvoSummary())
            for player in alivePlayers
        ]
        voteList = await asyncio.gather(*tasks)
        for votedPlayer in voteList:
            if votedPlayer == None:
                all_votes[None] = all_votes.get(None, 0) + 1
            elif votedPlayer in all_votes:
                all_votes[votedPlayer] += 1
            else:
                all_votes[votedPlayer] = 1
        votes.extend(sorted(all_votes, key=all_votes.get, reverse=True))

        logger.debug(f"All Votes: {all_votes}")

        return all_votes

    async def countSecondVotes(self, votedPlayers: list[Player]) -> Player:
        alivePlayers = self.getGameState().getAlivePlayers()

        secondVotes = {}
        for player in votedPlayers:
            secondVotes[player] = 0
        secondVotes[None] = 0

        playersCastingVotes = []
        for player in alivePlayers:
            if player in votedPlayers:
                continue
            playersCastingVotes.append(player)

        tasks = [
            player.castSecondVote(votedPlayers, self.convoManager.getConvoSummary())
            for player in playersCastingVotes
        ]
        voteList = await asyncio.gather(*tasks)

        for votedPlayer in voteList:
            secondVotes[votedPlayer] += 1

        logger.debug(f"Second Votes: {secondVotes}")

        sortedSecondVotes = sorted(secondVotes, key=secondVotes.get, reverse=True)
        nominatedPlayer = sortedSecondVotes[0]
        if (
            len(secondVotes) > 1
            and secondVotes[nominatedPlayer] == secondVotes[sortedSecondVotes[1]]
        ):
            logger.info("Theres been a tie in the votes!")
            return None

        return nominatedPlayer

    async def getMafiaVotes(self) -> Player:
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

        votes = [
            await mafia.pickTarget(alivePlayers, self.convoManager.getConvoSummary())
            for mafia in self.gameState.getMafias()
        ]
        return max(set(votes), key=votes.count)

    def checkWin(self) -> bool:
        if self.gameState.checkPlayerWin():
            logger.info("Game Over! Innocents Win!")
            return True
        if self.gameState.checkMafiaWin():
            logger.info("Game Over! Mafias Win!")
            return True

        return False

    """
    Keep going until the game is over.
    """

    async def gameLoop(self) -> None:
        logger.debug(self.gameState)
        logger.debug("Initiating all players...")
        logger.debug(f"WS Players: {self.gameState.getWsPlayers()}")
        logger.debug(f"GPT Players: {self.gameState.getGptPlayers()}")
        await self.initiateAllPlayers(
            self.gameState.getWsPlayers(), self.gameState.getGptPlayers()
        )
        
        await self.convoManager.sendAllPlayers([player.getName() for player in self.gameState.getAllPlayers()])

        while not self.checkWin():
            await self.nightPhase()
            logger.debug(self.gameState)
            if self.checkWin():
                break
            await self.dayPhase()
            logger.debug(self.gameState)

        finalTokens = self.getFinalTokenUsage(self.gameState.getAllPlayers())
        logger.info(f"Total token usage for this game: {finalTokens} tokens.")

        logger.info("Game is finished")
        logger.debug(f"Game state:\n {self.gameState}")

        for player in self.gameState.getGptPlayers():
            logger.debug(f"{player.getName()} had the following conversation history: ")
            logger.debug(await player.getConversation())

        await self.sendGameOverMessages(
            self.gameState.getWsPlayers(), self.gameState.getWinningRole()
        )

    async def initConversation(self) -> None:
        await self.convoManager.addConvo("The villagers discuss who to lynch:")

        starting_int = random.randint(0, len(self.gameState.getAlivePlayers()) - 1)

        talkQueue = []
        for i in range(len(self.gameState.getAlivePlayers())):
            talkQueue.append(
                self.gameState.getAlivePlayers()[
                    (starting_int + i) % len(self.gameState.getAlivePlayers())
                ]
            )

        for i in range(len(self.gameState.getAlivePlayers())):
            talkQueue.append(
                self.gameState.getAlivePlayers()[
                    (starting_int + i) % len(self.gameState.getAlivePlayers())
                ]
            )
        talkQueue = deque(talkQueue)

        timerOver = threading.Event()

        # def timerFunc():
        #     timerOver.set()

        # timer = threading.Timer(15, timerFunc)
        # timer.start()

        while len(talkQueue):
            nextPlayer = talkQueue.popleft()
            [playerConvo, raisedPlayer] = await nextPlayer.makeConvo(
                self.convoManager.getConvoSummary(), self.gameState.getAlivePlayers()
            )
            await self.convoManager.addChatConvo(
                playerConvo, nextPlayer.getName()
            )
            # if raisedPlayer is not None:
            #     talkQueue.appendleft(raisedPlayer)

        # Repeat twice, so two people get to talk.

        await self.convoManager.addConvo("Voting now begins.")

    async def murderPlayer(self, player: Player) -> None:
        await self.convoManager.addKillConvo(
            f"{player.getName()} was brutally murdered by the Mafia. The players role was: {player.role.value}",
            player.getName()
        )
        self.gameState.killPlayer(player)

    async def lynchPlayer(self, player: Player) -> None:
        await self.convoManager.addKillConvo(
            f"{player.getName()} was voted by the village and has been lynched! The players role was: {player.role.value}",
            player.getName()
        )
        self.gameState.killPlayer(player)

    """
    Function to ininitate the Web Socket players given in frontEndPlayers.
    Basically just tells them what their roles are.
    Params:
        frontEndPlayers (list[WSPlayer]): List of WSPlayers to initiate

    FRONT END PLAYERS MUST HAVE A CLIENT RELAY ATTACHED BEFORE CALLING THIS FUNCTION
    """

    async def initiateWSPlayers(self, frontEndPlayers: list[WSPlayer]) -> None:
        for player in frontEndPlayers:
            if player.clientRelay is None:
                raise ValueError("No ClientRelay is attached to the player")

            await player.updatePrivSumm(f"Your role is: {player.role.value}\n")

            if player.role == PlayerRole.MAFIA:
                mafia_names = [
                    mafia.getName()
                    for mafia in self.gameState.getMafias()
                    if mafia != player
                ]
                if mafia_names:
                    await player.updatePrivSumm(
                        f'Your fellow mafia members are: {", ".join(mafia_names)}\n'
                    )
                else:
                    await player.updatePrivSumm(
                        "You are the only Mafia member in this game.\n"
                    )

    async def initiateGPTPlayers(self, gptPlayers: list[GPTPlayer]) -> None:
        tasks1 = [
            player.init([p.getName() for p in self.gameState.getAllPlayers()])
            for player in gptPlayers
            if player.getRole() != PlayerRole.MAFIA
        ]
        tasks2 = [
            player.init(
                [p.getName() for p in self.gameState.getAllPlayers()],
                [p.getName() for p in self.gameState.getMafias() if p != player],
            )
            for player in gptPlayers
            if player.getRole() == PlayerRole.MAFIA
        ]
        
        tasks = tasks1 + tasks2

        await asyncio.gather(*tasks)

    async def initiateAllPlayers(
        self, frontEndPlayers: list[WSPlayer], gptPlayers: list[GPTPlayer]
    ) -> None:
        tasks = [
            self.initiateWSPlayers(frontEndPlayers),
            self.initiateGPTPlayers(gptPlayers),
        ]
        await asyncio.gather(*tasks)

    async def sendGameOverMessages(
        self, frontEndPlayers: list[WSPlayer], winningRole: str
    ) -> None:
        for player in frontEndPlayers:
            if player.clientRelay is None:
                raise ValueError("No ClientRelay is attached to the player")

            if winningRole == PlayerRole.MAFIA.value:
                for players in frontEndPlayers:
                    if players.role == PlayerRole.MAFIA:
                        await players.updatePrivSumm(
                            "Game Over! The Mafia have won! Congratulations, you are a winner!\n"
                        )
                    else:
                        await players.updatePrivSumm(
                            "Game Over! The Mafia have won! Better luck next time, you are a loser!\n"
                        )
            else:
                for players in frontEndPlayers:
                    if players.role == PlayerRole.MAFIA:
                        await players.updatePrivSumm(
                            "Game Over! The Innocents have won! Better luck next time, you are a loser!\n"
                        )
                    else:
                        await players.updatePrivSumm(
                            "Game Over! The Innocents have won! Congratulations, you are a winner!\n"
                        )

    def __str__(self):
        stringRep = f"GameManager with {self.gameState.getPlayerCount()} players, current day: {self.gameState.getDay()}\n"
        stringRep += f"List of current alive players:\n"
        for player in self.gameState.getInnocents():
            stringRep += f"{player}\n"

        return stringRep

    def getFinalTokenUsage(self, players: list[Player]) -> int:
        total_tokens = 0
        for player in players:
            if isinstance(player, GPTPlayer):
                total_tokens += player.getTokenUsage()
                logger.debug(
                    "GPTPlayer "
                    + player.getName()
                    + " used "
                    + str(player.getTokenUsage())
                    + " tokens."
                )

        return total_tokens


# if __name__ == "__main__":
#     inputParams = InputParams(
#         6,
#         [
#             PlayerType.DEFAULT_DERRICK,
#             PlayerType.REFINED_REGINALD,
#             PlayerType.SHIFTY_SHELBY,
#             PlayerType.QUIET_QUINN,
#             PlayerType.PECULIAR_POLLY
#         ],
#         1
#     )

#     gameManager9 = GameManager(inputParams)

#     funnyFile = open("funnyFile.txt", "w")

#     async def runGameLoop():
#         nonlocal gameManager9
#         await gameManager9.gameLoop()


#     await gameManager9.gameLoop()

#     print(gameManager9.convoManager.getConvoSummary(), file=funnyFile)

#     funnyFile.close()
