
import pytest

import GameManager as game_manager_module
from GPTProfiles import PlayerType
from InputParams import InputParams
from Player import Player
from PlayerRoles import PlayerRole


class RecordingClientRelay:
    messages: list[dict] = []

    def __init__(self, dest: str) -> None:
        self.dest = dest

    async def send_message(self, message: str) -> None:
        self.messages.append({"type": "chat_message", "note": message})

    async def send_chat_message(self, message: str, player_name: str) -> None:
        self.messages.append({
            "type": "player_chat_message",
            "note": message,
            "player": player_name,
        })

    async def report_player_killed(self, player_name: str) -> None:
        self.messages.append({"type": "player_killed", "player": player_name})

    async def send_player_list(self, player_names: list[str]) -> None:
        self.messages.append({"type": "player_list", "players": player_names})


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
    monkeypatch.setattr(game_manager_module, "ClientRelay", RecordingClientRelay)
    RecordingClientRelay.messages.clear()

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
        humanPlayers={"player:test:host": "Host"},
        playerTypes=[
            PlayerType.Default_Derrick,
            PlayerType.Refined_Reginald,
            PlayerType.Shifty_Shelby,
            PlayerType.Quiet_Quinn,
            PlayerType.Peculiar_Polly,
        ],
        mafiaCount=2,
        broadcastDest="game:test",
    )
    manager = game_manager_module.GameManager(inputParams=params)

    await manager.gameLoop()

    state = manager.getGameState()
    assert state.getWinningRole() == PlayerRole.MAFIA.value
    assert len(state.getDeadPlayers()) >= 1

    payloads = RecordingClientRelay.messages
    payload_types = {payload["type"] for payload in payloads}

    assert "player_list" in payload_types
    assert "chat_message" in payload_types
    assert all(payload["type"] != "prompt_for_message" for payload in payloads)
    assert any(
        payload.get("type") == "chat_message"
        and "Game Over! The Mafia have won!" in payload.get("note", "")
        for payload in payloads
    )

def test_multiple_human_players_receive_unique_numbers_and_correct_ws_classification(
    monkeypatch,
) -> None:
    monkeypatch.setattr(game_manager_module, "GPTPlayer", ScriptedGPTPlayer)
    monkeypatch.setattr(game_manager_module, "ClientRelay", RecordingClientRelay)
    monkeypatch.setattr(game_manager_module.random, "shuffle", lambda _: None)

    params = InputParams(
        playerCount=4,
        humanPlayers={
            "player:test:host": "Host",
            "player:test:guest": "Guest",
        },
        playerTypes=[
            PlayerType.Default_Derrick,
            PlayerType.Refined_Reginald,
        ],
        mafiaCount=1,
        broadcastDest="game:test",
    )

    manager = game_manager_module.GameManager(inputParams=params)
    players = manager.getGameState().getAllPlayers()
    ws_players = manager.getGameState().getWsPlayers()

    assert [player.number for player in players] == [0, 1, 2, 3]
    assert [player.getName() for player in ws_players] == ["Host", "Guest"]
    assert all(player in players for player in ws_players)

