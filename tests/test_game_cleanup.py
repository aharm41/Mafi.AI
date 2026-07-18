import pytest

import GameLifecycle as game_api


class FakeCache:
    instances = []

    def __init__(self, **kwargs):
        self.deleted = None
        self.closed = False
        self.instances.append(self)

    async def delete(self, *keys):
        self.deleted = keys

    async def aclose(self):
        self.closed = True


class SuccessfulGame:
    async def gameLoop(self):
        return None


class FailingGame:
    async def gameLoop(self):
        raise RuntimeError("game failed")


@pytest.mark.asyncio
@pytest.mark.parametrize("game", [SuccessfulGame(), FailingGame()])
async def test_game_completion_always_removes_valkey_state(monkeypatch, game):
    FakeCache.instances.clear()
    monkeypatch.setattr(game_api, "Redis", FakeCache)

    await game_api.run_game_and_cleanup(game, "ABC123")

    cache = FakeCache.instances[-1]
    assert cache.deleted == (
        "ABC123",
        "game:ABC123",
        "game:ABC123:players",
        "game:ABC123:relay-ready",
    )
    assert cache.closed is True
