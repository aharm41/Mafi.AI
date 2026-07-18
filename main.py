import logging

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from GameLifecycle import run_game_and_cleanup
from GameManager import GameManager
from GPTProfiles import PlayerType
from InputParams import InputParams

logger = logging.getLogger("web_log")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    handler = logging.FileHandler("web.log")
    handler.setLevel(logging.DEBUG)
    logger.addHandler(handler)


class StartGameRequest(BaseModel):
    gameId: str
    playerCount: int
    playerTypes: list[str]
    mafiaCount: int
    humanPlayers: dict[str, str]
    broadcastDest: str


app = FastAPI()


@app.post("/api/start_game")
async def start_game_api(
    payload: StartGameRequest,
    background_tasks: BackgroundTasks,
):
    try:
        player_types = [PlayerType[name] for name in payload.playerTypes]
    except KeyError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown PlayerType: {exc}",
        ) from exc

    params = InputParams(
        playerCount=payload.playerCount,
        humanPlayers=payload.humanPlayers,
        playerTypes=player_types,
        mafiaCount=payload.mafiaCount,
        broadcastDest=payload.broadcastDest,
    )
    try:
        params.validate()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    game_manager = GameManager(params)
    background_tasks.add_task(
        run_game_and_cleanup,
        game_manager,
        payload.gameId,
    )
    return JSONResponse(
        {"status": "started", "game_id": payload.gameId},
        status_code=202,
    )
