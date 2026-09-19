#!/usr/bin/env python3
"""Jev Showcase — interactive lab (FastAPI).

Offline-first: operator cards, cost lab, primitives playground, patterns,
jaggedness, model card. Optional live judge against TypeSafe System One.
"""

from __future__ import annotations

import json
import os
import time
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from jev_lab.client import TypeSafeError, load_api_key, system_one
from jev_lab.cost import estimate_cost, fanout_comparison
from jev_lab.home import (
    EXAMPLES,
    HOMES,
    apply_plan,
    build_questions,
    build_state,
    clone_home,
    general_reply,
    homes_catalog,
    mock_answers,
    overlay_house,
    plan,
    public_home,
    split_request,
    trace_rows,
)
from jev_lab.policy import ticket_policy

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "7872"))
TYPESAFE_MODEL = os.getenv("TYPESAFE_MODEL", "jev-latest").strip() or "jev-latest"
TYPESAFE_BASE_URL = os.getenv("TYPESAFE_BASE_URL", "https://api.typesafe.ai").rstrip("/")
VERSION = (ROOT / "VERSION").read_text(encoding="utf-8").strip()

STATIC_DIR = ROOT / "static"
HEADER_SRC = ROOT / "assets" / "header.jpg"
HEADER_DST = STATIC_DIR / "header.jpg"
DATA = ROOT / "data"

@asynccontextmanager
async def lifespan(_app: FastAPI):
    _ensure_header()
    yield


app = FastAPI(
    title="Jev Showcase",
    description="TypeSafe Jev — System One decisions, not chat",
    version=VERSION,
    lifespan=lifespan,
)


def _ensure_header() -> None:
    STATIC_DIR.mkdir(parents=True, exist_ok=True)
    if HEADER_SRC.exists() and (
        not HEADER_DST.exists()
        or HEADER_SRC.stat().st_mtime > HEADER_DST.stat().st_mtime
    ):
        HEADER_DST.write_bytes(HEADER_SRC.read_bytes())


def _load(name: str) -> Any:
    path = DATA / name
    if not path.exists():
        raise HTTPException(404, f"Missing data file: {name}")
    return json.loads(path.read_text(encoding="utf-8"))


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {
        "ok": True,
        "model": TYPESAFE_MODEL,
        "live": bool(load_api_key()),
        "base_url": TYPESAFE_BASE_URL,
        "version": VERSION,
        "features": {
            "hidden_knowledge": True,
            "playground": True,
            "cost_lab": True,
            "patterns": True,
            "jaggedness": True,
            "scenarios": True,
            "model_card": True,
            "live_judge": bool(load_api_key()),
            "smart_home": True,
        },
    }


@app.get("/api/hidden-knowledge")
def hidden_knowledge() -> Any:
    return _load("hidden-knowledge.json")


@app.get("/api/model-card")
def model_card() -> Any:
    return _load("model-card.json")


@app.get("/api/pricing")
def pricing() -> Any:
    return _load("pricing.json")


@app.get("/api/scenarios")
def scenarios() -> Any:
    return _load("scenarios.json")


@app.get("/api/jaggedness")
def jaggedness() -> Any:
    return _load("jaggedness.json")


@app.get("/api/patterns")
def patterns() -> Any:
    return _load("patterns.json")


@app.get("/api/claims")
def claims() -> Any:
    return _load("claims.json")


@app.get("/api/playground")
def playground() -> Any:
    return _load("playground.json")


@app.get("/api/fixtures/{name}")
def fixture(name: str) -> Any:
    safe = name.replace("..", "").replace("/", "")
    path = DATA / "fixtures" / f"{safe}.json"
    if not path.exists():
        raise HTTPException(404, f"No fixture named {safe}")
    return json.loads(path.read_text(encoding="utf-8"))


class CostRequest(BaseModel):
    input_tokens: int = Field(..., ge=0, le=2_000_000)
    output_tokens: int = Field(0, ge=0, le=2_000_000)
    questions: int = Field(1, ge=1, le=500)


@app.post("/api/cost/estimate")
def cost_estimate(req: CostRequest) -> dict[str, Any]:
    return estimate_cost(req.input_tokens, req.output_tokens, questions=req.questions)


class FanoutRequest(BaseModel):
    state_tokens: int = Field(3000, ge=1, le=32_000)
    question_tokens: int = Field(80, ge=1, le=2000)
    n_questions: int = Field(13, ge=1, le=200)


@app.post("/api/cost/fanout")
def cost_fanout(req: FanoutRequest) -> dict[str, Any]:
    return fanout_comparison(req.state_tokens, req.question_tokens, req.n_questions)


class PolicyRequest(BaseModel):
    answers: dict[str, Any]


@app.post("/api/policy/ticket")
def policy_ticket(req: PolicyRequest) -> dict[str, Any]:
    return ticket_policy(req.answers)


class JudgeRequest(BaseModel):
    state: Any
    questions: dict[str, Any] | None = None
    model: str | None = None


@app.post("/api/judge")
def judge(req: JudgeRequest) -> dict[str, Any]:
    if not load_api_key():
        raise HTTPException(
            400,
            "Live judge needs TYPESAFE_API_KEY. Use playground fixtures, or set the key in .env",
        )
    questions = req.questions or _load("playground.json")["questions"]
    t0 = time.perf_counter()
    try:
        data = system_one(
            req.state,
            questions,
            model=req.model or TYPESAFE_MODEL,
            base_url=TYPESAFE_BASE_URL,
        )
    except TypeSafeError as exc:
        raise HTTPException(exc.status_code, exc.body) from exc
    latency_ms = round((time.perf_counter() - t0) * 1000)
    answers = data.get("answers") or {}
    return {
        "live": True,
        "latency_ms": latency_ms,
        "model": data.get("model"),
        "answers": answers,
        "usage": data.get("usage") or {},
        "policy": ticket_policy(answers),
    }


class HomeRun(BaseModel):
    request: str = Field(..., min_length=1, max_length=2000)
    home_id: str = "1br"
    speaking_to: str | None = None
    house: dict[str, Any] | None = None
    force: bool = False


class HomeApply(BaseModel):
    home_id: str = "1br"
    house: dict[str, Any]
    plan: dict[str, Any]
    force: bool = True


class HomeSplit(BaseModel):
    request: str = Field(..., min_length=1, max_length=2000)


def _home_or_404(home_id: str) -> dict[str, Any]:
    if home_id not in HOMES:
        raise HTTPException(404, f"Unknown home: {home_id}")
    return clone_home(home_id)


@app.get("/api/home/bootstrap")
def home_bootstrap() -> dict[str, Any]:
    return {
        "homes": homes_catalog(),
        "examples": EXAMPLES,
        "live": bool(load_api_key()),
        "houses": {key: public_home(clone_home(key)) for key in HOMES},
    }


@app.post("/api/home/run")
def home_run(req: HomeRun) -> dict[str, Any]:
    home = overlay_house(_home_or_404(req.home_id), req.house)
    questions = build_questions(home)
    state = build_state(req.request, home, req.speaking_to)
    source = "mock"
    model = "mock"
    usage: dict[str, Any] = {}
    t0 = time.perf_counter()
    answers: dict[str, Any]
    if load_api_key():
        try:
            data = system_one(
                state,
                questions,
                model=TYPESAFE_MODEL,
                base_url=TYPESAFE_BASE_URL,
            )
            answers = data.get("answers") or {}
            source = "live"
            model = data.get("model") or TYPESAFE_MODEL
            usage = data.get("usage") or {}
        except TypeSafeError:
            answers = mock_answers(req.request, home, req.speaking_to, questions)
            source = "mock_fallback"
    else:
        answers = mock_answers(req.request, home, req.speaking_to, questions)
    latency_ms = round((time.perf_counter() - t0) * 1000)
    planned = plan(answers, home, req.speaking_to)
    result = None
    reply = None
    if planned["kind"] == "general":
        reply = general_reply(req.request)
    elif planned["kind"] in {"command", "status", "unavailable"}:
        result = apply_plan(home, planned, force=req.force)
    return {
        "source": source,
        "model": model,
        "latency_ms": latency_ms,
        "usage": usage,
        "plan": planned,
        "trace": trace_rows(questions, answers, planned.get("used") or []),
        "result": result,
        "reply": reply,
        "house": public_home(home),
        "question_count": len(questions),
    }


@app.post("/api/home/apply")
def home_apply(req: HomeApply) -> dict[str, Any]:
    home = overlay_house(_home_or_404(req.home_id), req.house)
    result = apply_plan(home, req.plan, force=req.force)
    return {"result": result, "house": public_home(home)}


@app.post("/api/home/split")
def home_split(req: HomeSplit) -> dict[str, Any]:
    return {"commands": split_request(req.request), "via": "heuristic"}


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/home")
def smart_home_page() -> FileResponse:
    return FileResponse(STATIC_DIR / "home.html")


app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


if __name__ == "__main__":
    uvicorn.run("app:app", host=HOST, port=PORT, reload=False)
