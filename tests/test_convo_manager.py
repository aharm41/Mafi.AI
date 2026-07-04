from unittest.mock import AsyncMock

import pytest

from ConvoManager import ConvoManager


@pytest.mark.asyncio
async def test_add_convo_updates_state_and_notifies_frontend() -> None:
    manager = ConvoManager()
    frontend = AsyncMock()
    manager.attach_frontend(frontend)

    await manager.addConvo("Night 1:")

    assert manager.getLastConvo() == "Night 1:\n"
    assert manager.getConvoSummary() == ["Night 1:"]
    frontend.send_message.assert_awaited_once_with("Night 1:")


@pytest.mark.asyncio
async def test_add_chat_convo_formats_and_sends_player_message() -> None:
    manager = ConvoManager()
    frontend = AsyncMock()
    manager.attach_frontend(frontend)

    await manager.addChatConvo("I suspect Bob.", "Alice")

    assert manager.getConvoSummary() == ["[Alice]: I suspect Bob."]
    frontend.send_chat_message.assert_awaited_once_with("I suspect Bob.", "Alice")


@pytest.mark.asyncio
async def test_add_kill_convo_reports_killed_player() -> None:
    manager = ConvoManager()
    frontend = AsyncMock()
    manager.attach_frontend(frontend)

    await manager.addKillConvo("Bob was killed.", "Bob")

    assert manager.getConvoSummary() == ["Bob was killed."]
    frontend.send_message.assert_awaited_once_with("Bob was killed.")
    frontend.report_player_killed.assert_awaited_once_with("Bob")


@pytest.mark.asyncio
async def test_send_all_players_forwards_roster() -> None:
    manager = ConvoManager()
    frontend = AsyncMock()
    manager.attach_frontend(frontend)

    await manager.sendAllPlayers(["A", "B", "C"])

    frontend.send_player_list.assert_awaited_once_with(["A", "B", "C"])
