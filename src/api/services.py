"""
Service Layer untuk AI Learning Insight API
Berisi logika bisnis untuk setiap model ML

UPDATED: Integrasi dengan Model yang sudah diperbaiki
- Model 1: Clustering dengan 5 persona (The Sprinter, Deep Diver, Night Owl, Struggler, Consistent)
- Model 2: Advice Generation dengan Gemini API
- Model 3: Pace Analysis dengan 3 kategori (fast/consistent/reflective learner)
"""

import joblib
import numpy as np
import pandas as pd
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Konfigurasi path model
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")


class ModelService:
    """Base service class untuk loading dan managing models"""
    
    def __init__(self):
        self.clustering_model = None
        self.clustering_scaler = None
        self.persona_detector = None  # NEW: Rule-based persona detector
        self.feature_columns = None   # NEW: Feature columns from training
        
        self.pace_model = None
        self.pace_cluster_labels = None  # NEW: Pace labels mapping
        self.pace_thresholds = None      # NEW: Feature thresholds
        
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        
        # Persona mapping - UPDATED sesuai dengan Model 1 yang diperbaiki
        self.persona_map = {
            0: {
                "label": "The Sprinter",
                "description": "Fast Learner - Cepat menyelesaikan materi dengan nilai tinggi",
                "criteria": "completion_speed rendah + avg_exam_score tinggi",
                "characteristics": [
                    "Menyelesaikan course lebih cepat dari rata-rata",
                    "Nilai ujian konsisten tinggi",
                    "Efisien dalam mengerjakan submission"
                ]
            },
            1: {
                "label": "The Deep Diver",
                "description": "Slow but Thorough - Lambat tapi teliti dan mendalam",
                "criteria": "completion_speed tinggi + avg_exam_score tinggi",
                "characteristics": [
                    "Membutuhkan waktu lebih lama untuk menyelesaikan materi",
                    "Namun nilai akhir sangat baik",
                    "Belajar dengan reflektif dan mendalam"
                ]
            },
            2: {
                "label": "The Struggler",
                "description": "Need Support - Membutuhkan bantuan ekstra",
                "criteria": "avg_exam_score rendah + submission_fail_rate tinggi",
                "characteristics": [
                    "Sering mengalami kesulitan dalam ujian",
                    "Tingkat kegagalan submission relatif tinggi",
                    "Membutuhkan dukungan dan bimbingan lebih"
                ]
            },
            3: {
                "label": "The Consistent",
                "description": "Steady Learner - Belajar rutin dan teratur",
                "criteria": "study_consistency_std rendah",
                "characteristics": [
                    "Pola belajar sangat konsisten",
                    "Durasi belajar stabil setiap hari/minggu",
                    "Disiplin dan terencana"
                ]
            },
            4: {
                "label": "The Night Owl",
                "description": "Night-time Learner - Aktif belajar di malam hari",
                "criteria": "avg_study_hour >= 19",
                "characteristics": [
                    "Mayoritas aktivitas belajar di jam 19:00 - 24:00",
                    "Konsistensi belajar cukup baik",
                    "Produktif di waktu malam"
                ]
            }
        }
        
        # Pace labels mapping - UPDATED sesuai dengan Model 3 yang diperbaiki
        self.pace_label_map = {
            0: "fast learner",
            1: "consistent learner", 
            2: "reflective learner"
        }
        
    def load_models(self):
        """Load semua model yang diperlukan"""
        try:
            # ================================================
            # Load Clustering Model (Model 1)
            # ================================================
            clustering_path = os.path.join(MODELS_DIR, "clustering_model_production.pkl")
            if os.path.exists(clustering_path):
                loaded = joblib.load(clustering_path)
                
                if isinstance(loaded, dict):
                    # Extract components from saved dictionary
                    self.clustering_model = loaded.get('clustering_model')
                    self.clustering_scaler = loaded.get('scaler')
                    self.persona_detector = loaded.get('persona_detector')
                    self.feature_columns = loaded.get('feature_columns', [
                        'avg_study_hour', 'study_consistency_std', 'completion_speed',
                        'avg_exam_score', 'submission_fail_rate', 'retry_count'
                    ])
                    
                    print(f"✓ Clustering model loaded from {clustering_path}")
                    print(f"  - Scaler: {'Yes' if self.clustering_scaler else 'No'}")
                    print(f"  - Persona detector: {'Yes' if self.persona_detector else 'No'}")
                    print(f"  - Features: {self.feature_columns}")
                else:
                    self.clustering_model = loaded
                    self.feature_columns = [
                        'avg_study_hour', 'study_consistency_std', 'completion_speed',
                        'avg_exam_score', 'submission_fail_rate', 'retry_count'
                    ]
                    print(f"✓ Clustering model loaded from {clustering_path} (legacy format)")
            else:
                print(f"⚠ Clustering model not found at {clustering_path}")
            
            # ================================================
            # Load Pace Model (Model 3)
            # ================================================
            pace_path = os.path.join(MODELS_DIR, "pace_model.pkl")
            if os.path.exists(pace_path):
                loaded = joblib.load(pace_path)
                
                if isinstance(loaded, dict):
                    self.pace_model = loaded.get('kmeans')
                    self.pace_cluster_labels = loaded.get('cluster_labels', {
                        0: 'fast learner',
                        1: 'consistent learner',
                        2: 'reflective learner'
                    })
                    self.pace_thresholds = loaded.get('feature_thresholds', {})
                    
                    print(f"✓ Pace model loaded from {pace_path}")
                    print(f"  - Cluster labels: {self.pace_cluster_labels}")
                    print(f"  - Thresholds: {list(self.pace_thresholds.keys()) if self.pace_thresholds else 'None'}")
                else:
                    self.pace_model = loaded
                    print(f"✓ Pace model loaded from {pace_path} (legacy format)")
            else:
                # Fallback to pace_model_production.pkl
                pace_prod_path = os.path.join(MODELS_DIR, "pace_model_production.pkl")
                if os.path.exists(pace_prod_path):
                    loaded = joblib.load(pace_prod_path)
                    if isinstance(loaded, dict):
                        self.pace_model = loaded.get('model') or loaded.get('kmeans')
                        self.pace_cluster_labels = loaded.get('cluster_labels', self.pace_label_map)
                    else:
                        self.pace_model = loaded
                    print(f"✓ Pace model loaded from {pace_prod_path}")
                else:
                    print(f"⚠ Pace model not found")
                
            # ================================================
            # Configure Gemini AI (Model 2)
            # ================================================
            if self.gemini_api_key:
                genai.configure(api_key=self.gemini_api_key)
                print("✓ Gemini AI configured")
            else:
                print("⚠ GEMINI_API_KEY not found in environment variables")
                
            return True
        except Exception as e:
            print(f"✗ Error loading models: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def check_health(self) -> Dict:
        """Check status semua model"""
        return {
            "clustering_model": self.clustering_model is not None,
            "pace_model": self.pace_model is not None,
            "advice_generator": bool(self.gemini_api_key)
        }


class PersonaService(ModelService):
    """Service untuk Model 1: Clustering/Persona Prediction"""
    
    def predict_persona(self, user_data: Dict) -> Dict:
        """
        Prediksi persona user berdasarkan data dari database
        
        UPDATED: Menggunakan rule-based persona assignment sesuai dengan
        kriteria yang didefinisikan di Model 1 yang sudah diperbaiki.
        
        Args:
            user_data: Dict berisi fitur user dari database
                - avg_study_hour: float (0-24)
                - study_consistency_std: float
                - completion_speed: float 
                - avg_exam_score: float (0-100)
                - submission_fail_rate: float (0-1)
                - retry_count: int
        
        Returns:
            Dict berisi persona_label, confidence, dan characteristics
        """
        # Extract features
        avg_study_hour = user_data.get('avg_study_hour', 12.0)
        study_consistency_std = user_data.get('study_consistency_std', 2.0)
        completion_speed = user_data.get('completion_speed', 1.0)
        avg_exam_score = user_data.get('avg_exam_score', 75.0)
        submission_fail_rate = user_data.get('submission_fail_rate', 0.1)
        retry_count = user_data.get('retry_count', 0)
        
        # ================================================
        # Rule-based Persona Assignment (sesuai Model 1)
        # ================================================
        # Priority order:
        # 1. The Night Owl (jam belajar >= 19)
        # 2. The Struggler (skor rendah + fail rate tinggi)
        # 3. The Sprinter (cepat + skor tinggi)
        # 4. The Deep Diver (lambat + skor tinggi)
        # 5. The Consistent (konsistensi tinggi / default)
        
        persona_label = "The Consistent"  # Default
        cluster_id = 3
        confidence = 0.7
        
        # Check Night Owl first (jam malam)
        if avg_study_hour >= 19:
            persona_label = "The Night Owl"
            cluster_id = 4
            confidence = 0.85
            
        # Check Struggler (kesulitan belajar)
        elif avg_exam_score < 60 and submission_fail_rate > 0.3:
            persona_label = "The Struggler"
            cluster_id = 2
            confidence = 0.8
            
        # Check Sprinter (cepat dan bagus)
        elif completion_speed < 0.5 and avg_exam_score >= 75:
            persona_label = "The Sprinter"
            cluster_id = 0
            confidence = 0.85
            
        # Check Deep Diver (lambat tapi bagus)
        elif completion_speed > 2.0 and avg_exam_score >= 70:
            persona_label = "The Deep Diver"
            cluster_id = 1
            confidence = 0.8
            
        # Check Consistent (jam stabil)
        elif study_consistency_std < 100:
            persona_label = "The Consistent"
            cluster_id = 3
            confidence = 0.75
        
        # Fallback: Use clustering model if available
        if self.clustering_model is not None:
            try:
                features = [
                    avg_study_hour,
                    study_consistency_std, 
                    completion_speed,
                    avg_exam_score,
                    submission_fail_rate,
                    retry_count
                ]
                
                X = np.array(features).reshape(1, -1)
                
                # Apply scaler if available
                if self.clustering_scaler is not None:
                    X = self.clustering_scaler.transform(X)
                
                # Get cluster prediction
                predicted_cluster = int(self.clustering_model.predict(X)[0])
                
                # Map to persona
                persona_info = self.persona_map.get(predicted_cluster, self.persona_map[3])
                
                # Calculate confidence from distance
                if hasattr(self.clustering_model, 'transform'):
                    distances = self.clustering_model.transform(X)[0]
                    min_distance = distances[predicted_cluster]
                    max_distance = np.max(distances)
                    confidence = 1 - (min_distance / max_distance) if max_distance > 0 else 0.75
                
                cluster_id = predicted_cluster
                persona_label = persona_info["label"]
                
            except Exception as e:
                print(f"Fallback to rule-based: {e}")
        
        # Get persona info
        persona_info = self.persona_map.get(cluster_id, self.persona_map[3])
        
        return {
            "cluster_id": cluster_id,
            "persona_label": persona_label,
            "confidence": round(float(confidence), 3),
            "description": persona_info["description"],
            "criteria": persona_info.get("criteria", ""),
            "characteristics": persona_info["characteristics"]
        }


class AdviceService(ModelService):
    """Service untuk Model 2: Personalized Advice Generation"""
    
    # Persona-specific context templates
    PERSONA_CONTEXTS = {
        'The Sprinter': """
CONTEXT PERSONA:
Siswa ini adalah Fast Learner yang menyelesaikan materi dengan CEPAT dan nilai TINGGI.
Kriteria: completion_speed rendah + avg_exam_score tinggi

FOKUS SARAN PERSONA:
- Apresiasi kecepatan dan kemampuannya
- Sarankan tantangan lebih tinggi (advanced topics, project-based learning)
- Dorong sharing knowledge dengan teman
""",
        
        'The Deep Diver': """
CONTEXT PERSONA:
Siswa ini belajar dengan tempo LAMBAT tapi MENDALAM (reflective learner).
Kriteria: completion_speed tinggi + avg_exam_score tinggi (lambat tapi nilai bagus)

FOKUS SARAN PERSONA:
- Apresiasi ketelitian dan pemahaman mendalamnya
- Sarankan tetap pertahankan kualitas, jangan terburu-buru
- Dorong dokumentasi proses belajarnya
""",
        
        'The Night Owl': """
CONTEXT PERSONA:
Siswa ini aktif belajar di MALAM HARI (jam 19.00 - 24.00).
Kriteria: avg_study_hour >= 19

FOKUS SARAN PERSONA:
- Akui jadwal belajar malamnya
- Sarankan optimasi jadwal (breaks, kesehatan mata, teknik pomodoro)
- Ingatkan pentingnya istirahat cukup dan jaga kesehatan
""",
        
        'The Struggler': """
CONTEXT PERSONA:
Siswa ini mengalami KESULITAN (nilai rendah, banyak submission/kuis gagal).
Kriteria: avg_exam_score rendah + submission_fail_rate tinggi + retry_count tinggi

FOKUS SARAN PERSONA:
- Berikan motivasi dan empati (jangan menyerah!)
- Sarankan resources tambahan (review materi, forum diskusi, mentor)
- Dorong untuk tidak menyerah, satu langkah kecil dulu
- Fokus pada pemahaman konsep dasar
""",
        
        'The Consistent': """
CONTEXT PERSONA:
Siswa ini belajar dengan RUTIN dan KONSISTEN setiap hari/minggu.
Kriteria: study_consistency_std rendah (stabil)

FOKUS SARAN PERSONA:
- Apresiasi konsistensi dan disiplinnya
- Sarankan tetap pertahankan momentum
- Dorong set target jangka panjang
- Ajarkan teknik time-blocking untuk efisiensi
"""
    }
    
    # Pace-specific context templates
    PACE_CONTEXTS = {
        'fast learner': """
CONTEXT PACE:
Berdasarkan analisis pace, siswa ini termasuk FAST LEARNER:
- Menyelesaikan banyak materi dalam waktu singkat (>5 materi/hari)
- Kecepatan belajar di atas rata-rata

FOKUS SARAN PACE:
- Pastikan pemahaman tidak dikorbankan demi kecepatan
- Dorong untuk eksplorasi topik advanced
""",

        'consistent learner': """
CONTEXT PACE:
Berdasarkan analisis pace, siswa ini termasuk CONSISTENT LEARNER:
- Belajar secara rutin dan teratur
- CV (Coefficient of Variation) mingguan rendah

FOKUS SARAN PACE:
- Pertahankan ritme belajar yang sudah baik
- Optimalkan waktu belajar dengan teknik spaced repetition
""",

        'reflective learner': """
CONTEXT PACE:
Berdasarkan analisis pace, siswa ini termasuk REFLECTIVE LEARNER:
- Menghabiskan waktu lebih untuk memahami materi secara mendalam
- Sering review materi yang sudah dipelajari

FOKUS SARAN PACE:
- Apresiasi kedalaman pemahaman
- Dorong untuk mencatat insight dan membuat rangkuman
"""
    }
    
    def generate_advice(
        self, 
        user_name: str,
        persona_label: str,
        pace_label: str = "consistent learner",
        additional_context: Optional[Dict] = None
    ) -> str:
        """
        Generate personalized advice menggunakan Gemini AI
        
        UPDATED: Menggunakan template yang sudah diperbaiki dengan
        integrasi persona dan pace context.
        
        Args:
            user_name: Nama user (display_name)
            persona_label: Label persona dari Model 1
            pace_label: Label pace dari Model 3 (fast/consistent/reflective learner)
            additional_context: Data tambahan (exam scores, stuck points, dll)
        
        Returns:
            str: Saran personal yang dihasilkan AI
        """
        if not self.gemini_api_key:
            # Fallback ke template-based advice jika Gemini tidak tersedia
            return self._generate_template_advice(user_name, persona_label, pace_label)
        
        try:
            # Build context
            avg_score = additional_context.get('avg_exam_score', 75) if additional_context else 75
            course_name = additional_context.get('course_name', 'learning journey') if additional_context else 'learning journey'
            
            # Status info dengan emoji
            if avg_score >= 85:
                status_info = "Performa sangat baik ⭐"
            elif avg_score >= 70:
                status_info = "Performa cukup baik 👍"
            elif avg_score >= 50:
                status_info = "Perlu peningkatan 📈"
            else:
                status_info = "Butuh bantuan ekstra 💪"
            
            # Get context templates
            persona_context = self.PERSONA_CONTEXTS.get(persona_label, "")
            pace_context = self.PACE_CONTEXTS.get(pace_label.lower(), "")
            
            # Build prompt
            prompt = f"""Kamu adalah AI Learning Coach untuk platform pembelajaran programming Dicoding.

DATA SISWA:
- Nama Siswa: {user_name}
- Kursus: {course_name}
- Persona Belajar: {persona_label}
- Pace Belajar: {pace_label.title()}
- Rata-rata Score Kuis: {avg_score:.1f}
- Status: {status_info}

TUGAS:
Berikan saran pembelajaran yang:
1. **Personal**: Panggil nama siswa
2. **Empatik**: Sesuai dengan persona DAN pace belajar mereka
3. **Actionable**: Berikan 1-2 saran konkret yang bisa langsung dipraktikkan

{persona_context}

{pace_context}

FORMAT OUTPUT:
- 1-2 paragraf dalam Bahasa Indonesia
- Tone: Sopan, memotivasi, dan suportif
- Hindari jargon teknis yang rumit
- Gabungkan insight dari persona DAN pace belajar
"""
            
            # Generate menggunakan Gemini
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = model.generate_content(prompt)
            
            return response.text.strip()
            
        except Exception as e:
            print(f"Error generating advice with Gemini: {str(e)}")
            return self._generate_template_advice(user_name, persona_label, pace_label)
    
    def _generate_template_advice(self, user_name: str, persona_label: str, pace_label: str = "consistent learner") -> str:
        """Fallback template-based advice generation"""
        pace_info = f"Sebagai {pace_label}, "
        
        if pace_label.lower() == "fast learner":
            pace_info += "kamu menyelesaikan materi dengan cepat"
        elif pace_label.lower() == "reflective learner":
            pace_info += "kamu belajar dengan mendalam dan reflektif"
        else:
            pace_info += "kamu belajar dengan konsisten"
        
        templates = {
            "The Sprinter": f"Halo {user_name}! Kamu adalah tipe Fast Learner yang hebat! {pace_info}. Pertahankan momentum belajarmu dan coba eksplorasi topik advanced. Kamu juga bisa membantu teman-teman yang kesulitan!",
            "The Deep Diver": f"Halo {user_name}! Kamu belajar dengan mendalam dan teliti. {pace_info}. Terus pertahankan kualitas pemahamanmu - kecepatan bukan segalanya! Coba dokumentasikan insight-insight yang kamu dapat.",
            "The Night Owl": f"Halo {user_name}! Kamu produktif di malam hari ya! {pace_info}. Jaga kesehatan dengan istirahat cukup dan gunakan teknik pomodoro untuk menjaga fokus.",
            "The Struggler": f"Halo {user_name}! Kami melihat kamu sedang menghadapi tantangan. {pace_info}. Jangan menyerah! Coba review materi dasar, join forum diskusi, atau hubungi mentor untuk bantuan. Satu langkah kecil setiap hari akan membawamu jauh!",
            "The Consistent": f"Halo {user_name}! Konsistensimu luar biasa! {pace_info}. Terus pertahankan rutinitas belajarmu yang sudah bagus. Set target jangka panjang dan gunakan teknik time-blocking untuk efisiensi!"
        }
        
        return templates.get(persona_label, f"Halo {user_name}! {pace_info}. Terus semangat dalam belajarmu!")


class PaceService(ModelService):
    """Service untuk Model 3: Learning Pace Analysis"""
    
    def analyze_pace(
        self, 
        user_data: Dict
    ) -> Dict:
        """
        Analisis kecepatan belajar user
        
        UPDATED: Menggunakan binary features sesuai dengan Model 3 yang diperbaiki:
        - fast_score: Apakah user fast learner
        - consistent_score: Apakah user consistent learner  
        - reflective_score: Apakah user reflective learner
        
        Args:
            user_data: Dict berisi data user:
                - materials_per_day: Jumlah materi per hari
                - weekly_cv: Coefficient of variation mingguan
                - completion_speed: Kecepatan penyelesaian
                
        Returns:
            Dict berisi pace analysis results
        """
        materials_per_day = user_data.get('materials_per_day', 3.0)
        weekly_cv = user_data.get('weekly_cv', 0.5)
        completion_speed = user_data.get('completion_speed', 1.0)
        
        # Thresholds sesuai dengan Model 3
        min_materials_per_day = self.pace_thresholds.get('min_materials_per_day', 5) if self.pace_thresholds else 5
        cv_median = self.pace_thresholds.get('cv_median', 0.5) if self.pace_thresholds else 0.5
        
        # Calculate binary scores
        fast_score = 1 if materials_per_day >= min_materials_per_day else 0
        consistent_score = 1 if weekly_cv <= cv_median else 0
        reflective_score = 1 if completion_speed > 1.5 else 0
        
        # Determine pace label based on scores
        if fast_score == 1 and consistent_score == 1:
            pace_label = "fast learner"
            cluster_id = 0
        elif consistent_score == 1:
            pace_label = "consistent learner"
            cluster_id = 1
        else:
            pace_label = "reflective learner"
            cluster_id = 2
        
        # Use model if available
        if self.pace_model is not None:
            try:
                features = np.array([[fast_score, consistent_score, reflective_score]])
                predicted_cluster = int(self.pace_model.predict(features)[0])
                pace_label = self.pace_cluster_labels.get(predicted_cluster, "consistent learner")
                cluster_id = predicted_cluster
            except Exception as e:
                print(f"Fallback to rule-based pace: {e}")
        
        return {
            "pace_label": pace_label,
            "cluster_id": cluster_id,
            "scores": {
                "fast_score": fast_score,
                "consistent_score": consistent_score,
                "reflective_score": reflective_score
            },
            "metrics": {
                "materials_per_day": round(materials_per_day, 2),
                "weekly_cv": round(weekly_cv, 3),
                "completion_speed": round(completion_speed, 2)
            }
        }
    
    def analyze_pace_simple(
        self, 
        user_duration: float,
        journey_stats: Dict
    ) -> Dict:
        """
        Analisis kecepatan belajar sederhana (untuk backward compatibility)
        
        Args:
            user_duration: Durasi belajar user (dalam jam)
            journey_stats: Dict berisi statistik journey
                - avg_duration: float (rata-rata durasi populasi)
                - expected_duration: float (durasi ekspektasi kurikulum)
                - journey_name: str
                - journey_id: int
        
        Returns:
            Dict berisi pace analysis results
        """
        avg_duration = journey_stats.get('avg_duration', user_duration)
        expected_duration = journey_stats.get('expected_duration', avg_duration)
        
        # Calculate pace percentage
        pace_percentage = ((avg_duration - user_duration) / avg_duration) * 100 if avg_duration > 0 else 0
        
        # Determine pace label
        if pace_percentage > 15:
            pace_label = "fast learner"
        elif pace_percentage < -15:
            pace_label = "reflective learner"
        else:
            pace_label = "consistent learner"
        
        # Calculate percentile
        if user_duration < avg_duration * 0.7:
            percentile = 90
        elif user_duration < avg_duration:
            percentile = 70
        elif user_duration < avg_duration * 1.3:
            percentile = 50
        else:
            percentile = 30
        
        return {
            "pace_label": pace_label,
            "pace_percentage": round(pace_percentage, 2),
            "user_duration_hours": round(user_duration, 2),
            "avg_duration_hours": round(avg_duration, 2),
            "expected_duration_hours": round(expected_duration, 2),
            "percentile_rank": percentile,
            "journey_name": journey_stats.get('journey_name', 'Unknown Journey'),
            "journey_id": journey_stats.get('journey_id', 0)
        }
    
    def get_pace_insight_text(self, pace_data: Dict) -> str:
        """Generate human-readable pace insight"""
        pace_label = pace_data.get('pace_label', 'consistent learner')
        
        if pace_label == "fast learner":
            return "Kamu belajar dengan cepat dan efisien! 🚀"
        elif pace_label == "reflective learner":
            return "Kamu belajar dengan mendalam dan reflektif - bagus untuk pemahaman! 📚"
        else:
            return "Kamu belajar dengan konsisten dan teratur - pertahankan ritme ini! ⭐"


# Singleton instances
persona_service = PersonaService()
advice_service = AdviceService()
pace_service = PaceService()
