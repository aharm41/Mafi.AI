import sys
import types
from pathlib import Path


GAME_LOGIC_DIR = Path(__file__).resolve().parents[1]
if str(GAME_LOGIC_DIR) not in sys.path:
    sys.path.insert(0, str(GAME_LOGIC_DIR))


# Allow imports of GPTPlayer/GameManager in environments without optional deps.
try:
    import openai  # noqa: F401
except ImportError:
    fake_openai = types.ModuleType("openai")

    class _DummyOpenAIClient:
        def __init__(self, *args, **kwargs):
            pass

    fake_openai.AsyncOpenAI = _DummyOpenAIClient
    fake_openai.OpenAI = _DummyOpenAIClient
    sys.modules["openai"] = fake_openai


try:
    import fastapi  # noqa: F401
except ImportError:
    fake_fastapi = types.ModuleType("fastapi")

    class _DummyWebSocket:
        pass

    fake_fastapi.WebSocket = _DummyWebSocket
    sys.modules["fastapi"] = fake_fastapi


try:
    import pydantic  # noqa: F401
except ImportError:
    fake_pydantic = types.ModuleType("pydantic")

    class _DummyBaseModel:
        pass

    fake_pydantic.BaseModel = _DummyBaseModel
    sys.modules["pydantic"] = fake_pydantic
