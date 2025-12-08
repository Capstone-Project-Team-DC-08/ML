"""
API Schemas untuk AI Learning Insight API
Berisi definisi struktur request dan response untuk setiap endpoint

UPDATED: Disesuaikan dengan Model yang sudah diperbaiki
- Model 1: 5 Persona (Sprinter, Deep Diver, Night Owl, Struggler, Consistent)
- Model 2: Advice dengan integrasi persona + pace
- Model 3: 3 Pace Labels (fast learner, consistent learner, reflective learner)
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


# ============================================
# Model 1: Clustering/Persona Schemas
# ============================================

class PersonaFeatures(BaseModel):
    """Fitur yang dibutuhkan untuk prediksi persona"""
    avg_study_hour: float = Field(
        default=12.0, 
        ge=0, le=24,
        description="Rata-rata jam belajar (0-24)"
    )
    study_consistency_std: float = Field(
        default=2.0,
        ge=0,
        description="Standar deviasi konsistensi belajar"
    )
    completion_speed: float = Field(
        default=1.0,
        ge=0,
        description="Kecepatan penyelesaian (rasio terhadap rata-rata)"
    )
    avg_exam_score: float = Field(
        default=75.0,
        ge=0, le=100,
        description="Rata-rata nilai ujian (0-100)"
    )
    submission_fail_rate: float = Field(
        default=0.1,
        ge=0, le=1,
        description="Rasio kegagalan submission (0-1)"
    )
    retry_count: int = Field(
        default=0,
        ge=0,
        description="Jumlah retry course"
    )


class PersonaRequest(BaseModel):
    """Request untuk mendapatkan persona pengguna"""
    user_id: int = Field(..., description="ID unik pengguna dari database", example=1)
    # Optional: fitur langsung jika sudah dihitung di backend
    features: Optional[PersonaFeatures] = Field(
        default=None,
        description="Optional: Fitur user yang sudah dihitung. Jika tidak disertakan, API akan menggunakan mock data."
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 123,
                "features": {
                    "avg_study_hour": 21.5,
                    "study_consistency_std": 2.3,
                    "completion_speed": 0.35,
                    "avg_exam_score": 78.5,
                    "submission_fail_rate": 0.15,
                    "retry_count": 1
                }
            }
        }


class PersonaResponse(BaseModel):
    """Response berisi persona/cluster label pengguna"""
    user_id: int = Field(..., description="ID unik pengguna")
    persona_label: str = Field(..., description="Label persona: 'The Sprinter', 'The Deep Diver', 'The Night Owl', 'The Struggler', 'The Consistent'")
    cluster_id: int = Field(..., description="ID cluster numerik (0-4)")
    confidence: float = Field(..., description="Skor confidence clustering (0-1)")
    description: Optional[str] = Field(None, description="Deskripsi persona")
    criteria: Optional[str] = Field(None, description="Kriteria pemilihan persona")
    characteristics: List[str] = Field(..., description="Karakteristik utama persona ini")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 123,
                "persona_label": "The Night Owl",
                "cluster_id": 4,
                "confidence": 0.85,
                "description": "Night-time Learner - Aktif belajar di malam hari",
                "criteria": "avg_study_hour >= 19",
                "characteristics": [
                    "Mayoritas aktivitas belajar di jam 19:00 - 24:00",
                    "Konsistensi belajar cukup baik",
                    "Produktif di waktu malam"
                ]
            }
        }


# ============================================
# Model 2: Advice Generation Schemas
# ============================================

class AdviceRequest(BaseModel):
    """Request untuk mendapatkan saran personal"""
    user_id: int = Field(..., description="ID unik pengguna")
    name: str = Field(..., description="Nama pengguna untuk personalisasi (display_name)")
    persona_label: Optional[str] = Field(
        default=None,
        description="Label persona dari Model 1. Jika tidak disertakan, akan diprediksi otomatis."
    )
    pace_label: Optional[str] = Field(
        default=None,
        description="Label pace dari Model 3: 'fast learner', 'consistent learner', 'reflective learner'"
    )
    avg_exam_score: Optional[float] = Field(
        default=None,
        description="Rata-rata skor ujian untuk konteks tambahan"
    )
    course_name: Optional[str] = Field(
        default=None,
        description="Nama kursus yang sedang diikuti"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 123,
                "name": "Budi Santoso",
                "persona_label": "The Night Owl",
                "pace_label": "fast learner",
                "avg_exam_score": 78.5,
                "course_name": "Belajar Machine Learning"
            }
        }


class AdviceResponse(BaseModel):
    """Response berisi saran personal yang dihasilkan AI"""
    user_id: int = Field(..., description="ID unik pengguna")
    name: str = Field(..., description="Nama pengguna")
    advice_text: str = Field(..., description="Teks saran yang dihasilkan oleh AI")
    persona_context: str = Field(..., description="Konteks persona dari Model 1")
    pace_context: str = Field(..., description="Konteks pace belajar dari Model 3")
    generated_at: str = Field(..., description="Timestamp pembuatan saran")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 123,
                "name": "Budi Santoso",
                "advice_text": "Halo Budi Santoso! Sebagai Night Owl yang belajar dengan pace cepat, kamu punya potensi luar biasa! Kami sarankan untuk tetap jaga kesehatan dengan istirahat cukup dan gunakan teknik pomodoro untuk fokus optimal di malam hari. Terus eksplorasi topik-topik advanced dan jangan ragu berbagi ilmu dengan teman-teman!",
                "persona_context": "The Night Owl",
                "pace_context": "fast learner",
                "generated_at": "2025-12-05T22:30:00"
            }
        }


# ============================================
# Model 3: Course/Learning Pace Schemas
# ============================================

class PaceFeatures(BaseModel):
    """Fitur untuk analisis pace belajar - UPDATED untuk Classification Model"""
    completion_speed: float = Field(
        default=1.0,
        ge=0,
        description="Kecepatan penyelesaian (rasio vs ekspektasi)"
    )
    study_consistency_std: float = Field(
        default=100.0,
        ge=0,
        description="Standar deviasi konsistensi belajar"
    )
    avg_study_hour: float = Field(
        default=14.0,
        ge=0, le=24,
        description="Rata-rata jam belajar (0-24)"
    )
    completed_modules: int = Field(
        default=30,
        ge=0,
        description="Jumlah modul yang diselesaikan"
    )
    total_modules_viewed: int = Field(
        default=50,
        ge=0,
        description="Total modul yang dilihat"
    )


class CoursePaceRequest(BaseModel):
    """Request untuk analisis kecepatan belajar pada course tertentu"""
    user_id: int = Field(..., description="ID unik pengguna")
    journey_id: int = Field(..., description="ID course/journey yang dianalisis")
    # Optional: fitur langsung jika sudah dihitung
    features: Optional[PaceFeatures] = Field(
        default=None,
        description="Optional: Fitur pace yang sudah dihitung"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 123,
                "journey_id": 45,
                "features": {
                    "completion_speed": 0.3,
                    "study_consistency_std": 50.0,
                    "avg_study_hour": 14.0,
                    "completed_modules": 50,
                    "total_modules_viewed": 60
                }
            }
        }


class PaceScores(BaseModel):
    """Skor binary untuk pace analysis"""
    fast_score: int = Field(..., description="Apakah user fast learner (0/1)")
    consistent_score: int = Field(..., description="Apakah user consistent learner (0/1)")
    reflective_score: int = Field(..., description="Apakah user reflective learner (0/1)")


class CoursePaceResponse(BaseModel):
    """Response berisi analisis kecepatan belajar"""
    user_id: int = Field(..., description="ID unik pengguna")
    journey_id: Optional[int] = Field(None, description="ID course/journey")
    journey_name: Optional[str] = Field(None, description="Nama course/journey")
    pace_label: str = Field(..., description="Label pace: 'fast learner', 'consistent learner', 'reflective learner'")
    cluster_id: Optional[int] = Field(None, description="ID cluster pace")
    scores: Optional[PaceScores] = Field(None, description="Skor binary untuk setiap kategori")
    pace_percentage: Optional[float] = Field(None, description="Perbandingan dengan rata-rata")
    user_duration_hours: Optional[float] = Field(None, description="Durasi belajar user (jam)")
    avg_duration_hours: Optional[float] = Field(None, description="Durasi rata-rata populasi (jam)")
    expected_duration_hours: Optional[float] = Field(None, description="Durasi ekspektasi kurikulum (jam)")
    percentile_rank: Optional[float] = Field(None, description="Persentil user dibanding populasi")
    insight: Optional[str] = Field(None, description="Insight teks tentang pace belajar")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 123,
                "journey_id": 45,
                "journey_name": "Belajar Machine Learning",
                "pace_label": "fast learner",
                "cluster_id": 0,
                "scores": {
                    "fast_score": 1,
                    "consistent_score": 1,
                    "reflective_score": 0
                },
                "pace_percentage": 25.5,
                "user_duration_hours": 30.0,
                "avg_duration_hours": 40.0,
                "expected_duration_hours": 50.0,
                "percentile_rank": 75,
                "insight": "Kamu belajar dengan cepat dan efisien! 🚀"
            }
        }


# ============================================
# Combined Insights Schema
# ============================================

class CompleteInsightsRequest(BaseModel):
    """Request untuk mendapatkan complete insights (semua model)"""
    user_id: int = Field(..., description="ID unik pengguna")
    user_name: str = Field(default="User", description="Nama pengguna")
    journey_id: Optional[int] = Field(None, description="ID journey terakhir")
    # Optional: fitur jika sudah dihitung
    persona_features: Optional[PersonaFeatures] = Field(None)
    pace_features: Optional[PaceFeatures] = Field(None)
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 123,
                "user_name": "Budi Santoso",
                "journey_id": 45
            }
        }


class CompleteInsightsResponse(BaseModel):
    """Response berisi complete insights dari semua model"""
    user_id: int
    user_name: str
    generated_at: str
    persona: PersonaResponse
    learning_pace: CoursePaceResponse
    personalized_advice: AdviceResponse


# ============================================
# Batch Processing Schemas
# ============================================

class BatchPersonaRequest(BaseModel):
    """Request untuk mendapatkan persona multiple users sekaligus"""
    user_ids: List[int] = Field(..., description="List ID pengguna", max_length=100)
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_ids": [123, 456, 789]
            }
        }


class BatchPersonaResponse(BaseModel):
    """Response berisi multiple persona results"""
    results: List[PersonaResponse] = Field(..., description="List hasil persona untuk setiap user")
    total_processed: int = Field(..., description="Jumlah user yang diproses")
    

# ============================================
# Health Check & Error Schemas
# ============================================

class HealthResponse(BaseModel):
    """Response untuk health check endpoint"""
    status: str = Field(..., description="Status API: 'healthy' atau 'degraded'")
    timestamp: str = Field(..., description="Timestamp saat pengecekan")
    models_loaded: Dict[str, bool] = Field(..., description="Status loading setiap model")
    version: str = Field(default="1.0.0", description="Versi API")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2025-12-05T22:30:00",
                "models_loaded": {
                    "clustering_model": True,
                    "pace_model": True,
                    "advice_generator": True
                },
                "version": "1.0.0"
            }
        }


class ErrorResponse(BaseModel):
    """Response untuk error/exception"""
    error: str = Field(..., description="Jenis error")
    message: str = Field(..., description="Pesan error detail")
    timestamp: str = Field(..., description="Timestamp saat error terjadi")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "UserNotFound",
                "message": "User dengan ID 999 tidak ditemukan di database",
                "timestamp": "2025-12-05T22:30:00"
            }
        }