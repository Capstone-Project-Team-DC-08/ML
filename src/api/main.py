from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import uvicorn

from schemas import (
    PaceRequest, PaceResponse,
    AdviceRequest, AdviceResponse,
    HealthResponse
)
from services import pace_service, advice_service

app = FastAPI(
    title="Learning Pace API",
    description="API untuk analisis pace belajar siswa",
    version="2.0.0",
    docs_url="/docs"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    print("Starting Learning Pace API...")
    pace_service.load_model()
    print("API ready at http://localhost:8000/docs")


@app.get("/")
async def root():
    return {
        "name": "Learning Pace API",
        "version": "2.0.0",
        "endpoints": {
            "pace": "/api/v1/pace/analyze",
            "advice": "/api/v1/advice/generate",
            "health": "/health"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="healthy" if pace_service.model else "degraded",
        timestamp=datetime.now().isoformat(),
        model_loaded=pace_service.model is not None
    )


@app.post("/api/v1/pace/analyze", response_model=PaceResponse)
async def analyze_pace(req: PaceRequest):
    """
    Analisis pace belajar berdasarkan 5 fitur:
    - completion_speed: rasio kecepatan (< 0.55 = fast, > 1.5 = reflective)
    - study_consistency_std: standar deviasi jam belajar
    - avg_study_hour: rata-rata jam belajar (0-24)
    - completed_modules: jumlah modul selesai
    - total_modules_viewed: total modul yang dilihat
    
    Output: fast learner, consistent learner, atau reflective learner
    """
    try:
        features = {
            "completion_speed": req.features.completion_speed,
            "study_consistency_std": req.features.study_consistency_std,
            "avg_study_hour": req.features.avg_study_hour,
            "completed_modules": req.features.completed_modules,
            "total_modules_viewed": req.features.total_modules_viewed
        }
        
        result = pace_service.predict(features)
        
        return PaceResponse(
            user_id=req.user_id,
            pace_label=result["label"],
            confidence=result["confidence"],
            insight=result["insight"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/advice/generate", response_model=AdviceResponse)
async def generate_advice(req: AdviceRequest):
    """
    Generate saran belajar personal untuk keseluruhan perjalanan belajar.
    Saran bersifat umum (tidak spesifik kelas tertentu) dan membangun.
    """
    try:
        advice = advice_service.generate(
            name=req.name,
            pace_label=req.pace_label,
            avg_score=req.avg_exam_score,
            completed_modules=req.completed_modules,
            total_modules=req.total_modules_viewed,
            completion_speed=req.completion_speed,
            consistency_std=req.study_consistency_std,
            total_courses=req.total_courses_enrolled,
            courses_completed=req.courses_completed,
            optimal_time=req.optimal_study_time,
        )
        
        return AdviceResponse(
            user_id=req.user_id,
            name=req.name,
            advice_text=advice,
            pace_context=req.pace_label
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
