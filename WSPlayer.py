from Player import Player
from PlayerRoles import PlayerRole as Roles
import logging
from ClientRelay import ClientRelay

logger = logging.getLogger('game')

class WSPlayer(Player):
    def __init__(self,
        name: str,
        number: int = 1,
        role: Roles = Roles.INNOCENT,
    ):
        super().__init__(name=name, number=number, role=role)
        self.clientRelay = None

    def attach_frontend(self, clientRelay: ClientRelay):
        self.clientRelay = clientRelay

    async def makeConvo(self, convo: str, alivePlayers: list[Player]) -> tuple[str, "Player"]:
        if self.clientRelay is None:
            raise ValueError('No ClientRelay is attached to the player')

        text = await self.clientRelay.ask_for_message('Type your message here...')

        return (text, None)

    async def castVote(self, alivePlayers: list[Player], convo: str) -> Player:
        if self.clientRelay is None:
            raise ValueError('No ClientRelay is attached to the player')
        
        choice = await self.clientRelay.ask_for_select('Who do you want to vote for?', [p.getName() for p in alivePlayers] + ['Skip'])
        for player in alivePlayers:
            if player.getName() == choice:
                return player
            
        if choice == 'Skip':
            return None

        raise ValueError("No player with the given name was found.")
        
    async def castSecondVote(self, votedPlayers: list[Player], convo: str) -> Player | None:
        if self.clientRelay is None:
            raise ValueError('No ClientRelay is attached to the player')
        
        choice = await self.clientRelay.ask_for_select('Who\'s your final choice?', [p.getName() for p in votedPlayers] + ['None'])
        if choice == 'None':
            return None
        
        for player in votedPlayers:
            if player is None:
                continue
            if player.getName() == choice:
                return player

        raise ValueError("No player with the given name was found.")


        
    async def makeDefense(self, alivePlayers: list[Player], convo: str) -> str:
        if self.clientRelay is None:
            raise ValueError('No ClientRelay is attached to the player')
        
        text = await self.clientRelay.ask_for_message('You are about to be lynched! Make your defense here...')

        return text
    
    async def pickTarget(self, innocentPlayers: list["Player"], convo: str) -> "Player":
        if self.role != Roles.MAFIA:
            raise ValueError("Only Mafia can pick a target.")

        if self.clientRelay is None:
            raise ValueError('No ClientRelay is attached to the player')
        
        choice = await self.clientRelay.ask_for_select('Who do you want to kill?', [p.getName() for p in innocentPlayers])
        for player in innocentPlayers:
            if player.getName() == choice:
                return player

        raise ValueError("No player with the given name was found.")

    async def getDoctorPick(self, alivePlayers: list["Player"], convo: str) -> "Player":
        if self.role != Roles.DOCTOR:
            raise ValueError("Only Doctor can pick a target.")
        
        if self.clientRelay is None:
            raise ValueError('No ClientRelay is attached to the player')
        
        choice = await self.clientRelay.ask_for_select('Who do you want to protect?', [p.getName() for p in alivePlayers])
        for player in alivePlayers:
            if player.getName() == choice:
                logger.debug(f'I, the doctor, {self}, am protecting {player}')
                return player

        raise ValueError("No player with the given name was found.")
    
    async def investigatePlayer(self, alivePlayers: list["Player"], convo: str) -> "Player":
        if self.role != Roles.SHERIFF:
            raise ValueError("Only Sheriff can investigate players.")
        
        if self.clientRelay is None:
            raise ValueError('No ClientRelay is attached to the player')

        choice = await self.clientRelay.ask_for_select('Who do you want to investigate?', [p.getName() for p in alivePlayers])

        for player in alivePlayers:
            if player.getName() == choice:
                logger.debug(f'I, the sheriff, {self}, am investigating {player}')
                return player

        raise ValueError("No player with the given name was found.")


    async def updatePrivSumm(self, summ: str) -> None:
        await self.clientRelay.send_message(summ)