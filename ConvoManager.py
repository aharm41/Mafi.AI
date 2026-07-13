from FrontEndConnector import FrontEndConnector
from Player import Player
from PlayerRoles import PlayerRole
from fastapi import WebSocket
import logging
import asyncio

logger = logging.getLogger('game')

class ConvoManager:
    """
    Class to manage the conversation, keeping tabs on all the things that have happened previously (will be
    passed to the AI models so they can figure out their next move)
    Stores a convo summary which is an overall summary for everything that's happened in the game so far,
    including player actions, votes, and any other relevant information (that ALL players can see)
    
    'Last convo' should refer to the previous night and day. So, should be cleared at the end of a day but 
    NOT at the end of a night.
    """

    def __init__(self):
        self.lastConvo = ''
        self.convoSummary = ''
        self.frontend = []
        
        self.convoState = []

    def attach_frontend(self, frontEndConnector: FrontEndConnector):
        self.frontend.append(frontEndConnector)

    def getLastConvo(self) -> str | None:
        return self.lastConvo

    def getConvoSummary(self) -> list[str] | None:
        return self.convoState

    """
    Just clears the LAST convo, not all convos
    """
    def clearConvo(self) -> None:
        self.lastConvo = ''

    def summariseConvo(self) -> str:
        if self.lastConvo == '':
            return ''
        else:
            return self.lastConvo[
                :30
            ]  # Return up to 30th character for now, gotta change

    """
    Summarises the previous convo, and then adds the new convo to the history.
    """

    async def addConvo(self, convo: str) -> None:
        self.convoSummary += convo + '\n'
        self.lastConvo += convo + '\n'
        await asyncio.gather(*[frontend.send_message(convo) for frontend in self.frontend])
            
            
        self.convoState.append(convo)
        
        
    async def addChatConvo(self, convo: str, player_name: str) -> None:
        self.convoSummary += f'[{player_name}]' + convo + '\n'
        self.lastConvo += f'[{player_name}]' + convo + '\n'
        await asyncio.gather(*[frontend.send_chat_message(convo, player_name) for frontend in self.frontend])
        self.convoState.append(f'[{player_name}]: {convo}')
        
        
    async def addKillConvo(self, convo: str, player_name: str) -> None:
        self.convoSummary += convo + '\n'
        self.lastConvo += convo + '\n'
        await asyncio.gather(*[frontend.send_message(convo) for frontend in self.frontend])
        await asyncio.gather(*[frontend.report_player_killed(player_name) for frontend in self.frontend])

        self.convoState.append(convo)
        
        
    async def sendAllPlayers(self, player_names: list[str]) -> None:
        await asyncio.gather(*[frontend.send_player_list(player_names) for frontend in self.frontend])
    

    def addToSummary(self, convo: str) -> None:
        self.convoSummary += convo + '\n'
