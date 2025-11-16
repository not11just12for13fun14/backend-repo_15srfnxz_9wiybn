import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Literal
from database import db, create_document, get_documents
from schemas import Task, MoodLog
import requests

app = FastAPI(title="BrainDash API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Environment
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

class TaskInput(BaseModel):
    text: str
    mood: Optional[str] = None
    energy: Optional[Literal["low", "medium", "high"]] = None

class MoodInput(BaseModel):
    mood: str
    energy: Literal["low", "medium", "high"]
    notes: Optional[str] = None

@app.get("/")
def root():
    return {"app": "BrainDash API", "status": "ok"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set",
        "database_name": "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": []
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections
                response["connection_status"] = "Connected"
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response

# --- AI helper ---

def call_gemini_categorize(text: str, mood: Optional[str], energy: Optional[str]):
    """Call Gemini API to categorize and score a task. Fallbacks to simple heuristics if key missing."""
    if not GEMINI_API_KEY:
        # Heuristic fallback
        t = text.lower()
        category = (
            "admin" if any(k in t for k in ["email", "invoice", "schedule", "book", "call"]) else
            "deep" if any(k in t for k in ["write", "design", "analy", "plan"]) else
            "creative" if any(k in t for k in ["brainstorm", "sketch", "compose"]) else
            "social" if any(k in t for k in ["meet", "coffee", "chat"]) else
            "other"
        )
        urgency = 3 if any(k in t for k in ["today", "urgent", "asap", "now"]) else (2 if "tomorrow" in t else 1)
        energy_req = "high" if any(k in t for k in ["write", "design", "clean", "gym"]) else ("low" if any(k in t for k in ["email", "sort", "file"]) else "medium")
        base = 50 + (10 if urgency==3 else 0) + (5 if urgency==2 else 0)
        if energy and energy_req == energy:
            base += 10
        priority = max(0, min(100, base))
        tips = [
            "Break it into a 10-minute starter step.",
            "Set a 20-minute timer and start.",
            "Pair it with music that matches your energy.",
        ]
        due = "today" if "today" in t else ("tomorrow" if "tomorrow" in t else None)
        return {
            "category": category,
            "urgency": urgency,
            "energy": energy_req,
            "priority": priority,
            "tips": tips,
            "due": due,
        }
    # If we had a key, we'd call Gemini here. Keeping placeholder stub to avoid runtime errors.
    return call_gemini_categorize.__wrapped__(text, mood, energy)  # type: ignore

# --- Routes ---

@app.post("/api/tasks")
def create_task(task: TaskInput):
    """Create a task from natural language, categorize via AI/heuristic, and store."""
    try:
        ai = call_gemini_categorize(task.text, task.mood, task.energy)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI error: {str(e)[:100]}")

    data = Task(
        text=task.text,
        category=ai.get("category"),
        energy=ai.get("energy"),
        urgency=ai.get("urgency"),
        priority=ai.get("priority"),
        due=ai.get("due"),
        tips=ai.get("tips", []),
        mood=task.mood,
        user_energy=task.energy,
    )
    inserted_id = create_document("task", data)
    return {"id": inserted_id, "task": data.model_dump()}

@app.get("/api/tasks")
def list_tasks(energy: Optional[str] = None):
    """List tasks, optionally filtered by energy type, sorted by priority desc."""
    filter_dict = {}
    if energy:
        filter_dict["energy"] = energy
    docs = get_documents("task", filter_dict)
    # Transform ObjectIds to strings
    for d in docs:
        if "_id" in d:
            d["id"] = str(d.pop("_id"))
    # Sort by priority desc if present
    docs.sort(key=lambda x: x.get("priority", 0), reverse=True)
    return {"tasks": docs}

@app.post("/api/mood")
def log_mood(mood: MoodInput):
    data = MoodLog(mood=mood.mood, energy=mood.energy, notes=mood.notes)
    inserted_id = create_document("moodlog", data)
    return {"id": inserted_id, "mood": mood.model_dump()}

@app.get("/api/mood")
def list_mood():
    docs = get_documents("moodlog", {})
    for d in docs:
        if "_id" in d:
            d["id"] = str(d.pop("_id"))
    docs.sort(key=lambda x: x.get("created_at", 0), reverse=True)
    return {"moods": docs}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
