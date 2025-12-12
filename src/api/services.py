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
from openai import OpenAI
from dotenv import load_dotenv

# Konfigurasi path model
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")

# Load environment variables from root .env file
ENV_PATH = os.path.join(BASE_DIR, ".env")
load_dotenv(dotenv_path=ENV_PATH)


class ModelService:
    """Base service class untuk loading dan managing models"""
    
    def __init__(self):
        # Persona model attributes
        self.clustering_model = None
        self.clustering_scaler = None
        self.label_encoder = None        # For classification model
        self.persona_mapping = None      # Cluster to persona label mapping
        self.feature_columns = None      # Feature columns from training
        self.model_type = None           # 'classification' or 'clustering'
        
        # Pace model attributes
        self.pace_model = None
        self.pace_scaler = None          # For pace classification
        self.pace_label_encoder = None   # For pace classification
        self.pace_cluster_labels = None  # Pace labels mapping
        self.pace_feature_columns = None # Feature columns for pace
        self.pace_thresholds = None      # Feature thresholds (clustering)
        self.pace_model_type = None      # 'classification' or 'clustering'
        
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        
        # Initialize OpenRouter client
        if self.gemini_api_key:
            self.openrouter_client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=self.gemini_api_key
            )
        else:
            self.openrouter_client = None
        
        # Persona mapping - FIXED to match Classification Model's LabelEncoder order
        # Model mapping: 0=The Consistent, 1=The Deep Diver, 2=The Night Owl, 3=The Sprinter, 4=The Struggler
        self.persona_map = {
            0: {
                "label": "The Consistent",
                "description": "Steady Learner - Belajar rutin dan teratur",
                "criteria": "study_consistency_std rendah",
                "characteristics": [
                    "Pola belajar sangat konsisten",
                    "Durasi belajar stabil setiap hari/minggu",
                    "Disiplin dan terencana"
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
                "label": "The Night Owl",
                "description": "Night-time Learner - Aktif belajar di malam hari",
                "criteria": "avg_study_hour >= 19",
                "characteristics": [
                    "Mayoritas aktivitas belajar di jam 19:00 - 24:00",
                    "Konsistensi belajar cukup baik",
                    "Produktif di waktu malam"
                ]
            },
            3: {
                "label": "The Sprinter",
                "description": "Fast Learner - Cepat menyelesaikan materi dengan nilai tinggi",
                "criteria": "completion_speed rendah + avg_exam_score tinggi",
                "characteristics": [
                    "Menyelesaikan course lebih cepat dari rata-rata",
                    "Nilai ujian konsisten tinggi",
                    "Efisien dalam mengerjakan submission"
                ]
            },
            4: {
                "label": "The Struggler",
                "description": "Need Support - Membutuhkan bantuan ekstra",
                "criteria": "avg_exam_score rendah + submission_fail_rate tinggi",
                "characteristics": [
                    "Sering mengalami kesulitan dalam ujian",
                    "Tingkat kegagalan submission relatif tinggi",
                    "Membutuhkan dukungan dan bimbingan lebih"
                ]
            }
        }
        
        # Pace labels mapping - FIXED to match Classification Model's LabelEncoder order
        # Model mapping: 0=consistent learner, 1=fast learner, 2=reflective learner
        self.pace_label_map = {
            0: "consistent learner",
            1: "fast learner", 
            2: "reflective learner"
        }
        
    def load_models(self):
        """Load semua model yang diperlukan"""
        try:
            # ================================================
            # Load Persona Model (Model 1)
            # Priority: Classification model > Clustering model
            # ================================================
            
            # Try loading Classification model first (NEW - more accurate)
            classifier_path = os.path.join(MODELS_DIR, "persona_classifier.pkl")
            clustering_path = os.path.join(MODELS_DIR, "clustering_model_production.pkl")
            
            if os.path.exists(classifier_path):
                loaded = joblib.load(classifier_path)
                
                # Classification model format
                self.clustering_model = loaded.get('model')  # RandomForest classifier
                self.clustering_scaler = loaded.get('scaler')
                self.label_encoder = loaded.get('label_encoder')
                self.persona_mapping = loaded.get('persona_mapping')
                self.feature_columns = loaded.get('feature_columns', [
                    'avg_study_hour', 'study_consistency_std', 'completion_speed',
                    'avg_exam_score', 'submission_fail_rate', 'retry_count'
                ])
                self.model_type = loaded.get('model_type', 'classification')
                
                print(f"[OK] Classification model loaded from {classifier_path}")
                print(f"  - Model type: {self.model_type}")
                print(f"  - Scaler: {'Yes' if self.clustering_scaler else 'No'}")
                print(f"  - Persona mapping: {self.persona_mapping}")
                print(f"  - Features: {self.feature_columns}")
                
            elif os.path.exists(clustering_path):
                # Fallback to clustering model
                loaded = joblib.load(clustering_path)
                
                if isinstance(loaded, dict):
                    self.clustering_model = loaded.get('clustering_model')
                    self.clustering_scaler = loaded.get('scaler')
                    self.persona_mapping = loaded.get('persona_mapping')
                    self.feature_columns = loaded.get('feature_columns', [
                        'avg_study_hour', 'study_consistency_std', 'completion_speed',
                        'avg_exam_score', 'submission_fail_rate', 'retry_count'
                    ])
                else:
                    self.clustering_model = loaded
                    self.persona_mapping = None
                    self.feature_columns = [
                        'avg_study_hour', 'study_consistency_std', 'completion_speed',
                        'avg_exam_score', 'submission_fail_rate', 'retry_count'
                    ]
                
                self.model_type = 'clustering'
                print(f"[OK] Clustering model loaded from {clustering_path} (fallback)")
                print(f"  - Model type: {self.model_type}")
            else:
                print(f"[WARN] No persona model found")
            
            # ================================================
            # Load Pace Model (Model 3)
            # Priority: Classification model > Clustering model
            # ================================================
            pace_classifier_path = os.path.join(MODELS_DIR, "pace_classifier.pkl")
            pace_path = os.path.join(MODELS_DIR, "pace_model.pkl")
            
            if os.path.exists(pace_classifier_path):
                # NEW: Classification model (more accurate)
                loaded = joblib.load(pace_classifier_path)
                
                self.pace_model = loaded.get('model')  # RandomForest classifier
                self.pace_scaler = loaded.get('scaler')
                self.pace_label_encoder = loaded.get('label_encoder')
                self.pace_cluster_labels = loaded.get('pace_mapping', {
                    0: 'consistent learner',
                    1: 'fast learner',
                    2: 'reflective learner'
                })
                self.pace_feature_columns = loaded.get('feature_columns', [
                    'completion_speed', 'study_consistency_std', 'avg_study_hour',
                    'completed_modules', 'total_modules_viewed'
                ])
                self.pace_model_type = loaded.get('model_type', 'classification')
                
                print(f"[OK] Pace classification model loaded from {pace_classifier_path}")
                print(f"  - Model type: {self.pace_model_type}")
                print(f"  - Pace mapping: {self.pace_cluster_labels}")
                print(f"  - Features: {self.pace_feature_columns}")
                
            elif os.path.exists(pace_path):
                # Fallback to clustering model
                loaded = joblib.load(pace_path)
                
                if isinstance(loaded, dict):
                    self.pace_model = loaded.get('kmeans')
                    self.pace_cluster_labels = loaded.get('cluster_labels', {
                        0: 'fast learner',
                        1: 'consistent learner',
                        2: 'reflective learner'
                    })
                    self.pace_thresholds = loaded.get('feature_thresholds', {})
                else:
                    self.pace_model = loaded
                
                self.pace_model_type = 'clustering'
                print(f"[OK] Pace clustering model loaded from {pace_path} (fallback)")
                print(f"  - Model type: {self.pace_model_type}")
            else:
                print(f"[WARN] No pace model found")
                
            # ================================================
            # Configure OpenRouter AI (Model 2)
            # ================================================
            if self.gemini_api_key:
                self.openrouter_client = OpenAI(
                    base_url="https://openrouter.ai/api/v1",
                    api_key=self.gemini_api_key
                )
                print("[OK] OpenRouter AI configured")
            else:
                self.openrouter_client = None
                print("[WARN] GEMINI_API_KEY not found in environment variables")
                
            return True
        except Exception as e:
            print(f"[ERROR] Error loading models: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def check_health(self) -> Dict:
        """Check status semua model"""
        return {
            "clustering_model": self.clustering_model is not None,
            "pace_model": self.pace_model is not None,
            "advice_generator": self.openrouter_client is not None
        }


class PersonaService(ModelService):
    """Service untuk Model 1: Clustering/Persona Prediction"""
    
    def predict_persona(self, user_data: Dict) -> Dict:
        """
        Prediksi persona user berdasarkan data dari database
        
        FIXED: Menggunakan ML Model sebagai PRIMARY method.
        Rule-based hanya digunakan sebagai FALLBACK jika model tidak tersedia.
        
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
        
        # Default values (untuk fallback rule-based)
        # Note: cluster_id 0 = The Consistent berdasarkan LabelEncoder model
        persona_label = "The Consistent"
        cluster_id = 0
        confidence = 0.7
        
        # ================================================
        # PRIMARY: Use ML Model if available
        # ================================================
        if self.clustering_model is not None:
            try:
                import pandas as pd
                
                # Create DataFrame with proper feature names
                feature_names = self.feature_columns or [
                    'avg_study_hour', 'study_consistency_std', 'completion_speed',
                    'avg_exam_score', 'submission_fail_rate', 'retry_count'
                ]
                
                features = [
                    avg_study_hour,
                    study_consistency_std, 
                    completion_speed,
                    avg_exam_score,
                    submission_fail_rate,
                    retry_count
                ]
                
                X = pd.DataFrame([features], columns=feature_names)
                
                # Apply scaler if available
                if self.clustering_scaler is not None:
                    X_scaled = self.clustering_scaler.transform(X)
                else:
                    X_scaled = X.values
                
                # Get prediction from ML model
                predicted_class = int(self.clustering_model.predict(X_scaled)[0])
                
                # Get confidence using predict_proba (Classification model)
                if hasattr(self.clustering_model, 'predict_proba'):
                    # Classification model - use probability
                    proba = self.clustering_model.predict_proba(X_scaled)[0]
                    confidence = float(proba[predicted_class])
                    model_type = 'classification'
                elif hasattr(self.clustering_model, 'transform'):
                    # Clustering model - use distance
                    distances = self.clustering_model.transform(X_scaled)[0]
                    min_distance = distances[predicted_class]
                    max_distance = np.max(distances)
                    confidence = 1 - (min_distance / max_distance) if max_distance > 0 else 0.75
                    model_type = 'clustering'
                else:
                    confidence = 0.85
                    model_type = 'unknown'
                
                # Get persona label from mapping
                if hasattr(self, 'persona_mapping') and self.persona_mapping:
                    persona_label = self.persona_mapping.get(predicted_class, "The Consistent")
                elif hasattr(self, 'label_encoder') and self.label_encoder:
                    persona_label = self.label_encoder.inverse_transform([predicted_class])[0]
                else:
                    persona_info = self.persona_map.get(predicted_class, self.persona_map[3])
                    persona_label = persona_info["label"]
                
                cluster_id = predicted_class
                
                print(f"[{model_type.upper()}] Predicted: {persona_label} (confidence: {confidence:.2%})")
                
                # ================================================
                # POST-PROCESSING: Rule-Based Override
                # Override ML prediction for clear-cut cases
                # ================================================
                override_applied = False
                
                # Night Owl override (critical: study hour is definitive)
                if avg_study_hour >= 19 and avg_study_hour <= 4 and persona_label != "The Night Owl":
                    persona_label = "The Night Owl"
                    cluster_id = 2  # Based on new mapping
                    confidence = 0.90
                    override_applied = True
                    print(f"[OVERRIDE] Night Owl detected (avg_study_hour={avg_study_hour})")
                
                # Struggler override (critical: low score + high fail rate)
                elif avg_exam_score < 60 and submission_fail_rate > 0.3 and persona_label != "The Struggler":
                    persona_label = "The Struggler"
                    cluster_id = 4
                    confidence = 0.85
                    override_applied = True
                    print(f"[OVERRIDE] Struggler detected (score={avg_exam_score}, fail_rate={submission_fail_rate})")
                
                # Sprinter override (critical: fast + high score)
                elif completion_speed < 0.4 and avg_exam_score >= 80 and persona_label != "The Sprinter":
                    persona_label = "The Sprinter"
                    cluster_id = 3
                    confidence = 0.85
                    override_applied = True
                    print(f"[OVERRIDE] Sprinter detected (speed={completion_speed}, score={avg_exam_score})")
                
            except Exception as e:
                print(f"[ML Model] Error: {e}, falling back to rule-based")
                import traceback
                traceback.print_exc()
                # Fall through to rule-based below
                self.clustering_model = None  # Reset to use fallback
        
        # ================================================
        # FALLBACK: Rule-based Persona Assignment
        # Only used if ML model is not available or failed
        # ================================================
        if self.clustering_model is None:
            print("[Rule-Based] Using rule-based persona assignment as fallback")
            
            # Priority order based on criteria from notebook
            if avg_study_hour >= 19 and avg_study_hour <= 4:
                persona_label = "The Night Owl"
                cluster_id = 2
                confidence = 0.85
            elif avg_exam_score < 60 and submission_fail_rate > 0.3:
                persona_label = "The Struggler"
                cluster_id = 4
                confidence = 0.8
            elif completion_speed < 0.5 and avg_exam_score >= 75:
                persona_label = "The Sprinter"
                cluster_id = 3
                confidence = 0.85
            elif completion_speed > 2.0 and avg_exam_score >= 70:
                persona_label = "The Deep Diver"
                cluster_id = 1
                confidence = 0.8
            else:
                persona_label = "The Consistent"
                cluster_id = 0
                confidence = 0.75
        
        # Get cluster_id from persona_label if we have mapping
        if hasattr(self, 'persona_mapping') and self.persona_mapping:
            for cid, label in self.persona_mapping.items():
                if label == persona_label:
                    cluster_id = cid
                    break
        
        # Get persona info for response
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
        print(f"[DEBUG] gemini_api_key: {'SET' if self.gemini_api_key else 'NOT SET'}")
        print(f"[DEBUG] openrouter_client: {self.openrouter_client}")
        
        if not self.gemini_api_key or not self.openrouter_client:
            print("[DEBUG] Falling back to template-based advice")
            return self._generate_template_advice(user_name, persona_label, pace_label)
        
        try:
            print(additional_context)
            print("[DEBUG] Calling OpenRouter API...")
            # Build context
            avg_score = additional_context.get('avg_exam_score', 75) if additional_context else 75
            
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
            prompt = f"""Kamu adalah AI Learning Coach untuk platform pembelajaran di Pacu Pintar.

DATA SISWA:
- Nama Siswa: {user_name}
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
            
            # Generate menggunakan OpenRouter
            print("[DEBUG] Sending request to OpenRouter...")
            response = self.openrouter_client.chat.completions.create(
                model="mistralai/devstral-2512:free", #or use model: google/gemini-2.0-flash-001
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            
            result = response.choices[0].message.content.strip()
            return result
            
        except Exception as e:
            print(f"[DEBUG] Error generating advice with OpenRouter: {str(e)}")
            import traceback
            traceback.print_exc()
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
        
        UPDATED: Menggunakan Classification model sebagai primary.
        
        Args:
            user_data: Dict berisi data user:
                - completion_speed: Kecepatan penyelesaian
                - study_consistency_std: Standar deviasi konsistensi
                - avg_study_hour: Jam belajar rata-rata
                - completed_modules: Jumlah modul selesai
                - total_modules_viewed: Total modul dilihat
                
        Returns:
            Dict berisi pace analysis results
        """
        # Extract features
        completion_speed = user_data.get('completion_speed', 1.0)
        study_consistency_std = user_data.get('study_consistency_std', 100.0)
        avg_study_hour = user_data.get('avg_study_hour', 14.0)
        completed_modules = user_data.get('completed_modules', 30)
        total_modules_viewed = user_data.get('total_modules_viewed', 50)
        
        # Default values
        pace_label = "consistent learner"
        cluster_id = 0
        confidence = 0.7
        
        # ================================================
        # PRIMARY: Use Classification Model if available
        # ================================================
        if self.pace_model is not None and self.pace_model_type == 'classification':
            try:
                import pandas as pd
                
                # Create DataFrame with proper feature names
                feature_names = self.pace_feature_columns or [
                    'completion_speed', 'study_consistency_std', 'avg_study_hour',
                    'completed_modules', 'total_modules_viewed'
                ]
                
                features = [
                    completion_speed,
                    study_consistency_std,
                    avg_study_hour,
                    completed_modules,
                    total_modules_viewed
                ]
                
                X = pd.DataFrame([features], columns=feature_names)
                
                # Apply scaler
                if self.pace_scaler is not None:
                    X_scaled = self.pace_scaler.transform(X)
                else:
                    X_scaled = X.values
                
                # Get prediction
                predicted_class = int(self.pace_model.predict(X_scaled)[0])
                
                # Get confidence using predict_proba
                if hasattr(self.pace_model, 'predict_proba'):
                    proba = self.pace_model.predict_proba(X_scaled)[0]
                    confidence = float(proba[predicted_class])
                else:
                    confidence = 0.85
                
                # Get pace label
                if self.pace_cluster_labels:
                    pace_label = self.pace_cluster_labels.get(predicted_class, "consistent learner")
                elif self.pace_label_encoder:
                    pace_label = self.pace_label_encoder.inverse_transform([predicted_class])[0]
                
                cluster_id = predicted_class
                
                print(f"[CLASSIFICATION] Pace: {pace_label} (confidence: {confidence:.2%})")
                
            except Exception as e:
                print(f"[Pace Model] Error: {e}, falling back to rule-based")
                import traceback
                traceback.print_exc()
        
        # ================================================
        # FALLBACK: Rule-based Pace Assignment
        # ================================================
        elif self.pace_model is None or self.pace_model_type != 'classification':
            # Fast Learner: cepat menyelesaikan
            if completion_speed < 0.55:
                pace_label = "fast learner"
                cluster_id = 1
                confidence = 0.85
            # Reflective Learner: lebih lambat, lebih mendalam
            elif completion_speed > 1.5:
                pace_label = "reflective learner"
                cluster_id = 2
                confidence = 0.80
            # Consistent Learner: default
            else:
                pace_label = "consistent learner"
                cluster_id = 0
                confidence = 0.75
            
            print(f"[RULE-BASED] Pace: {pace_label}")
        
        return {
            "pace_label": pace_label,
            "cluster_id": cluster_id,
            "confidence": round(float(confidence), 3),
            "metrics": {
                "completion_speed": round(completion_speed, 2),
                "study_consistency_std": round(study_consistency_std, 2),
                "avg_study_hour": round(avg_study_hour, 2)
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
            return "Kamu belajar dengan cepat dan efisien! Pertahankan momentum ini."
        elif pace_label == "reflective learner":
            return "Kamu belajar dengan mendalam dan reflektif - bagus untuk pemahaman konsep!"
        else:
            return "Kamu belajar dengan konsisten dan teratur - pertahankan ritme ini!"


# Singleton instances
persona_service = PersonaService()
advice_service = AdviceService()
pace_service = PaceService()
