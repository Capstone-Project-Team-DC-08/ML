"""
AI Learning Insight API - Main Application
FastAPI application untuk serving 3 model ML:
1. Model Clustering (Persona Prediction) - 5 Persona
2. Model Advice Generation (Personalized Advice) - Gemini AI
3. Model Pace Analysis (Learning Speed) - 3 Pace Categories

UPDATED: Integrasi dengan model yang sudah diperbaiki
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from datetime import datetime
from typing import List, Optional
import uvicorn

from schemas import (
    PersonaRequest, PersonaResponse, PersonaFeatures,
    AdviceRequest, AdviceResponse,
    CoursePaceRequest, CoursePaceResponse, PaceFeatures, PaceScores,
    BatchPersonaRequest, BatchPersonaResponse,
    CompleteInsightsRequest,
    HealthResponse, ErrorResponse
)
from services import persona_service, advice_service, pace_service

# Initialize FastAPI app
app = FastAPI(
    title="AI Learning Insight API",
    description="""
    API untuk sistem AI Learning Insight yang menyediakan:
    
    ## Model 1: Persona Clustering
    Identifikasi 5 tipe pembelajar:
    - **The Sprinter**: Fast Learner (cepat + nilai tinggi)
    - **The Deep Diver**: Slow but Thorough (lambat tapi mendalam)
    - **The Night Owl**: Night-time Learner (aktif jam 19-24)
    - **The Struggler**: Need Support (butuh bantuan ekstra)
    - **The Consistent**: Steady Learner (belajar rutin)
    
    ## Model 2: Personalized Advice
    Saran belajar personal menggunakan AI Gemini dengan konteks:
    - Persona dari Model 1
    - Pace dari Model 3
    
    ## Model 3: Learning Pace Analysis
    Kategorisasi pace belajar:
    - **Fast Learner**: Menyelesaikan materi dengan cepat
    - **Consistent Learner**: Belajar teratur dan stabil
    - **Reflective Learner**: Belajar mendalam dan reflektif
    
    Dikembangkan untuk integrasi dengan website pembelajaran Dicoding.
    """,
    version="1.1.0",
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
    print("🚀 Starting AI Learning Insight API v1.1.0...")
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
        "version": "1.1.0",
        "documentation": "/docs",
        "health_check": "/health",
        "models": {
            "persona": "5 types (Sprinter, Deep Diver, Night Owl, Struggler, Consistent)",
            "advice": "Gemini AI powered",
            "pace": "3 categories (fast, consistent, reflective)"
        }
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
        version="1.1.0"
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
    Prediksi tipe pembelajar (persona) berdasarkan data histori user.
    
    **5 Persona yang tersedia:**
    - **The Sprinter** (cluster 0): completion_speed rendah + avg_exam_score tinggi
    - **The Deep Diver** (cluster 1): completion_speed tinggi + avg_exam_score tinggi
    - **The Struggler** (cluster 2): avg_exam_score rendah + submission_fail_rate tinggi
    - **The Consistent** (cluster 3): study_consistency_std rendah
    - **The Night Owl** (cluster 4): avg_study_hour >= 19
    
    **Cara penggunaan:**
    - Kirim `user_id` untuk prediksi dengan mock data
    - Atau kirim `features` jika sudah menghitung fitur dari database
    """
)
async def predict_persona(request: PersonaRequest):
    """Endpoint untuk memprediksi persona user"""
    try:
        # Use features from request if provided, otherwise use defaults
        if request.features:
            user_data = {
                'avg_study_hour': request.features.avg_study_hour,
                'study_consistency_std': request.features.study_consistency_std,
                'completion_speed': request.features.completion_speed,
                'avg_exam_score': request.features.avg_exam_score,
                'submission_fail_rate': request.features.submission_fail_rate,
                'retry_count': request.features.retry_count
            }
        else:
            # Mock data for demo - tim backend akan mengganti ini
            user_data = {
                'avg_study_hour': 21.5,
                'study_consistency_std': 2.3,
                'completion_speed': 0.35,
                'avg_exam_score': 78.5,
                'submission_fail_rate': 0.15,
                'retry_count': 1
            }
        
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
            # Mock data - tim backend akan mengganti dengan query database
            user_data = {
                'avg_study_hour': 12.0,
                'study_consistency_std': 100.0,
                'completion_speed': 1.0,
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
    
    **Konteks yang digunakan:**
    - Persona label (dari Model 1)
    - Pace label (dari Model 3)
    - Context tambahan (skor ujian, nama kursus)
    
    **Output:**
    Teks saran personal dalam Bahasa Indonesia yang:
    - Personal (menyebut nama)
    - Empatik (sesuai persona dan pace)
    - Actionable (saran konkret)
    """
)
async def generate_advice(request: AdviceRequest):
    """Generate personalized advice untuk user"""
    try:
        # Get persona if not provided
        persona_label = request.persona_label
        if not persona_label:
            # Predict persona with default data
            user_data = {
                'avg_study_hour': 14.0,
                'study_consistency_std': 80.0,
                'completion_speed': 1.0,
                'avg_exam_score': request.avg_exam_score or 75.0,
                'submission_fail_rate': 0.1,
                'retry_count': 0
            }
            persona_result = persona_service.predict_persona(user_data)
            persona_label = persona_result['persona_label']
        
        # Get pace label
        pace_label = request.pace_label or "consistent learner"
        
        # Additional context
        additional_context = {
            'avg_exam_score': request.avg_exam_score or 75.0,
            'course_name': request.course_name or 'learning journey'
        }
        
        # Generate advice
        advice_text = advice_service.generate_advice(
            user_name=request.name,
            persona_label=persona_label,
            pace_label=pace_label,
            additional_context=additional_context
        )
        
        return AdviceResponse(
            user_id=request.user_id,
            name=request.name,
            advice_text=advice_text,
            persona_context=persona_label,
            pace_context=pace_label,
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
    Analisis kecepatan belajar user.
    
    **3 Kategori Pace:**
    - **Fast Learner**: Menyelesaikan materi dengan cepat (>5 materi/hari)
    - **Consistent Learner**: Belajar teratur dan stabil (CV rendah)
    - **Reflective Learner**: Belajar mendalam dan reflektif
    
    **Cara penggunaan:**
    - Kirim `user_id` dan `journey_id` untuk analisis
    - Opsional: kirim `features` jika sudah menghitung dari database
    """
)
async def analyze_pace(request: CoursePaceRequest):
    """Analyze learning pace untuk user - Updated for Classification Model"""
    try:
        # Use features if provided (Classification Model features)
        if request.features:
            # Features for Classification Model:
            # completion_speed, study_consistency_std, avg_study_hour, 
            # completed_modules, total_modules_viewed
            user_data = {
                'completion_speed': request.features.completion_speed,
                'study_consistency_std': request.features.study_consistency_std,
                'avg_study_hour': request.features.avg_study_hour,
                'completed_modules': request.features.completed_modules,
                'total_modules_viewed': request.features.total_modules_viewed
            }
            result = pace_service.analyze_pace(user_data)
            
            # Add journey info from request when using features
            result['journey_id'] = request.journey_id
            # Mock journey name - in production, get from database
            result['journey_name'] = f"Journey {request.journey_id}"
            
            # Calculate additional metrics based on features
            # Estimate pace percentage based on completion speed
            completion_speed = request.features.completion_speed
            if completion_speed < 0.55:
                result['pace_percentage'] = round((1 - completion_speed) * 100, 2)
                result['percentile_rank'] = 85
            elif completion_speed > 1.5:
                result['pace_percentage'] = round((1 - completion_speed) * 100, 2)
                result['percentile_rank'] = 30
            else:
                result['pace_percentage'] = round((1 - completion_speed) * 100, 2)
                result['percentile_rank'] = 50
            
            # Estimate durations based on completed modules
            completed_modules = request.features.completed_modules
            total_modules = request.features.total_modules_viewed
            if total_modules > 0:
                progress = completed_modules / total_modules
                result['user_duration_hours'] = round(completed_modules * 1.5, 2)  # 1.5 hours per module
                result['avg_duration_hours'] = round(total_modules * 1.5, 2)  # Expected based on total
                result['expected_duration_hours'] = round(total_modules * 2, 2)  # 2 hours expected per module
            
        else:
            # Use simple analysis with mock data (fallback)
            journey_stats = {
                'journey_id': request.journey_id,
                'journey_name': 'Belajar Machine Learning Pemula',
                'avg_duration': 40.0,
                'expected_duration': 50.0
            }
            result = pace_service.analyze_pace_simple(30.0, journey_stats)
        
        # Get pace insight
        insight = pace_service.get_pace_insight_text(result)
        
        # Build response with all fields
        response_data = {
            "user_id": request.user_id,
            "journey_id": result.get('journey_id', request.journey_id),
            "journey_name": result.get('journey_name', f"Journey {request.journey_id}"),
            "pace_label": result.get('pace_label', 'consistent learner'),
            "cluster_id": result.get('cluster_id', 0),
            "insight": insight
        }
        
        # Add confidence if available (from Classification model)
        if 'confidence' in result:
            response_data['confidence'] = result['confidence']
        
        # Add scores if available
        if 'scores' in result:
            response_data['scores'] = PaceScores(**result['scores'])
        
        # Add metrics
        if 'pace_percentage' in result:
            response_data['pace_percentage'] = result['pace_percentage']
        if 'user_duration_hours' in result:
            response_data['user_duration_hours'] = result['user_duration_hours']
        if 'avg_duration_hours' in result:
            response_data['avg_duration_hours'] = result['avg_duration_hours']
        if 'expected_duration_hours' in result:
            response_data['expected_duration_hours'] = result['expected_duration_hours']
        if 'percentile_rank' in result:
            response_data['percentile_rank'] = result['percentile_rank']
        
        return CoursePaceResponse(**response_data)
        
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
    """Get overall pace summary untuk user"""
    try:
        # Mock data - tim backend akan mengganti dengan query database
        summary = {
            "user_id": user_id,
            "total_courses_completed": 5,
            "dominant_pace_label": "consistent learner",
            "pace_distribution": {
                "fast_learner": 2,
                "consistent_learner": 2,
                "reflective_learner": 1
            },
            "insight": "Kamu paling sering belajar dengan pace yang konsisten dan teratur!",
            "courses": []
        }
        
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
    - Persona dari Model 1 (5 tipe)
    - Personalized Advice dari Model 2 (Gemini AI)
    - Learning Pace dari Model 3 (3 kategori)
    
    Endpoint ini cocok untuk ditampilkan di dashboard user.
    """
)
async def get_complete_insights(
    user_id: int, 
    user_name: str = "User",
    journey_id: Optional[int] = None
):
    """Get complete insights untuk user (gabungan 3 model)"""
    try:
        # 1. Get Persona
        user_data = {
            'avg_study_hour': 21.5,
            'study_consistency_std': 2.3,
            'completion_speed': 0.35,
            'avg_exam_score': 78.5,
            'submission_fail_rate': 0.15,
            'retry_count': 1
        }
        persona_result = persona_service.predict_persona(user_data)
        
        # 2. Get Pace (using Classification Model features)
        pace_data = {
            'completion_speed': 0.3,
            'study_consistency_std': 50.0,
            'avg_study_hour': 14.0,
            'completed_modules': 50,
            'total_modules_viewed': 60
        }
        pace_result = pace_service.analyze_pace(pace_data)
        pace_insight = pace_service.get_pace_insight_text(pace_result)
        
        # 3. Generate Advice
        advice_text = advice_service.generate_advice(
            user_name=user_name,
            persona_label=persona_result['persona_label'],
            pace_label=pace_result.get('pace_label', 'consistent learner'),
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
                "description": persona_result.get('description', ''),
                "characteristics": persona_result['characteristics']
            },
            "learning_pace": {
                "label": pace_result.get('pace_label', 'consistent learner'),
                "scores": pace_result.get('scores', {}),
                "insight": pace_insight
            },
            "personalized_advice": {
                "text": advice_text,
                "context": {
                    "persona": persona_result['persona_label'],
                    "pace": pace_result.get('pace_label', 'consistent learner')
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
