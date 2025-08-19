from Player import Player
from PlayerRoles import PlayerRole

class ConvoManager:
    """
    Class to manage the conversation, keeping tabs on all the things that have happened previously (will be
    passed to the AI models so they can figure out their next move)
    Stores a convo summary which is an overall summary for everything that's happened in the game so far,
    including player actions, votes, and any other relevant information (that ALL players can see)
    """
    def __init__(self):
        self.lastConvo = None
        self.convoSummary = None

    def getLastConvo(self) -> str | None:
        return self.lastConvo
    
    def getConvoSummary(self) -> str | None:
        return self.convoSummary

    def clearConvo(self) -> None:
        self.lastConvo = None

    def summariseConvo(self) -> str:
        if self.lastConvo == None:
            return ""
        else:
            return self.lastConvo[:30] # Return up to 30th character for now, gott change

    """
    Summarises the previous convo, and then adds the new convo to the history.
    """
    def addConvo(self, convo: str) -> None:
        self.convoSummary += self.summariseConvo() + "\n"
        self.lastConvo = convo

    def addToSummary(self, convo: str) -> None:
        self.convoSummary += convo + "\n"