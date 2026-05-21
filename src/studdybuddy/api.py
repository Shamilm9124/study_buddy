import asyncio
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from studdybuddy.chat import answer_user_with_search_status
from studdybuddy.flashcards import generate_flashcards, generate_quiz, save_flashcards

app = FastAPI(title="Study Buddy Chat")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    query: str
    personality: str | None = None
    messages: list[Message] = Field(default_factory=list)


class ChatResponse(BaseModel):
    response: str
    live_search_used: bool = False


class FlashcardRequest(BaseModel):
    messages: list[Message]


class Flashcard(BaseModel):
    title: str
    question: str
    answer: str


class FlashcardResponse(BaseModel):
    summary: list[str]
    cards: list[Flashcard]


class QuizQuestion(BaseModel):
    title: str
    question: str
    options: list[str]
    correct_index: int
    explanation: str


class QuizResponse(BaseModel):
    summary: list[str]
    questions: list[QuizQuestion]


@app.get("/", response_class=HTMLResponse)
async def root():
    html = Path(__file__).parent / "static" / "index.html"
    return HTMLResponse(html.read_text(encoding="utf-8"))


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    loop = asyncio.get_event_loop()
    messages = [message.dict() for message in request.messages]
    try:
        result, live_search_used = await loop.run_in_executor(
            None,
            lambda: answer_user_with_search_status(
                request.query,
                request.personality,
                messages,
            ),
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="The study assistant could not generate an answer. Check the server terminal and API key setup.",
        ) from exc
    return ChatResponse(response=result, live_search_used=live_search_used)


@app.post("/api/flashcards", response_model=FlashcardResponse)
async def flashcards(request: FlashcardRequest):
    loop = asyncio.get_event_loop()
    messages = [message.dict() for message in request.messages]
    try:
        result = await loop.run_in_executor(None, lambda: generate_flashcards(messages))
        save_flashcards(result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Flashcard generation failed. Check the server terminal and API key setup.",
        ) from exc
    return FlashcardResponse(**result)


@app.post("/api/quiz", response_model=QuizResponse)
async def quiz(request: FlashcardRequest):
    loop = asyncio.get_event_loop()
    messages = [message.dict() for message in request.messages]
    try:
        result = await loop.run_in_executor(None, lambda: generate_quiz(messages))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Quiz generation failed. Check the server terminal and API key setup.",
        ) from exc
    return QuizResponse(**result)


def run():
    uvicorn.run("studdybuddy.api:app", host="0.0.0.0", port=8000, reload=True)
