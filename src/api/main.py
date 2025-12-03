"""
AI Learning Insight API - Main Application
FastAPI application untuk serving 3 model ML:
1. Model Clustering (Persona Prediction)
2. Model Advice Generation (Personalized Advice)
3. Model Pace Analysis (Learning Speed Comparison)
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import List
import uvicorn

from schemas import (
    PersonaRequest, PersonaResponse,
    AdviceRequest, AdviceResponse,
    CoursePaceRequest, CoursePaceResponse,
    BatchPersonaRequest, BatchPersonaResponse,
    HealthResponse, ErrorResponse
)
from services import persona_service, advice_service, pace_service

# Initialize FastAPI app
app = FastAPI(
    title="AI Learning Insight API",
    description="""
    API untuk sistem AI Learning Insight yang menyediakan:
    - **Persona Clustering**: Identifikasi tipe pembelajar (The Sprinter, Night Owl, dll)
    - **Personalized Advice**: Saran belajar personal menggunakan AI
    - **Learning Pace Analysis**: Analisis kecepatan belajar dibanding populasi
    
    Dikembangkan untuk integrasi dengan website pembelajaran.
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware untuk allow akses dari frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Dalam production, ganti dengan domain spesifik
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# Startup & Health Check Endpoints
# ============================================

@app.on_event("startup")
async def startup_event():
    """Load all models saat aplikasi start"""
    print("=" * 60)
    print("🚀 Starting AI Learning Insight API...")
    print("=" * 60)
    
    success = persona_service.load_models()
    
    if success:
        print("✅ All models loaded successfully!")
    else:
        print("⚠️  Some models failed to load, check logs above")
    
    print("=" * 60)
    print("📝 API Documentation available at: http://localhost:8000/docs")
    print("=" * 60)


@app.get(
    "/", 
    tags=["General"],
    summary="API Root"
)
async def root():
    """Root endpoint - menampilkan info API"""
    return {
        "message": "Welcome to AI Learning Insight API",
        "version": "1.0.0",
        "documentation": "/docs",
        "health_check": "/health"
    }


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["General"],
    summary="Health Check",
    description="Check status API dan semua model yang di-load"
)
async def health_check():
    """Health check endpoint"""
    models_status = persona_service.check_health()
    
    all_healthy = all(models_status.values())
    
    return HealthResponse(
        status="healthy" if all_healthy else "degraded",
        timestamp=datetime.now().isoformat(),
        models_loaded=models_status,
        version="1.0.0"
    )


# ============================================
# Model 1: Persona/Clustering Endpoints
# ============================================

@app.post(
    "/api/v1/persona/predict",
    response_model=PersonaResponse,
    tags=["Model 1: Persona Clustering"],
    summary="Prediksi Persona User",
    description="""
    Prediksi tipe pembelajar (persona) berdasarkan data histori user dari database.
    
    **Data yang dibutuhkan dari database:**
    - avg_study_hour: Rata-rata jam belajar (0-24)
    - study_consistency_std: Standar deviasi konsistensi
    - completion_speed: Kecepatan menyelesaikan course (jam)
    - avg_exam_score: Rata-rata nilai ujian
    - submission_fail_rate: Rasio kegagalan submission (0-1)
    - retry_count: Jumlah mengulang course
    
    **Output Persona:**
    - The Sprinter: Fast Learner
    - The Deep Diver: Slow but Thorough
    - The Night Owl: Night-time Learner
    - The Struggler: Need Support
    - The Consistent: Steady Learner
    """
)
async def predict_persona(request: PersonaRequest):
    """
    Endpoint untuk memprediksi persona user
    
    CATATAN UNTUK TIM BACKEND:
    - Ambil data user_id dari database
    - Hitung semua fitur yang dibutuhkan dari tabel terkait
    - Kirim ke endpoint ini dalam format yang sesuai
    """
    try:
        # MOCK DATA - Dalam implementasi real, data ini dari database
        # Tim backend akan mengganti ini dengan query database
        user_data = {
            'avg_study_hour': 21.5,  # Dari developer_journey_trackings
            'study_consistency_std': 2.3,  # Dari developer_journey_trackings
            'completion_speed': 35.0,  # Dari developer_journey_completions
            'avg_exam_score': 78.5,  # Dari exam_results
            'submission_fail_rate': 0.15,  # Dari developer_journey_submissions
            'retry_count': 1  # Dari developer_journey_completions
        }
        
        # TODO: Tim backend, ganti dengan:
        # user_data = fetch_user_features_from_db(request.user_id)
        
        # Predict persona
        result = persona_service.predict_persona(user_data)
        
        return PersonaResponse(
            user_id=request.user_id,
            **result
        )
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error predicting persona: {str(e)}"
        )


@app.post(
    "/api/v1/persona/batch",
    response_model=BatchPersonaResponse,
    tags=["Model 1: Persona Clustering"],
    summary="Batch Predict Persona Multiple Users",
    description="Prediksi persona untuk multiple users sekaligus (max 100 users)"
)
async def batch_predict_persona(request: BatchPersonaRequest):
    """Batch prediction untuk multiple users"""
    try:
        results = []
        
        for user_id in request.user_ids:
            # MOCK DATA - ganti dengan database query
            user_data = {
                'avg_study_hour': 12.0,
                'study_consistency_std': 2.0,
                'completion_speed': 30.0,
                'avg_exam_score': 75.0,
                'submission_fail_rate': 0.1,
                'retry_count': 0
            }
            
            result = persona_service.predict_persona(user_data)
            results.append(PersonaResponse(user_id=user_id, **result))
        
        return BatchPersonaResponse(
            results=results,
            total_processed=len(results)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error in batch prediction: {str(e)}"
        )


# ============================================
# Model 2: Advice Generation Endpoints
# ============================================

@app.post(
    "/api/v1/advice/generate",
    response_model=AdviceResponse,
    tags=["Model 2: Advice Generation"],
    summary="Generate Personalized Advice",
    description="""
    Generate saran belajar personal menggunakan AI (Gemini API).
    
    **Membutuhkan:**
    - Data user dari database
    - Hasil persona dari Model 1
    - Hasil pace dari Model 3
    - GEMINI_API_KEY di environment variables
    
    **Output:**
    Teks saran personal yang empatik dan actionable dalam Bahasa Indonesia.
    """
)
async def generate_advice(request: AdviceRequest):
    """
    Generate personalized advice untuk user
    
    CATATAN UNTUK TIM BACKEND:
    - Panggil endpoint /api/v1/persona/predict dulu untuk dapat persona
    - Panggil endpoint /api/v1/pace/analyze untuk dapat pace info
    - Gabungkan semua context dan panggil endpoint ini
    """
    try:
        # Step 1: Get persona (dari Model 1)
        # MOCK - Tim backend panggil API persona atau ambil dari cache
        persona_label = "The Night Owl"
        
        # Step 2: Get pace info (dari Model 3)
        # MOCK - Tim backend panggil API pace
        pace_info = "20% lebih cepat dari rata-rata siswa"
        
        # Step 3: Get additional context dari database (optional)
        additional_context = {
            'avg_exam_score': 78.5,
            'completion_rate': 65,
            'stuck_topic': 'Machine Learning Advanced'
        }
        
        # TODO: Tim backend, ganti dengan:
        # persona_label = get_user_persona(request.user_id)
        # pace_info = get_user_pace_insight(request.user_id)
        # additional_context = get_user_learning_context(request.user_id)
        
        # Generate advice
        advice_text = advice_service.generate_advice(
            user_name=request.name,
            persona_label=persona_label,
            pace_info=pace_info,
            additional_context=additional_context
        )
        
        return AdviceResponse(
            user_id=request.user_id,
            name=request.name,
            advice_text=advice_text,
            persona_context=persona_label,
            pace_context=pace_info,
            generated_at=datetime.now().isoformat()
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error generating advice: {str(e)}"
        )


# ============================================
# Model 3: Learning Pace Endpoints
# ============================================

@app.post(
    "/api/v1/pace/analyze",
    response_model=CoursePaceResponse,
    tags=["Model 3: Learning Pace"],
    summary="Analyze Learning Pace",
    description="""
    Analisis kecepatan belajar user pada course tertentu dibanding populasi.
    
    **Data yang dibutuhkan dari database:**
    - user_duration: Durasi user menyelesaikan course (jam)
    - avg_duration: Rata-rata durasi populasi untuk course ini
    - expected_duration: Durasi ekspektasi dari kurikulum (hours_to_study)
    
    **Output:**
    - Pace label (Fast/Average/Slow)
    - Persentase perbandingan dengan rata-rata
    - Percentile ranking
    """
)
async def analyze_pace(request: CoursePaceRequest):
    """
    Analyze learning pace untuk user pada course tertentu
    
    CATATAN UNTUK TIM BACKEND:
    - Query durasi user dari developer_journey_completions
    - Hitung rata-rata durasi dari semua user yang menyelesaikan journey ini
    - Ambil expected duration dari developer_journeys.hours_to_study
    """
    try:
        # MOCK DATA - Dalam implementasi real, data dari database
        user_duration = 30.0  # Jam yang dibutuhkan user
        
        journey_stats = {
            'journey_id': request.journey_id,
            'journey_name': 'Belajar Machine Learning Pemula',
            'avg_duration': 40.0,  # Rata-rata populasi
            'expected_duration': 50.0  # Dari hours_to_study
        }
        
        # TODO: Tim backend, ganti dengan:
        # user_duration = get_user_journey_duration(request.user_id, request.journey_id)
        # journey_stats = get_journey_statistics(request.journey_id)
        
        # Analyze pace
        result = pace_service.analyze_pace(user_duration, journey_stats)
        
        return CoursePaceResponse(
            user_id=request.user_id,
            **result
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing pace: {str(e)}"
        )


@app.get(
    "/api/v1/pace/{user_id}/summary",
    tags=["Model 3: Learning Pace"],
    summary="Get User Overall Pace Summary",
    description="Get ringkasan pace user untuk semua course yang pernah diambil"
)
async def get_pace_summary(user_id: int):
    """
    Get overall pace summary untuk user
    
    CATATAN UNTUK TIM BACKEND:
    - Query semua journey yang pernah diambil user
    - Hitung pace untuk masing-masing
    - Return summary statistics
    """
    try:
        # MOCK DATA
        summary = {
            "user_id": user_id,
            "total_courses_completed": 5,
            "average_pace_percentage": 15.5,
            "overall_pace_label": "Fast Learner",
            "fastest_course": "Python Basics",
            "slowest_course": "Advanced Machine Learning",
            "courses": []
        }
        
        # TODO: Tim backend, implement dengan:
        # summary = calculate_user_pace_summary(user_id)
        
        return summary
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting pace summary: {str(e)}"
        )


# ============================================
# Combined Insight Endpoint (All Models)
# ============================================

@app.get(
    "/api/v1/insights/{user_id}",
    tags=["Combined Insights"],
    summary="Get Complete User Insights",
    description="""
    Get complete learning insights combining all 3 models:
    - Persona dari Model 1
    - Personalized Advice dari Model 2  
    - Learning Pace dari Model 3
    
    Endpoint ini cocok untuk ditampilkan di dashboard user.
    """
)
async def get_complete_insights(user_id: int, user_name: str = "User"):
    """
    Get complete insights untuk user (gabungan 3 model)
    
    CATATAN UNTUK TIM BACKEND:
    - Ini adalah endpoint convenience yang menggabungkan semua model
    - Bisa digunakan untuk dashboard user
    - Atau bisa panggil endpoint individual jika perlu granular control
    """
    try:
        # 1. Get Persona
        user_data = {
            'avg_study_hour': 21.5,
            'study_consistency_std': 2.3,
            'completion_speed': 35.0,
            'avg_exam_score': 78.5,
            'submission_fail_rate': 0.15,
            'retry_count': 1
        }
        persona_result = persona_service.predict_persona(user_data)
        
        # 2. Get Pace (untuk last journey sebagai contoh)
        journey_stats = {
            'journey_id': 1,
            'journey_name': 'Machine Learning Basics',
            'avg_duration': 40.0,
            'expected_duration': 50.0
        }
        pace_result = pace_service.analyze_pace(30.0, journey_stats)
        pace_insight = pace_service.get_pace_insight_text(pace_result)
        
        # 3. Generate Advice
        advice_text = advice_service.generate_advice(
            user_name=user_name,
            persona_label=persona_result['persona_label'],
            pace_info=pace_insight,
            additional_context={'avg_exam_score': 78.5}
        )
        
        # Combine all
        complete_insights = {
            "user_id": user_id,
            "user_name": user_name,
            "generated_at": datetime.now().isoformat(),
            "persona": {
                "label": persona_result['persona_label'],
                "cluster_id": persona_result['cluster_id'],
                "confidence": persona_result['confidence'],
                "characteristics": persona_result['characteristics']
            },
            "learning_pace": {
                "label": pace_result['pace_label'],
                "percentage": pace_result['pace_percentage'],
                "insight": pace_insight
            },
            "personalized_advice": {
                "text": advice_text,
                "context": {
                    "persona": persona_result['persona_label'],
                    "pace": pace_insight
                }
            }
        }
        
        return complete_insights
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting complete insights: {str(e)}"
        )


# ============================================
# Error Handlers
# ============================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Custom HTTP exception handler"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.__class__.__name__,
            message=exc.detail,
            timestamp=datetime.now().isoformat()
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """General exception handler"""
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error=exc.__class__.__name__,
            message=str(exc),
            timestamp=datetime.now().isoformat()
        ).dict()
    )


# ============================================
# Main - untuk running langsung
# ============================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload saat development
        log_level="info"
    )
