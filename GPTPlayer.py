from __future__ import annotations
import PlayerRoles as Roles
from Player import Player
from GPTProfiles import *
import logging
from typing import Optional
from openai import AsyncOpenAI
from pydantic import BaseModel
import json

logger = logging.getLogger('game')

"""
GPTPlayer class. Inherits from Player. Uses GPT-5 to make decisions.
Has a maximmum token usage of 15,000 tokens per game: if exceeded, a value error is raised.
Every use of the OpenAI API needs to call the makeInuptMessage function as that checks tokens.
"""
class GPTPlayer(Player):
    client = AsyncOpenAI()
    
    convo_addition_message = 'Now its your turn to speak. You may or may not accuse one or multiple players. ' \
    'You can only accuse alive players. Check with your tool for the alive players and pull a player out of that list if you accuse. '
    vote_message = 'Now its your turn to vote. You can only vote alive players. Check with your tool for the alive players and pull a player out of that list. ' \
    'You dont have to vote someone if you dont want to. Make sure your pick is exactly as the name appears. Say nothing but the name.'
    second_vote_message = """
    Players have been staged for being lynched. You now cast your second vote.
    Check with your tool to see what players are being staged, and pick a player out
    of there to cast your final vote. Or, vote None if you don't want to vote anyone.
    Make sure your pick is exactly as the name appears. Say nothing but the name.
    """
    making_defense_message = """
    You have been voted to be lynched! Make your defense now. If you want to deflect blame,
    use your get alive players tool to get the list of currently alive players. Make sure your response is within 50 words.
    """
    picking_target_message = """
    It's time for you to pick a player to kill as Mafia. Use your get alive players tool to get
    the list of currently alive players, and pick one of them as your target. Make sure your pick is exactly as the name appears. Say nothing but the name.
    """
    investigating_player_message = """
    It's time to investigate a player as Sheriff. Use your get alive players tool to get
    the list of currently alive players, and pick one of them to investigate. Make sure your pick is exactly as the name appears. Say nothing but the name.
    """
    doctor_protecting_message = """
    It's time to pick a player to protect as Doctor. Use your get alive players tool to get
    the list of currently alive players, and pick one of them to protect. Make sure your pick is exactly as the name appears. Say nothing but the name.
    """

    alivePlayers_tool = [
        {
            "type": "function",
            "name": "get_alive_players",
            "description": "Get the names of the currently alive players in the game",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False
            },
            "strict": True,
        },
    ]

    getStagedPlayers_tool = [
        {
            "type": "function",
            "name": "get_staged_players",
            "description": "Get the names of the currently staged players for voting",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False
            },
            "strict": True,
        }
    ]

    getInnocentPlayers_tool = [
        {
            "type": "function",
            "name": "get_innocent_players",
            "description": "Get the names of the alive and innocent players for picking a target",
            "parameters": {
                "type": "object",
                "properties": {},
                "additionalProperties": False
            },
            "strict": True,
        }
    ]

    def __init__(
        self,
        name: str,
        number: int = 1,
        role: Roles.PlayerRole = Roles.PlayerRole.INNOCENT,
        profile: BaseGPTConfig = BaseGPTConfig()
    ) -> None:
        super().__init__(name, number, role)

        self.developer_message_innocent = profile.developer_message_innocent
        self.developer_message_mafia = profile.developer_message_mafia
        self.developer_message_doctor = profile.developer_message_doctor
        self.developer_message_sheriff = profile.developer_message_sheriff

        self.token_usage = 0

    async def makeConvo(self, convo: str, alivePlayers: list[Player]) -> tuple[str, "Player"]:
        input_message = self.makeInputMessage(self.convo_addition_message, convo)

        response = await self.client.responses.create(
            model = "gpt-5-mini-2025-08-07",
            tools = self.alivePlayers_tool,
            input = input_message,
        )

        input_message += response.output

        for item in response.output:
            if item.type == "function_call" and item.name == "get_alive_players":
                alive_players = [player.getName() for player in alivePlayers]

                input_message.append({
                    "type": "function_call_output",
                    "call_id": item.call_id,
                    "output": json.dumps({
                        "alive_players": alive_players
                    })
                })

        response = await self.client.responses.create(
            model = "gpt-5-mini-2025-08-07",
            tools = self.alivePlayers_tool,
            input = input_message,
        )

        self.token_usage += response.usage.total_tokens

        return (response.output_text, None)
    
    async def castVote(self, alivePlayers: list[Player], convo: str) -> Player:
        logger.debug(f'GPT Player {self.getName()} was given this summary: ' + convo)

        input_message = self.makeInputMessage(self.vote_message, convo)

        class PlayerVote(BaseModel):
            your_vote: Optional[str] = None

        response = await self.client.responses.parse(
            model = "gpt-5-mini-2025-08-07",
            tools = self.alivePlayers_tool,
            input = input_message,
            text_format = PlayerVote,
        )

        input_message += response.output

        for item in response.output:
            if item.type == "function_call" and item.name == "get_alive_players":
                alive_players = [player.getName() for player in alivePlayers]

                input_message.append({
                    "type": "function_call_output",
                    "call_id": item.call_id,
                    "output": json.dumps({
                        "alive_players": alive_players
                    })
                })

        response = await self.client.responses.parse(
            model = "gpt-5-mini-2025-08-07",
            tools = self.alivePlayers_tool,
            input = input_message,
            text_format = PlayerVote,
        )

        self.token_usage += response.usage.total_tokens

        for player in alivePlayers:
            if player.getName() == response.output_parsed.your_vote:
                return player
            
        if response.output_parsed.your_vote is None:
            logger.debug('Uh oh, GPTPlayer voted for None')
            return None
        logger.debug('Uh oh, GPTPlayer casted a vote on a non-existent or dead player: ' + response.output_parsed.your_vote)

        return None
    
    async def castSecondVote(self, votedPlayers: list[Player], convo: str) -> Player:
        logger.debug(f'GPT Player {self.getName()} was given this summary when casting second vote: ' + convo)

        input_message = self.makeInputMessage(self.second_vote_message, convo)

        class PlayerVote(BaseModel):
            your_vote: Optional[str] = None

        response = await self.client.responses.parse(
            model = "gpt-5-mini-2025-08-07",
            tools = self.getStagedPlayers_tool,
            input = input_message,
            text_format = PlayerVote,
        )

        input_message += response.output

        for item in response.output:
            if item.type == "function_call" and item.name == "get_staged_players":
                staged_players = [player.getName() if player is not None else None for player in votedPlayers]

                input_message.append({
                    "type": "function_call_output",
                    "call_id": item.call_id,
                    "output": json.dumps({
                        "staged_players": staged_players
                    })
                })

        response = await self.client.responses.parse(
            model = "gpt-5-mini-2025-08-07",
            tools = self.getStagedPlayers_tool,
            input = input_message,
            text_format = PlayerVote,
        )

        self.token_usage += response.usage.total_tokens

        for player in votedPlayers:
            if player is not None and player.getName() == response.output_parsed.your_vote:
                logger.debug('GPTPlayer casted second vote: ' + player.getName())
                return player
            
        logger.debug('Uh oh, GPTPlayer casted second vote on an un-staged player: ' + response.output_parsed.your_vote)
            
        return None
    
    async def makeDefense(self, alivePlayers: list[Player], convo: str) -> str:
        logger.debug(f'GPT Player {self.getName()} was given this summary when making defense: ' + convo)

        input_message = self.makeInputMessage(self.making_defense_message, convo)

        response = await self.client.responses.create(
            model = "gpt-5-mini-2025-08-07",
            tools = self.alivePlayers_tool,
            input = input_message,
        )

        input_message += response.output

        for item in response.output:
            if item.type == "function_call" and item.name == "get_alive_players":
                alive_players = [player.getName() for player in alivePlayers]

                input_message.append({
                    "type": "function_call_output",
                    "call_id": item.call_id,
                    "output": json.dumps({
                        "alive_players": alive_players
                    })
                })

        response = await self.client.responses.create(
            model = "gpt-5-mini-2025-08-07",
            tools = self.alivePlayers_tool,
            input = input_message,
        )

        self.token_usage += response.usage.total_tokens

        return response.output_text
    
    async def pickTarget(self, innocentPlayers: list["Player"], convo: str) -> "Player":
        logger.debug(f'Innocent Players: {[player.getName() for player in innocentPlayers]}')
        if self.role != Roles.PlayerRole.MAFIA:
            raise ValueError("Only Mafia can pick a target.")

        input_message = self.makeInputMessage(self.picking_target_message, convo)

        class MafiaPick(BaseModel):
            your_pick: str

        response = await self.client.responses.parse(
            model = "gpt-5-mini-2025-08-07",
            tools = self.getInnocentPlayers_tool,
            input = input_message,
            text_format = MafiaPick,
        )

        input_message += response.output

        for item in response.output:
            if item.type == "function_call" and item.name == "get_innocent_players":
                innocent_players = [player.getName() for player in innocentPlayers]

                input_message.append({
                    "type": "function_call_output",
                    "call_id": item.call_id,
                    "output": json.dumps({
                        "innocent_players": innocent_players
                    })
                })

        response = await self.client.responses.parse(
            model = "gpt-5-mini-2025-08-07",
            tools = self.getInnocentPlayers_tool,
            input = input_message,
            text_format = MafiaPick,
        )

        self.token_usage += response.usage.total_tokens

        for player in innocentPlayers:
            if player is not None and player.getName() == response.output_parsed.your_pick:
                logger.debug('GPTPlayer picked target: ' + player.getName())
                return player
            
        logger.debug('Uh oh, GPTPlayer picked a non-innocent or dead player as target: ' + response.output_parsed.your_pick)
        raise ValueError('No player was picked as target by GPTPlayer')
    
    async def investigatePlayer(self, alivePlayers: list["Player"], convo: str) -> None:
        if self.role != Roles.PlayerRole.SHERIFF:
            raise ValueError("Only Sheriff can investigate players.")

        input_message = self.makeInputMessage(self.investigating_player_message, convo)

        class SheriffPick(BaseModel):
            your_pick: str

        response = await self.client.responses.parse(
            model = "gpt-5-mini-2025-08-07",
            tools = self.alivePlayers_tool,
            input = input_message,
            text_format = SheriffPick,
        )

        input_message += response.output

        for item in response.output:
            if item.type == "function_call" and item.name == "get_alive_players":
                alive_players = [player.getName() for player in alivePlayers]

                input_message.append({
                    "type": "function_call_output",
                    "call_id": item.call_id,
                    "output": json.dumps({
                        "alive_players": alive_players
                    })
                })

        response = await self.client.responses.parse(
            model = "gpt-5-mini-2025-08-07",
            tools = self.alivePlayers_tool,
            input = input_message,
            text_format = SheriffPick,
        )

        self.token_usage += response.usage.total_tokens

        for player in alivePlayers:
            if player.getName() == response.output_parsed.your_pick:
                logger.debug('GPTPlayer investigated: ' + player.getName())
                return player
            
        logger.debug('Uh oh, GPTPlayer investigated a non-existent or dead player: ' + response.output_parsed.your_pick)
        raise ValueError('No player was investigated by GPTPlayer')

    async def getDoctorPick(self, alivePlayers: list["Player"], convo: str) -> "Player":
        if self.role != Roles.PlayerRole.DOCTOR:
            raise ValueError("Only Doctor can pick a target.")
            
        input_message = self.makeInputMessage(self.doctor_protecting_message, convo)

        class DoctorPick(BaseModel):
            your_pick: str

        response = await self.client.responses.parse(
            model = "gpt-5-mini-2025-08-07",
            tools = self.alivePlayers_tool,
            input = input_message,
            text_format = DoctorPick,
        )

        input_message += response.output

        for item in response.output:
            if item.type == "function_call" and item.name == "get_alive_players":
                alive_players = [player.getName() for player in alivePlayers]

                input_message.append({
                    "type": "function_call_output",
                    "call_id": item.call_id,
                    "output": json.dumps({
                        "alive_players": alive_players
                    })
                })

        response = await self.client.responses.parse(
            model = "gpt-5-mini-2025-08-07",
            tools = self.alivePlayers_tool,
            input = input_message,
            text_format = DoctorPick,
        )

        self.token_usage += response.usage.total_tokens

        for player in alivePlayers:
            if player.getName() == response.output_parsed.your_pick:
                logger.debug('GPTPlayer (Doctor) is protecting: ' + player.getName())
                return player
            
        logger.debug('Uh oh, GPTPlayer investigated a non-existent or dead player: ' + response.output_parsed.your_pick)
        raise ValueError('No player was investigated by GPTPlayer')
    
    def makeInputMessage(self, inputAddition: str, convo: str) -> list[dict]:
        self.checkTokenUsage()

        switcher = {
            Roles.PlayerRole.INNOCENT: self.developer_message_innocent,
            Roles.PlayerRole.MAFIA: self.developer_message_mafia,
            Roles.PlayerRole.DOCTOR: self.developer_message_doctor,
            Roles.PlayerRole.SHERIFF: self.developer_message_sheriff,
        }

        input_message = [
            {
                "role": "developer",
                "content": switcher.get(self.role, self.developer_message_innocent),
            },
            {
                "role": "user",
                "content": self.privateSumm + '\n' + convo + '\n' + inputAddition + ' Keep your response within 30 words.',
            },
        ]

        return input_message
    
    def checkTokenUsage(self) -> None:
        if self.token_usage > 15000:
            logger.warning(f'GPTPlayer {self.getName()} has used {self.token_usage} tokens and is over the limit')
            raise ValueError(f'GPTPlayer {self.getName()} has exceeded the token usage limit.')
        
    def getTokenUsage(self) -> int:
        return self.token_usage