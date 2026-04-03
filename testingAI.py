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
    "role": "system",
    "content": "You are playing a game of Mafia. There are 9 players. You have been given the role of Innocent. Your name is Pirate Pete. Talk like a pirate",
    },
    {
    "role": "developer",
    "content": "Keep your response within 70 words"
    },
    {
    "role": "user",
    "content": """
    Night 1: Player 1 was killed by the Mafia.
    Flabby Frank says: Hey guys, I think it's Peculiar Polly.
    Peculiar Polly says: Nah, I think it's Flabby Frank!
    """
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



# response = client.responses.parse(
#     model = "gpt-5-mini-2025-08-07",
#     # tools = tool,
#     input = input_message,
# )

conversation = client.conversations.create(
    items = input_message
)

id = conversation.id

first_response = client.responses.create(
    conversation = id,
    model = "gpt-5-mini-2025-08-07",
    # tools = tool,
    input = input_message,
)

print(first_response.output)

print(client.conversations.items.list(conversation_id=id))


second_response = client.responses.create(
    conversation=id,
    model="gpt-5-mini-2025-08-07",
    input=[
        {
            "role": "user",
            "content": ["Humany player: Hey Pete, I think you're fat and ugly.", "Yo, my penis is kinda small ngl."]
        }
    ]
)
print('------------------')

print(second_response.output)

print(client.conversations.items.list(conversation_id=id))

# print(response.output_parsed)
# print(response.output_parsed.accused.name)
# with open('funnyFile2.txt', 'w') as f:
#     print(response, file=f)