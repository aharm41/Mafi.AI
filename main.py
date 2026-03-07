from typing import Any, Dict, List, Optional
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect, WebSocketException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel, Field
from GameManager import GameManager
from InputParams import InputParams
import logging

import json
import uuid
import asyncio

from GPTProfiles import PlayerType

logger = logging.getLogger('web_log')
logger.setLevel(logging.DEBUG)

fh = logging.FileHandler('web.log')
fh.setLevel(logging.DEBUG)

logger.addHandler(fh)

class InputParamsIn(BaseModel):
    playerCount: int = Field(ge=4, le=12)
    playerTypes: List[str]
    mafiaCount: Optional[int] = None

app = FastAPI()

app.state.param_sessions: Dict[str, Dict[str, Any]] = {}

@app.get("/setup", response_class=HTMLResponse)
async def setup_page():

    # Serve the HTML below (paste it in as a triple-quoted string)
    return HTMLResponse(SETUP_HTML)

@app.get("/api/player-types")
async def list_player_types():
    # Expose enum values to the frontend so the dropdown is always correct
    # Works for typical Enum definitions
    return {"playerTypes": [e.name for e in PlayerType]}

@app.post("/api/setup")
async def receive_setup(payload: InputParamsIn, request: Request):

    try:
        player_types = [PlayerType[name] for name in payload.playerTypes]
    except KeyError as e:
        raise HTTPException(400, detail=f"Unknown PlayerType: {e}")

    params = InputParams(
        playerCount=payload.playerCount,
        playerTypes=player_types,
        mafiaCount=payload.mafiaCount,
    )

    try:
        params.validate()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    sid = uuid.uuid4().hex

    app.state.param_sessions[sid] = {
        "playerCount": params.playerCount,
        "playerTypes": [pt.name for pt in player_types],  # store names, JSON-safe
        "mafiaCount": params.mafiaCount,
        "doctorCount": params.doctorCount,
        "sheriffCount": params.sheriffCount,
    }

    lobby_url = f"/lobby?sid={sid}"
    return JSONResponse({"session_id": sid, "lobby_url": lobby_url})

@app.websocket("/lobby/ws")
async def lobby_ws(ws: WebSocket):
    sid = ws.query_params.get("sid")
    if not sid:
      await ws.close(code=1008, reason="Missing session ID.")
      return

    await ws.accept()

    data = app.state.param_sessions.get(sid)
    if not data:
        logger.error(f"WebSocket connection with invalid session ID: {sid}")
        raise WebSocketException(code=1008, reason="Unknown or expired session ID.")

    try:
        inputParams = InputParams(
          data['playerCount'],
          [PlayerType[name] for name in data["playerTypes"]],
          data['mafiaCount']
        )
        inputParams.validate()
        
        gameManager = GameManager(inputParams, ws)

        funnyFile = open("funnyFile.txt", "w")

        await gameManager.gameLoop()

        print(gameManager.convoManager.getConvoSummary(), file=funnyFile)

        funnyFile.close()

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected.")
        return
    except Exception as e:
        logger.exception("Unhandled exception in lobby_ws")
        await ws.send_text(json.dumps({
            "type": "error",
            "detail": "An internal server error occurred."
        }))
        return
    
SETUP_HTML = r"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Mafi.AI — Setup</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    body { font-family: system-ui, sans-serif; padding: 24px; max-width: 920px; margin: 0 auto; }
    h1 { margin: 0 0 8px; }
    .muted { color: #666; margin-top: 0; }
    .card { border: 1px solid #ddd; border-radius: 12px; padding: 16px; margin-top: 16px; }
    .row { display: flex; gap: 12px; flex-wrap: wrap; align-items: center; }
    label { font-weight: 600; }
    input, select, button { padding: 10px; border-radius: 10px; border: 1px solid #ccc; }
    input[type="number"] { width: 140px; }
    .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
    .grid3 { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 12px; }
    .error { color: #b00020; white-space: pre-wrap; }
    .ok { color: #0a7b2c; }
    a { color: inherit; }
    .pill { display: inline-block; padding: 2px 10px; border: 1px solid #ccc; border-radius: 999px; font-size: 12px; }
    .readonly { background: #f7f7f7; }
  </style>
</head>
<body>
  <h1>Game Setup</h1>
  <p class="muted">Configure your <span class="pill">InputParams</span> and then jump into the lobby.</p>

  <div class="card">
    <div class="grid3">
      <div>
        <label for="playerCount">Total players (4–12)</label><br />
        <input id="playerCount" type="number" min="4" max="12" value="6" />
      </div>

      <div>
        <label for="mafiaCount">Mafia count (optional override)</label><br />
        <input id="mafiaCount" type="number" min="1" placeholder="auto" />
        <div class="muted" style="font-size:12px;margin-top:6px;">
          Default = max(1, playerCount // 4)
        </div>
      </div>

      <div>
        <label>Fixed roles</label><br />
        <input class="readonly" value="Doctor = 1, Sheriff = 1" disabled />
      </div>
    </div>
  </div>

  <div class="card">
    <h3 style="margin-top:0;">GPT Players</h3>
    <p class="muted" style="margin-top:0;">
      You must choose exactly <b>playerCount - 1</b> GPT player types
      (because the first player is your WebSocket player).
    </p>

    <div id="playersContainer"></div>
  </div>

  <div class="card">
    <div class="row">
      <button id="submitBtn">Create Lobby Link</button>
      <span id="status" class="muted"></span>
    </div>

    <div id="error" class="error" style="margin-top:12px;"></div>

    <div id="result" style="margin-top:12px; display:none;">
      <div class="ok">Setup accepted.</div>
      <div style="margin-top:8px;">
        <a id="lobbyLink" href="#">Go to /lobby</a>
      </div>
    </div>
  </div>

<script>
  const playerCountEl = document.getElementById("playerCount");
  const mafiaCountEl  = document.getElementById("mafiaCount");
  const playersContainer = document.getElementById("playersContainer");
  const submitBtn = document.getElementById("submitBtn");
  const statusEl = document.getElementById("status");
  const errorEl = document.getElementById("error");
  const resultEl = document.getElementById("result");
  const lobbyLinkEl = document.getElementById("lobbyLink");

  let PLAYER_TYPES = [];

  function setStatus(msg) { statusEl.textContent = msg || ""; }
  function setError(msg) { errorEl.textContent = msg || ""; }

  function clamp(n, lo, hi) {
    return Math.max(lo, Math.min(hi, n));
  }

  function buildPlayersUI() {
    const playerCount = clamp(parseInt(playerCountEl.value || "6", 10), 4, 12);
    playerCountEl.value = playerCount;

    const neededGPT = playerCount - 1;

    playersContainer.innerHTML = "";
    for (let i = 0; i < neededGPT; i++) {
      const row = document.createElement("div");
      row.className = "row";
      row.style.margin = "10px 0";

      const label = document.createElement("div");
      label.style.minWidth = "160px";
      label.innerHTML = `<b>GPT Player ${i+1}</b>`;

      const select = document.createElement("select");
      select.dataset.index = String(i);
      select.style.minWidth = "260px";

      // Option: blank (forces user to choose)
      const blank = document.createElement("option");
      blank.value = "";
      blank.textContent = "Select a PlayerType...";
      select.appendChild(blank);

      for (const t of PLAYER_TYPES) {
        const opt = document.createElement("option");
        opt.value = t;
        opt.textContent = t.replaceAll("_", " ");
        select.appendChild(opt);
      }

      row.appendChild(label);
      row.appendChild(select);
      playersContainer.appendChild(row);
    }

    resultEl.style.display = "none";
    setError("");
  }

  async function loadPlayerTypes() {
    setStatus("Loading player types...");
    const res = await fetch("/api/player-types");
    if (!res.ok) throw new Error("Failed to load /api/player-types");
    const data = await res.json();
    PLAYER_TYPES = data.playerTypes || [];
    setStatus("");
  }

  function collectPayload() {
    const playerCount = clamp(parseInt(playerCountEl.value || "6", 10), 4, 12);
    const mafiaRaw = (mafiaCountEl.value || "").trim();
    const mafiaCount = mafiaRaw === "" ? null : Number(mafiaRaw);

    const selects = playersContainer.querySelectorAll("select");
    const playerTypes = [];
    for (const s of selects) {
      const v = (s.value || "").trim();
      playerTypes.push(v);
    }

    return { playerCount, playerTypes, mafiaCount };
  }

  function clientValidate(payload) {
    const errors = [];

    // Must choose all playerTypes
    if (payload.playerTypes.some(v => !v)) {
      errors.push("Please select a PlayerType for every GPT Player slot.");
    }

    // Must match playerCount - 1
    if (payload.playerTypes.length !== payload.playerCount - 1) {
      errors.push("Internal mismatch: number of GPT players must be playerCount - 1.");
    }

    // Basic mafia sanity (server does real validation)
    if (payload.mafiaCount !== null) {
      if (!Number.isFinite(payload.mafiaCount) || payload.mafiaCount < 1) {
        errors.push("If provided, mafiaCount must be a positive integer.");
      }
    }

    return errors;
  }

  playerCountEl.addEventListener("change", buildPlayersUI);

  submitBtn.addEventListener("click", async () => {
    resultEl.style.display = "none";
    setError("");
    setStatus("Submitting...");

    const payload = collectPayload();
    const errs = clientValidate(payload);
    if (errs.length) {
      setStatus("");
      setError(errs.join("\n"));
      return;
    }

    try {
      const res = await fetch("/api/setup", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json().catch(() => ({}));

      if (!res.ok) {
        setStatus("");
        setError(data.detail || "Server rejected setup.");
        return;
      }

      setStatus("");
      resultEl.style.display = "block";
      lobbyLinkEl.href = data.lobby_url;
      lobbyLinkEl.textContent = `Go to ${data.lobby_url}`;
    } catch (e) {
      setStatus("");
      setError(String(e));
    }
  });

  (async function init() {
    try {
      await loadPlayerTypes();
      buildPlayersUI();
    } catch (e) {
      setStatus("");
      setError("Init failed: " + String(e));
    }
  })();
</script>
</body>
</html>
"""