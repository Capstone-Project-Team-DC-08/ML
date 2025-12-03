"""
API Schemas untuk AI Learning Insight API
Berisi definisi struktur request dan response untuk setiap endpoint
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime


# ============================================
# Model 1: Clustering/Persona Schemas
# ============================================

class PersonaRequest(BaseModel):
    """Request untuk mendapatkan persona pengguna"""
    user_id: int = Field(..., description="ID unik pengguna dari database", example=1)
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 123
            }
        }


class PersonaResponse(BaseModel):
    """Response berisi persona/cluster label pengguna"""
    user_id: int = Field(..., description="ID unik pengguna")
    persona_label: str = Field(..., description="Label persona seperti 'The Night Owl', 'The Sprinter', dll")
    cluster_id: int = Field(..., description="ID cluster numerik (0-4)")
    confidence: float = Field(..., description="Skor confidence clustering (0-1)")
    characteristics: List[str] = Field(..., description="Karakteristik utama persona ini")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 123,
                "persona_label": "The Night Owl",
                "cluster_id": 2,
                "confidence": 0.85,
                "characteristics": [
                    "Aktif belajar di malam hari (19:00-24:00)",
                    "Konsistensi belajar tinggi",
                    "Nilai ujian rata-rata baik"
                ]
            }
        }


# ============================================
# Model 2: Advice Generation Schemas
# ============================================

class AdviceRequest(BaseModel):
    """Request untuk mendapatkan saran personal"""
    user_id: int = Field(..., description="ID unik pengguna")
    name: str = Field(..., description="Nama pengguna untuk personalisasi")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 123,
                "name": "Budi"
            }
        }


class AdviceResponse(BaseModel):
    """Response berisi saran personal yang dihasilkan AI"""
    user_id: int = Field(..., description="ID unik pengguna")
    name: str = Field(..., description="Nama pengguna")
    advice_text: str = Field(..., description="Teks saran yang dihasilkan oleh AI")
    persona_context: str = Field(..., description="Konteks persona dari Model 1")
    pace_context: str = Field(..., description="Konteks kecepatan belajar dari Model 3")
    generated_at: str = Field(..., description="Timestamp pembuatan saran")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 123,
                "name": "Budi",
                "advice_text": "Halo Budi! Kami melihat kamu adalah tipe 'Night Owl' yang suka belajar di malam hari...",
                "persona_context": "The Night Owl",
                "pace_context": "20% lebih cepat dari rata-rata",
                "generated_at": "2025-12-02T22:30:00"
            }
        }


# ============================================
# Model 3: Course/Learning Pace Schemas
# ============================================

class CoursePaceRequest(BaseModel):
    """Request untuk analisis kecepatan belajar pada course tertentu"""
    user_id: int = Field(..., description="ID unik pengguna")
    journey_id: int = Field(..., description="ID course/journey yang dianalisis")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 123,
                "journey_id": 45
            }
        }


class CoursePaceResponse(BaseModel):
    """Response berisi analisis kecepatan belajar dan label course"""
    user_id: int = Field(..., description="ID unik pengguna")
    journey_id: int = Field(..., description="ID course/journey")
    journey_name: str = Field(..., description="Nama course/journey")
    pace_label: str = Field(..., description="Label kecepatan: 'Fast Learner', 'Average', 'Slow but Thorough'")
    pace_percentage: float = Field(..., description="Perbandingan dengan rata-rata (positif = lebih cepat, negatif = lebih lambat)")
    user_duration_hours: float = Field(..., description="Durasi belajar user (jam)")
    avg_duration_hours: float = Field(..., description="Durasi rata-rata populasi (jam)")
    expected_duration_hours: float = Field(..., description="Durasi ekspektasi kurikulum (jam)")
    percentile_rank: float = Field(..., description="Persentil user dibanding populasi (0-100)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": 123,
                "journey_id": 45,
                "journey_name": "Belajar Machine Learning",
                "pace_label": "Fast Learner",
                "pace_percentage": 25.5,
                "user_duration_hours": 30.0,
                "avg_duration_hours": 40.0,
                "expected_duration_hours": 50.0,
                "percentile_rank": 75.5
            }
        }


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
    status: str = Field(..., description="Status API: 'healthy' atau 'unhealthy'")
    timestamp: str = Field(..., description="Timestamp saat pengecekan")
    models_loaded: Dict[str, bool] = Field(..., description="Status loading setiap model")
    version: str = Field(default="1.0.0", description="Versi API")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2025-12-02T22:30:00",
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
                "timestamp": "2025-12-02T22:30:00"
            }
        }
