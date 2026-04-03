from __future__ import annotations
import PlayerRoles as Roles
from Player import Player
from GPTProfiles import *
import logging
from enum import Enum
from typing import Optional
from openai import AsyncOpenAI
from pydantic import BaseModel
import json

logger = logging.getLogger('game')

TOKEN_MAX = 100000

"""
GPTPlayer class. Inherits from Player. Uses GPT-5 to make decisions.
Has a maximmum token usage of 15,000 tokens per game: if exceeded, a value error is raised.
Every use of the OpenAI API needs to call the makeInuptMessage function as that checks tokens.
"""
class GPTPlayer(Player):
    convoIndex = 0
    convoID = 0
    
    convo_addition_message = 'What do you say to the rest of the players?'
    vote_message = 'Now cast your vote (you may skip if you\'d like).'
    second_vote_message = """
    You now cast your second and final vote for this round. (you may skip if you\'d like).
    """
    making_defense_message = """
    You have been voted to be lynched! Make your defense now. Try to deflect blame!
    """
    picking_target_message = """
    Pick a player to target for the night as Mafia.
    """
    investigating_player_message = """
    As a Sheriff, pick a player to investigate and find their role.
    """
    doctor_protecting_message = """
    As a doctor, choose a player to be protected from the Mafia's attack tonight.
    """

    def __init__(
        self,
        name: str,
        number: int = 1,
        role: Roles.PlayerRole = Roles.PlayerRole.INNOCENT,
        profile: BaseGPTConfig = BaseGPTConfig()
    ) -> None:
        super().__init__(name, number, role)
        self.client = AsyncOpenAI()

        match role:
            case Roles.PlayerRole.INNOCENT:
                self.sys_message = profile.developer_message_innocent
            case Roles.PlayerRole.MAFIA:
                self.sys_message = profile.developer_message_mafia
            case Roles.PlayerRole.DOCTOR:
                self.sys_message = profile.developer_message_doctor
            case Roles.PlayerRole.SHERIFF:
                self.sys_message = profile.developer_message_sheriff

        self.token_usage = 0
        
    
    async def init(self, players: list[str], other_mafias: list[str] = None) -> None:
        if self.convoID != 0:
            raise ValueError('Conversation already exists for this player.')
        
        system_message = self.sys_message + ' \n ' + 'The players this game are: ' + ', '.join(players)
        if other_mafias:
            system_message += '\n' + 'Your other mafia players are: ' + ', '.join(other_mafias)
            system_message += '\n' + 'Try to co-ordinate with them sneakily without revealing either of your identities as Mafia.'

        
        conversation = await self.client.conversations.create(
            items=[
                {'role': 'system', 'content': system_message},
                {'role': 'developer', 'content': 'Keep responses within 50 words.'}
            ]
        )
        
        self.convoID = conversation.id
        
        
    async def makeConvo(self, convo: list[str], alivePlayers: list[Player]) -> tuple[str, "Player"]:
        input_addition = self.convo_addition_message + '\n' + 'The alive players are: ' + ', '.join([player.getName() for player in alivePlayers]) + '\n'
        input_message = self.makeInputMessage(input_addition, convo)

        response = await self.client.responses.create(
            conversation = self.convoID,
            model = "gpt-5-mini-2025-08-07",
            input = input_message,
        )

        self.token_usage += response.usage.total_tokens

        return (response.output_text, None)
    
    async def castVote(self, alivePlayers: list[Player], convo: list[str]) -> Player:
        logger.debug(f'GPT Player {self.getName()} was given this summary: ' + '\n'.join(convo))

        input_message = self.makeInputMessage(self.vote_message, convo)
        
        player_list = [player.getName() for player in alivePlayers]
        players = Enum('players', player_list)

        class PlayerVote(BaseModel):
            your_vote: Optional[players] = None

        response = await self.client.responses.parse(
            conversation=self.convoID,
            model = "gpt-5-mini-2025-08-07",
            input = input_message,
            text_format = PlayerVote,
        )

        self.token_usage += response.usage.total_tokens
        
        if response.output_parsed.your_vote is None:
            logger.debug('GPTPlayer voted for None')
            return None

        for player in alivePlayers:
            if player.getName() == response.output_parsed.your_vote.name:
                return player
            
        logger.debug('Uh oh, GPTPlayer casted a vote on a non-existent or dead player: ' + response.output_parsed.your_vote.name)
        raise ValueError("No player with the given name was found.")

    
    async def castSecondVote(self, votedPlayers: list[Player], convo: list[str]) -> Player:
        logger.debug(f'GPT Player {self.getName()} was given this summary when casting second vote: ' + '\n'.join(convo))

        input_message = self.makeInputMessage(self.second_vote_message, convo)

        player_list = [player.getName() for player in votedPlayers]
        players = Enum('players', player_list)

        class PlayerVote(BaseModel):
            your_vote: Optional[players] = None

        response = await self.client.responses.parse(
            conversation = self.convoID,
            model = "gpt-5-mini-2025-08-07",
            input = input_message,
            text_format = PlayerVote,
        )

        self.token_usage += response.usage.total_tokens
        if response.output_parsed.your_vote is None:
            return None

        for player in votedPlayers:
            if player is not None and player.getName() == response.output_parsed.your_vote.name:
                logger.debug('GPTPlayer casted second vote: ' + player.getName())
                return player
            
        raise ValueError("No player with the given name was found.")
    
    
    async def makeDefense(self, alivePlayers: list[Player], convo: list[str]) -> str:
        logger.debug(f'GPT Player {self.getName()} was given this summary when making defense: ' + '\n '.join(convo))

        input_addition = self.making_defense_message + '\n' + 'The alive players are: ' + ', '.join([player.getName() for player in alivePlayers]) + '\n'
        input_message = self.makeInputMessage(input_addition, convo)

        response = await self.client.responses.create(
            conversation = self.convoID,
            model = "gpt-5-mini-2025-08-07",
            input = input_message,
        )

        self.token_usage += response.usage.total_tokens

        return response.output_text
    
    
    async def pickTarget(self, innocentPlayers: list["Player"], convo: str) -> "Player":
        logger.debug(f'Innocent Players: {[player.getName() for player in innocentPlayers]}')
        if self.role != Roles.PlayerRole.MAFIA:
            raise ValueError("Only Mafia can pick a target.")

        player_list = [player.getName() for player in innocentPlayers]
        players = Enum('players', player_list)

        input_message = self.makeInputMessage(self.picking_target_message, convo)

        class MafiaPick(BaseModel):
            your_pick: players

        response = await self.client.responses.parse(
            conversation = self.convoID,
            model = "gpt-5-mini-2025-08-07",
            input = input_message,
            text_format = MafiaPick,
        )

        self.token_usage += response.usage.total_tokens

        for player in innocentPlayers:
            if player is not None and player.getName() == response.output_parsed.your_pick.name:
                logger.debug('GPTPlayer picked target: ' + player.getName())
                return player
            
        logger.debug('Uh oh, GPTPlayer picked a non-innocent or dead player as target: ' + response.output_parsed.your_pick.name)
        raise ValueError('No player was picked as target by GPTPlayer')
    
    
    async def investigatePlayer(self, alivePlayers: list["Player"], convo: str) -> None:
        if self.role != Roles.PlayerRole.SHERIFF:
            raise ValueError("Only Sheriff can investigate players.")

        player_list = [player.getName() for player in alivePlayers]
        players = Enum('players', player_list)

        input_message = self.makeInputMessage(self.investigating_player_message, convo)

        class SheriffPick(BaseModel):
            your_pick: players

        response = await self.client.responses.parse(
            conversation = self.convoID,
            model = "gpt-5-mini-2025-08-07",
            input = input_message,
            text_format = SheriffPick,
        )

        self.token_usage += response.usage.total_tokens

        for player in alivePlayers:
            if player.getName() == response.output_parsed.your_pick.name:
                logger.debug('GPTPlayer investigated: ' + player.getName())
                return player
            
        logger.debug('Uh oh, GPTPlayer investigated a non-existent or dead player: ' + response.output_parsed.your_pick.name)
        raise ValueError('No player was investigated by GPTPlayer')

    async def getDoctorPick(self, alivePlayers: list["Player"], convo: str) -> "Player":
        if self.role != Roles.PlayerRole.DOCTOR:
            raise ValueError("Only Doctor can pick a target.")
        
        player_list = [player.getName() for player in alivePlayers]
        players = Enum('players', player_list)
            
        input_message = self.makeInputMessage(self.doctor_protecting_message, convo)

        class DoctorPick(BaseModel):
            your_pick: players

        response = await self.client.responses.parse(
            conversation = self.convoID,
            model = "gpt-5-mini-2025-08-07",
            input = input_message,
            text_format = DoctorPick,
        )

        self.token_usage += response.usage.total_tokens

        for player in alivePlayers:
            if player.getName() == response.output_parsed.your_pick.name:
                logger.debug('GPTPlayer (Doctor) is protecting: ' + player.getName())
                return player
            
        logger.debug('Uh oh, GPTPlayer investigated a non-existent or dead player: ' + response.output_parsed.your_pick.name)
        raise ValueError('No player was investigated by GPTPlayer')
    
    def makeInputMessage(self, inputAddition: str, convo: list[str]) -> list[dict]:
        self.checkTokenUsage()
        
        input_msg = '\n'.join(convo[self.convoIndex + 1:]) + '\n' + inputAddition # Plus one to not repeat myself.
        self.convoIndex = len(convo)

        return [
            {
                "role": "user",
                "content": input_msg,
            },
        ]
        
    async def updatePrivSumm(self, summ):
        msg = [
            {
                "role": "user",
                "content": summ,
            }
        ]
        
        await self.client.conversations.items.create(
            conversation_id = self.convoID,
            items = msg,
        )
        
    
    async def getConversation(self):
        page = await self.client.conversations.items.list(self.convoID)
        
        return page.data
            
    
    def checkTokenUsage(self) -> None:
        if self.token_usage > 100000:
            logger.warning(f'GPTPlayer {self.getName()} has used {self.token_usage} tokens and is over the limit')
            raise ValueError(f'GPTPlayer {self.getName()} has exceeded the token usage limit.')
        
        
    def getTokenUsage(self) -> int:
        return self.token_usage