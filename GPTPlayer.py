from __future__ import annotations
import PlayerRoles as Roles
from Player import Player
import logging
import random
from typing import Optional
from openai import OpenAI
from pydantic import BaseModel
import json

class GPTPlayer(Player):
    client = OpenAI()

    developer_message = "You are playing a game of Mafia. There are 9 players. You have been given the role of Innocent. Your name is Pirate Pete. Talk like a pirate."
    convo_addition_message = 'Now its your turn to speak. You may or may not accuse one or multiple players. ' \
    'You can only accuse alive players. Check with your tool for the alive players and pull a player out of that list if you accuse. ' \
    'Keep your response within 30 words.'
    vote_message = 'Now its your turn to vote. You can only vote alive players. Check with your tool for the alive players and pull a player out of that list. ' \
    'You dont have to vote someone if you dont want to. '

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

    def makeConvo(self, convo: str, alivePlayers: list[Player]) -> tuple[str, "Player"]:

        logging.debug(f'GPT Player {self.getName()} was given this summary: ' + convo)

        input_message = [
            {
                "role": "developer",
                "content": self.developer_message,
            },
            {
                "role": "user",
                "content": convo + '\n' + self.convo_addition_message
            },
        ]

        response = self.client.responses.create(
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

        response = self.client.responses.create(
            model = "gpt-5-mini-2025-08-07",
            tools = self.alivePlayers_tool,
            input = input_message,
        )

        return (response.output_text, None)
    
    def castVote(self, alivePlayers: list[Player], convo: str) -> Player:
        logging.debug(f'GPT Player {self.getName()} was given this summary: ' + convo)

        input_message = [
            {
                "role": "developer",
                "content": self.developer_message,
            },
            {
                "role": "user",
                "content": convo + '\n' + self.convo_addition_message
            }
        ]

        class PlayerVote(BaseModel):
            your_vote: Optional[str] = None

        response = self.client.responses.parse(
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

        response = self.client.responses.parse(
            model = "gpt-5-mini-2025-08-07",
            tools = self.alivePlayers_tool,
            input = input_message,
            text_format = PlayerVote,
        )

        for player in alivePlayers:
            if player.getName() == response.output_parsed.your_vote:
                return player
            
        return None