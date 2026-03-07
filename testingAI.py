from openai import OpenAI
from pydantic import BaseModel
import json
from Player import Player
from enum import Enum

client = OpenAI()

alive_players_list = ['Shifty Shelby', 'Player 9', 'Player 3', 'Player 2', 'Innocent Andy']
player_names = Enum('alive_players', alive_players_list)

class ConversationFragment(BaseModel):
    your_response: str
    accused: player_names

tool = [
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

input_message = [
    {
    "role": "developer",
    "content": "You are playing a game of Mafia. There are 9 players. You have been given the role of Innocent. Your name is Pirate Pete. Talk like a pirate.",
    },
    {
    "role": "user",
    "content": "This is what happend in the Mafia game so far: " \
    'Night 1: ' \
    'Player 1 was killed by the Mafia. ' \
    'Day 2: ' \
    'Player 1 says: Hey guys, I think its Player 9. ' \
    'Player 4 says: Hey guys! I like men. '
    'Player 7 makes his/her defense: I am not part of the Mafia! I swear it! ' \
    'Night 2: ' \
    'Player 6 was killed by the Mafia. ' \
    'Day 3: ' \
    'Player 7 makes his/her defense: I am not part of the Mafia! I swear it! ' \
    'Night 3: ' \
    'Player 4 was killed by the Mafia. ' \
    'Day 4: ' \
    'Player 3 makes his/her defense: I am not part of the Mafia! I swear it! ' \
    'Now its your turn to speak. You may or may not accuse one or multiple players. ' \
    'You can only accuse alive players.' \
    'Keep your response within 30 words.',
    }
]

# response = client.responses.parse(
#     model = "gpt-5-mini-2025-08-07",
#     # tools = tool,
#     input = input_message,
#     text_format = ConversationFragment,
# )

# input_message += response.output

# for item in response.output:
#     if item.type == "function_call":
#         if item.name == "get_alive_players":
#             alive_players = ['Shifty Shelby', 'Player 9', 'Player 3', 'Player 2', 'Innocent Andy']

#             input_message.append({
#                 "type": "function_call_output",
#                 "call_id": item.call_id,
#                 "output": json.dumps({
#                     "alive_players": alive_players
#                 })
#             })

# print(input_message)

response = client.responses.parse(
    model = "gpt-5-mini-2025-08-07",
    # tools = tool,
    input = input_message,
    text_format = ConversationFragment,
)

print(response.output_parsed)
print(response.output_parsed.accused.name)
# with open('funnyFile2.txt', 'w') as f:
#     print(response, file=f)