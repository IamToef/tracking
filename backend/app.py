import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from typing import List, Tuple, Dict, Any, Optional

from matching_engine import MatchingEngine

app = FastAPI(title="Mentor-Student Matching System")

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "..", "data")
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")

MENTORS_CSV = os.path.join(DATA_DIR, "mentors_prod_200_enriched.csv")
STUDENTS_CSV = os.path.join(DATA_DIR, "students_prod_2000_enriched.csv")
OVERRIDES_JSON = os.path.join(DATA_DIR, "overrides.json")

# Initialize matching engine
engine = MatchingEngine(MENTORS_CSV, STUDENTS_CSV)

# Models
class MatchConfig(BaseModel):
    session_duration: int = 60
    default_same_gender: bool = True
    weight_theme: float = 0.6
    weight_jaccard: float = 0.4
    poor_fit_threshold: float = 0.2

class OverridesModel(BaseModel):
    forced: List[Tuple[str, str]] = []  # list of (student_id, mentor_id)
    blocked: List[Tuple[str, str]] = []  # list of (student_id, mentor_id)
    skipped_students: List[str] = []
    skipped_mentors: List[str] = []

class MatchRequest(BaseModel):
    config: MatchConfig
    overrides: OverridesModel

class RejectionRequest(BaseModel):
    assignments: List[Dict[str, Any]]
    config: MatchConfig
    overrides: OverridesModel
    seed: Optional[int] = None

# Routes
@app.get("/")
def get_index():
    """Serves the index.html page."""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.exists(index_path):
        return HTMLResponse(content=open(index_path, encoding="utf-8").read())
    return HTMLResponse("<h1>index.html not found!</h1>")

@app.get("/style.css")
def get_css():
    """Serves style.css."""
    css_path = os.path.join(FRONTEND_DIR, "style.css")
    if os.path.exists(css_path):
        return FileResponse(css_path, media_type="text/css")
    return HTMLResponse("", status_code=404)

@app.get("/script.js")
def get_js():
    """Serves script.js."""
    js_path = os.path.join(FRONTEND_DIR, "script.js")
    if os.path.exists(js_path):
        return FileResponse(js_path, media_type="application/javascript")
    return HTMLResponse("", status_code=404)

@app.get("/api/data")
def get_raw_data():
    """Returns raw student and mentor details for setup select boxes."""
    # Reload engine data in case files changed
    engine.load_data()
    
    mentors_list = []
    for m in engine.raw_mentors:
        mentors_list.append({
            'id': m['ID'],
            'name': m['Name'],
            'gender': m['gender'],
            'expectation': m['expectation'],
            'personalities': m['personalites']
        })
        
    students_list = []
    for s in engine.raw_students:
        students_list.append({
            'id': s['ID'],
            'name': s['Name'],
            'gender': s['gender'],
            'expectation': s['expectation'],
            'symptom': s['symptom']
        })
        
    return {
        'mentors': mentors_list,
        'students': students_list
    }

@app.get("/api/overrides")
def get_overrides():
    """Loads and returns current overrides configuration."""
    if os.path.exists(OVERRIDES_JSON):
        try:
            with open(OVERRIDES_JSON, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"forced": [], "blocked": [], "skipped_students": [], "skipped_mentors": []}

@app.post("/api/overrides")
def save_overrides(overrides: OverridesModel):
    """Saves overrides configuration to file."""
    try:
        with open(OVERRIDES_JSON, "w", encoding="utf-8") as f:
            json.dump(overrides.dict(), f, indent=2, ensure_ascii=False)
        return {"status": "success", "message": "Overrides saved successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save overrides: {str(e)}")

@app.post("/api/match")
def perform_match(request: MatchRequest):
    """Performs the matching process using matching engine."""
    engine.load_data() # Ensure fresh data
    try:
        results = engine.run_match(
            config=request.config.dict(),
            overrides=request.overrides.dict()
        )
        return results
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Matching failed: {str(e)}")

@app.post("/api/simulate-rejection")
def perform_rejection_simulation(request: RejectionRequest):
    """Simulates 20% of matched students rejecting their mentors."""
    engine.load_data()
    try:
        results = engine.simulate_rejection(
            current_assignments=request.assignments,
            config=request.config.dict(),
            overrides=request.overrides.dict(),
            seed=request.seed
        )
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    # Read host and port from environment variables or default to 0.0.0.0 and 8000
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app:app", host=host, port=port, reload=True)
