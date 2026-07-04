import json

import pytest

import GameManager as game_manager_module
from GPTProfiles import PlayerType
from InputParams import InputParams
from Player import Player
from PlayerRoles import PlayerRole


class DummyWebSocket:
    def __init__(self) -> None:
        self.messages: list[str] = []

    async def send_text(self, message: str) -> None:
        self.messages.append(message)

    async def receive_text(self) -> str:
        raise AssertionError("receive_text should not be called in this regression path.")


class ScriptedGPTPlayer(Player):
    def __init__(
        self,
        name: str,
        number: int = 1,
        role: PlayerRole = PlayerRole.INNOCENT,
        profile=None,
    ) -> None:
        super().__init__(name=name, number=number, role=role, profile=profile)
        self._token_usage = 0

    async def init(self, players: list[str], other_mafias: list[str] | None = None) -> None:
        return None

    async def makeConvo(self, convo: list[str], alivePlayers: list[Player]) -> tuple[str, Player | None]:
        return ("I have nothing useful to add.", None)

    async def castVote(self, alivePlayers: list[Player], convo: list[str]) -> Player | None:
        for player in alivePlayers:
            if player.getRole() != PlayerRole.MAFIA:
                return player

        return alivePlayers[0] if alivePlayers else None

    async def castSecondVote(self, votedPlayers: list[Player], convo: list[str]) -> Player | None:
        return votedPlayers[0] if votedPlayers else None

    async def makeDefense(self, alivePlayers: list[Player], convo: list[str]) -> str:
        return "I am innocent."

    async def pickTarget(self, innocentPlayers: list[Player], convo: list[str]) -> Player:
        if self.role != PlayerRole.MAFIA:
            raise ValueError("Only Mafia can pick a target.")

        for player in innocentPlayers:
            if player.getRole() == PlayerRole.SHERIFF:
                return player

        return innocentPlayers[0]

    async def investigatePlayer(self, alivePlayers: list[Player], convo: list[str]) -> Player:
        return alivePlayers[0]

    async def getDoctorPick(self, alivePlayers: list[Player], convo: list[str]) -> Player:
        return alivePlayers[-1]

    async def getConversation(self):
        return []

    def getTokenUsage(self) -> int:
        return self._token_usage


@pytest.mark.asyncio
@pytest.mark.regression
async def test_game_loop_reaches_mafia_win_and_emits_game_over_message(monkeypatch) -> None:
    monkeypatch.setattr(game_manager_module, "GPTPlayer", ScriptedGPTPlayer)
    monkeypatch.setattr(game_manager_module.random, "shuffle", lambda _: None)

    async def ws_make_convo(self, convo: list[str], alivePlayers: list[Player]):
        return ("I am listening.", None)

    async def ws_cast_vote(self, alivePlayers: list[Player], convo: list[str]):
        for player in alivePlayers:
            if player.getRole() != PlayerRole.MAFIA:
                return player

        return alivePlayers[0] if alivePlayers else None

    async def ws_cast_second_vote(self, votedPlayers: list[Player], convo: list[str]):
        return votedPlayers[0] if votedPlayers else None

    async def ws_make_defense(self, alivePlayers: list[Player], convo: list[str]):
        return "I am innocent."

    monkeypatch.setattr(game_manager_module.WSPlayer, "makeConvo", ws_make_convo)
    monkeypatch.setattr(game_manager_module.WSPlayer, "castVote", ws_cast_vote)
    monkeypatch.setattr(game_manager_module.WSPlayer, "castSecondVote", ws_cast_second_vote)
    monkeypatch.setattr(game_manager_module.WSPlayer, "makeDefense", ws_make_defense)

    params = InputParams(
        playerCount=6,
        playerTypes=[
            PlayerType.Default_Derrick,
            PlayerType.Refined_Reginald,
            PlayerType.Shifty_Shelby,
            PlayerType.Quiet_Quinn,
            PlayerType.Peculiar_Polly,
        ],
        mafiaCount=2,
    )
    ws = DummyWebSocket()
    manager = game_manager_module.GameManager(inputParams=params, ws=ws)

    await manager.gameLoop()

    state = manager.getGameState()
    assert state.getWinningRole() == PlayerRole.MAFIA.value
    assert len(state.getDeadPlayers()) >= 1

    payloads = [json.loads(message) for message in ws.messages]
    payload_types = {payload["type"] for payload in payloads}

    assert "player_list" in payload_types
    assert "chat_message" in payload_types
    assert all(payload["type"] != "prompt_for_message" for payload in payloads)
    assert any(
        payload.get("type") == "chat_message"
        and "Game Over! The Mafia have won!" in payload.get("note", "")
        for payload in payloads
    )
