from pydantic import BaseModel
from typing import Optional


class PaceFeatures(BaseModel):
    completion_speed: float
    study_consistency_std: float
    avg_study_hour: float
    completed_modules: int
    total_modules_viewed: int


class PaceRequest(BaseModel):
    user_id: int
    features: PaceFeatures


class PaceResponse(BaseModel):
    user_id: int
    pace_label: str
    confidence: float
    insight: str


class AdviceRequest(BaseModel):
    user_id: int
    name: str
    pace_label: str
    avg_exam_score: float = 75.0
    completed_modules: int = 0
    total_modules_viewed: int = 0
    completion_speed: float = 1.0
    study_consistency_std: float = 2.0
    total_courses_enrolled: int = 0
    courses_completed: int = 0
    optimal_study_time: str = "Pagi"
    avg_study_hour: float = 12.0


class AdviceResponse(BaseModel):
    user_id: int
    name: str
    advice_text: str
    pace_context: str


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    model_loaded: bool
