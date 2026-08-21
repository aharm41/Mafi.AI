import argparse
import json
import logging
from InputParams import InputParams
from GameManager import GameManager
from ClientRelay import ClientRelay
import asyncio
import uuid

async def run_game(game: GameManager):
    await game.gameLoop()

if __name__ == "__main__":
    logger = logging.getLogger('game')
    logging.basicConfig(level=logging.DEBUG)
    fh = logging.FileHandler('sys.stderr')
    fh.setLevel(logging.DEBUG)
    logger.addHandler(fh)

    parser = argparse.ArgumentParser(description="Starts the Mafi.AI game with the specified input params")
    parser.add_argument("--gamep", required=True)
    parser.add_argument("--connects", required=True)

    args = parser.parse_args()
    
    data = json.loads(args.gamep)
    ws = args.connects.split(",")
    
    game_id = uuid.uuid4().hex
    game_relay = ClientRelay(game_id)
    
    for player in ws:
        player_id = uuid.uuid4().hex
        
    
    logger.debug(f"Starting game with data: {data}")

    inputParams = InputParams(**data)
    
    game = GameManager(inputParams, ws, )
    
    asyncio.run(run_game(game))