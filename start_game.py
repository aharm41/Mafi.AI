import argparse
import json
from InputParams import InputParams
from GameManager import GameManager

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Starts the Mafi.AI game with the specified input params")
    parser.add_argument("--gamep", required=True)
    parser.add_argument("--connects", required=True)

    args = parser.parse_args()
    
    data = json.loads(args.gamep)
    ws = args.connects.split(",")
    
    print(f"Starting game with data: {data}")

    inputParams = InputParams(**data)
    
    game = GameManager(inputParams, ws)
    
    
    