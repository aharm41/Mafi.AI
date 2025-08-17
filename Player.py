import PlayerRoles as Roles
import random


class Player:
    """
    Player class. Human and AI Players inherit from this CUNT.
    """

    def __init__(
        self,
        name: str,
        number: int = 1,
        role: Roles.PlayerRole = Roles.PlayerRole.INNOCENT,
    ) -> None:
        self.number = number
        self.name = name
        self.role = role

    def makeConvo(self, question: str | None, player: "Player") -> tuple[str, int]:
        """
        Answer a question posed to it if given, and then return a tuple with the answer and another Player
        that we want to talk to next

        Args:
        question: The question that was just posed to it
        player: the player that posed the question to it.

        Returns: tuple[0]: what it wants to say, tuple[1]: who it wants to talk next
        """
        return (
            "I'm not sure who to vote... how about you?",
            random.randint(1, 8),
        )  # Please Change this.

    def castVote(self) -> int:
        """
        Based on the previous conversation, make a vote.

        Currently just votes for itself lol

        Returns: NUMBER of player to be voted out
        """
        return random.randint(1, 8)  # Randomly votes for a player

    def castSecondVote(self, nominatedPlayers: tuple[int, int]) -> tuple[bool, bool]:
        """
        Based on the previous conversation and after the prosecuted have a chance to defend themselves,

        Args: nominatedPlayers: A tuple containing the two numbers of the two players nominated

        Returns: true or false whether or not we want to eject,
        """
        return [random.choice([True, False]), random.choice([True, False])]

    def makeDefense(self) -> str:
        """
        You've been accused of being in the Mafia! Try to defend yourself the best way you can.
        This is the conversation that you are allowed to have after you've being nominated
        as being in the mafia. Good luck!

        Returns: Your conversational defense to all the players
        """
        return "I am not part of the Mafia! I swear it!"
