from __future__ import annotations
import PlayerRoles as Roles
import logging
import random

logger = logging.getLogger('game')

class Player:
    """
    Player class. Human and AI Players inherit from this.
    """

    def __init__(
        self,
        name: str,
        number: int = 1,
        role: Roles.PlayerRole = Roles.PlayerRole.INNOCENT,
        profile: str | None = None
    ) -> None:
        self.number = number
        self.name = name
        self.role = role
        self.privateSumm = ""

    async def makeConvo(self, convo: str, alivePlayers: list[Player]) -> tuple[str, "Player"]:
        """
        Answer a question posed to it if given, and then return a tuple with the answer and another Player
        that we want to talk to next

        Args:
        question: The question that was just posed to it
        player: the player that posed the question to it.

        Returns: tuple[0]: what it wants to say, tuple[1]: who it wants to talk next
        """
        return (
            "I swear it's not me guys!",
            random.randint(1, 8),
        )  # Please Change this.

    async def castVote(self, alivePlayers: list[Player], convo: str) -> Player:
        """
        Based on the previous conversation, make a vote.

        Returns: Player to be voted out
        """
        choice = random.randint(0, len(alivePlayers) - 1)
        print(f"I voted for player {alivePlayers[choice]}")
        return alivePlayers[choice]  # Randomly votes for a player

    async def castSecondVote(self, votedPlayers: list[Player], convo: str) -> Player:
        """
        After a group of players have been voted, choose a player from the list as the final
        vote to vote out, or choose None if you think a mistake has been made
        """

        return random.choice(votedPlayers)

    async def makeDefense(self, alivePlayers: list[Player], convo: str) -> str:
        """
        You've been accused of being in the Mafia! Try to defend yourself the best way you can.
        This is the conversation that you are allowed to have after you've being nominated
        as being in the mafia. Good luck!

        Returns: Your conversational defense to all the players
        """
        return "I am not part of the Mafia! I swear it!"

    async def pickTarget(self, innocentPlayers: list["Player"], convo: str) -> "Player":
        """
        As a Mafia player, pick a target, throw an error if not Mafia
        """
        if self.role != Roles.PlayerRole.MAFIA:
            raise ValueError("Only Mafia can pick a target.")

        choice = random.randint(0, len(innocentPlayers) - 1)
        print(f"I'm going to kill {innocentPlayers[choice]}")
        return innocentPlayers[choice]

    async def getDoctorPick(self, alivePlayers: list["Player"], convo: str) -> "Player":
        if self.role != Roles.PlayerRole.DOCTOR:
            raise ValueError("Only Doctor can pick a target.")
            
        protectedPlayer = random.choice(alivePlayers)
        logger.debug(f'I, the doctor, {self}, am protecting {protectedPlayer}')
        return protectedPlayer

    async def investigatePlayer(self, alivePlayers: list["Player"], convo: str) -> "Player":
        if self.role != Roles.PlayerRole.SHERIFF:
            raise ValueError("Only Sheriff can investigate players.")

        investigatedPlayer = random.choice(alivePlayers)
        logger.debug(f'I, the Sherrif, {self}, am about to investigate {investigatedPlayer}')
        return investigatedPlayer

    async def updatePrivSumm(self, summ: str) -> None:
        self.privateSumm += summ + "\n"
        
    def getRole(self) -> Roles.PlayerRole:
        return self.role

    def getName(self) -> str:
        return self.name

    def __str__(self) -> str:
        return self.name + ", role: " + str(self.role)
