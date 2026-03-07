from Player import Player
from fastapi import WebSocket
from PlayerRoles import PlayerRole as Roles
import logging
from FrontEndConnector import FrontEndConnector

logger = logging.getLogger('game')

class WSPlayer(Player):
    def __init__(self,
        name: str,
        number: int = 1,
        role: Roles = Roles.INNOCENT,
    ):
        super().__init__(name=name, number=number, role=role)
        self.frontEndConnector = None

    def attach_frontend(self, frontEndConnector: FrontEndConnector):
        self.frontEndConnector = frontEndConnector

    async def makeConvo(self, convo: str, alivePlayers: list[Player]) -> tuple[str, "Player"]:
        if self.frontEndConnector is None:
            raise ValueError('No Web socket is attached yet to the Player class')

        text = await self.frontEndConnector.ask_for_message('Type your message here...')

        return (text, None)

    async def castVote(self, alivePlayers: list[Player], convo: str) -> Player:
        if self.frontEndConnector is None:
            raise ValueError('No Web socket is attached yet to the Player class')
        
        choice = await self.frontEndConnector.ask_for_select('Who do you want to vote for?', [p.getName() for p in alivePlayers] + ['Skip'])
        for player in alivePlayers:
            if player.getName() == choice:
                return player
            
        if choice == 'Skip':
            return None

        raise ValueError("No player with the given name was found.")
        
    async def castSecondVote(self, votedPlayers: list[Player], convo: str) -> Player | None:
        if self.frontEndConnector is None:
            raise ValueError('No Web socket is attached yet to the Player class')
        
        choice = await self.frontEndConnector.ask_for_select('Who\'s your final choice?', [p.getName() if p is not None else 'None' for p in votedPlayers])
        if choice == 'None':
            return None
        
        for player in votedPlayers:
            if player is None:
                continue
            if player.getName() == choice:
                return player

        raise ValueError("No player with the given name was found.")


        
    async def makeDefense(self, alivePlayers: list[Player], convo: str) -> str:
        if self.frontEndConnector is None:
            raise ValueError('No Web socket is attached yet to the Player class')
        
        text = await self.frontEndConnector.ask_for_message('You are about to be lynched! Make your defense here...')

        return text
    
    async def pickTarget(self, innocentPlayers: list["Player"], convo: str) -> "Player":
        if self.role != Roles.MAFIA:
            raise ValueError("Only Mafia can pick a target.")

        if self.frontEndConnector is None:
            raise ValueError('No Web socket is attached yet to the Player class')
        
        choice = await self.frontEndConnector.ask_for_select('Who do you want to kill?', [p.getName() for p in innocentPlayers])
        for player in innocentPlayers:
            if player.getName() == choice:
                return player

        raise ValueError("No player with the given name was found.")

    async def getDoctorPick(self, alivePlayers: list["Player"], convo: str) -> "Player":
        if self.role != Roles.DOCTOR:
            raise ValueError("Only Doctor can pick a target.")
        
        if self.frontEndConnector is None:
            raise ValueError('No Web socket is attached yet to the Player class')
        
        choice = await self.frontEndConnector.ask_for_select('Who do you want to protect?', [p.getName() for p in alivePlayers])
        for player in alivePlayers:
            if player.getName() == choice:
                logger.debug(f'I, the doctor, {self}, am protecting {player}')
                return player

        raise ValueError("No player with the given name was found.")
    
    async def investigatePlayer(self, alivePlayers: list["Player"], convo: str) -> "Player":
        if self.role != Roles.SHERIFF:
            raise ValueError("Only Sheriff can investigate players.")
        
        if self.frontEndConnector is None:
            raise ValueError('No Web socket is attached yet to the Player class')

        choice = await self.frontEndConnector.ask_for_select('Who do you want to investigate?', [p.getName() for p in alivePlayers])

        for player in alivePlayers:
            if player.getName() == choice:
                logger.debug(f'I, the sheriff, {self}, am investigating {player}')
                return player

        raise ValueError("No player with the given name was found.")


    async def updatePrivSumm(self, summ: str) -> None:
        await self.frontEndConnector.send_message(summ)