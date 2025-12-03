"""
Service Layer untuk AI Learning Insight API
Berisi logika bisnis untuk setiap model ML
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
        self.clustering_scaler = None  # For preprocessing
        self.pace_model = None
        self.pace_scaler = None
        self.gemini_api_key = os.getenv("GEMINI_API_KEY", "")
        
        # Persona mapping untuk clustering
        self.persona_map = {
            0: {
                "label": "The Sprinter",
                "description": "Fast Learner - Cepat menyelesaikan materi dengan nilai tinggi",
                "characteristics": [
                    "Menyelesaikan course lebih cepat dari rata-rata",
                    "Nilai ujian konsisten tinggi",
                    "Efisien dalam mengerjakan submission"
                ]
            },
            1: {
                "label": "The Deep Diver",
                "description": "Slow but Thorough - Lambat tapi teliti dan mendalam",
                "characteristics": [
                    "Membutuhkan waktu lebih lama untuk menyelesaikan materi",
                    "Namun nilai akhir sangat baik",
                    "Belajar dengan reflektif dan mendalam"
                ]
            },
            2: {
                "label": "The Night Owl",
                "description": "Night-time Learner - Aktif belajar di malam hari",
                "characteristics": [
                    "Mayoritas aktivitas belajar di jam 19:00 - 24:00",
                    "Konsistensi belajar cukup baik",
                    "Produktif di waktu malam"
                ]
            },
            3: {
                "label": "The Struggler",
                "description": "Need Support - Membutuhkan bantuan ekstra",
                "characteristics": [
                    "Sering mengalami kesulitan dalam ujian",
                    "Tingkat kegagalan submission relatif tinggi",
                    "Membutuhkan dukungan dan bimbingan lebih"
                ]
            },
            4: {
                "label": "The Consistent",
                "description": "Steady Learner - Belajar rutin dan teratur",
                "characteristics": [
                    "Pola belajar sangat konsisten",
                    "Durasi belajar stabil setiap hari/minggu",
                    "Disiplin dan terencana"
                ]
            }
        }
        
    def load_models(self):
        """Load semua model yang diperlukan"""
        try:
            # Load clustering model
            clustering_path = os.path.join(MODELS_DIR, "clustering_model_production.pkl")
            if os.path.exists(clustering_path):
                loaded = joblib.load(clustering_path)
                # Check if it's a dictionary (pipeline output)
                if isinstance(loaded, dict):
                    # Extract actual model from dictionary
                    self.clustering_model = loaded.get('clustering_model') or loaded.get('kmeans') or loaded.get('model')
                    self.clustering_scaler = loaded.get('scaler')  # Get scaler for preprocessing
                    if self.clustering_model is None:
                        print(f"⚠ Could not find model in dict keys: {list(loaded.keys())}")
                    else:
                        print(f"✓ Clustering model loaded from {clustering_path} (extracted from dict)")
                        if self.clustering_scaler:
                            print(f"✓ Scaler also loaded for preprocessing")
                else:
                    self.clustering_model = loaded
                    print(f"✓ Clustering model loaded from {clustering_path}")
            else:
                print(f"⚠ Clustering model not found at {clustering_path}")
            
            # Load pace model
            pace_path = os.path.join(MODELS_DIR, "pace_model_production.pkl")
            if os.path.exists(pace_path):
                loaded = joblib.load(pace_path)
                # Check if it's a dictionary
                if isinstance(loaded, dict):
                    self.pace_model = loaded.get('model') or loaded.get('regressor') or loaded.get('pace_model')
                    self.pace_scaler = loaded.get('scaler')
                    if self.pace_model is None:
                        print(f"⚠ Could not find model in dict keys: {list(loaded.keys())}")
                    else:
                        print(f"✓ Pace model loaded from {pace_path} (extracted from dict)")
                        if self.pace_scaler:
                            print(f"✓ Scaler also loaded for preprocessing")
                else:
                    self.pace_model = loaded
                    print(f"✓ Pace model loaded from {pace_path}")
            else:
                print(f"⚠ Pace model not found at {pace_path}")
                
            # Configure Gemini AI untuk advice generation
            if self.gemini_api_key:
                genai.configure(api_key=self.gemini_api_key)
                print("✓ Gemini AI configured")
            else:
                print("⚠ GEMINI_API_KEY not found in environment variables")
                
            return True
        except Exception as e:
            print(f"✗ Error loading models: {str(e)}")
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
        
        Args:
            user_data: Dict berisi fitur user dari database
                - avg_study_hour: float
                - study_consistency_std: float
                - completion_speed: float
                - avg_exam_score: float
                - submission_fail_rate: float
                - retry_count: int
        
        Returns:
            Dict berisi cluster_id, persona_label, confidence, dan characteristics
        """
        if self.clustering_model is None:
            raise ValueError("Clustering model belum di-load")
        
        # Prepare features (sesuaikan urutan dengan training)
        features = [
            user_data.get('avg_study_hour', 12.0),
            user_data.get('study_consistency_std', 2.0),
            user_data.get('completion_speed', 30.0),
            user_data.get('avg_exam_score', 75.0),
            user_data.get('submission_fail_rate', 0.1),
            user_data.get('retry_count', 0)
        ]
        
        X = np.array(features).reshape(1, -1)
        
        # Apply scaler if available
        if self.clustering_scaler is not None:
            X = self.clustering_scaler.transform(X)
        
        # Predict cluster
        cluster_id = int(self.clustering_model.predict(X)[0])
        
        # Get distance to cluster centers untuk confidence score
        if hasattr(self.clustering_model, 'transform'):
            distances = self.clustering_model.transform(X)[0]
            min_distance = distances[cluster_id]
            max_distance = np.max(distances)
            confidence = 1 - (min_distance / max_distance) if max_distance > 0 else 0.5
        else:
            # Fallback confidence
            confidence = 0.75
        
        # Get persona info
        persona_info = self.persona_map.get(cluster_id, self.persona_map[0])
        
        return {
            "cluster_id": cluster_id,
            "persona_label": persona_info["label"],
            "confidence": round(float(confidence), 3),
            "characteristics": persona_info["characteristics"]
        }


class AdviceService(ModelService):
    """Service untuk Model 2: Personalized Advice Generation"""
    
    def generate_advice(
        self, 
        user_name: str,
        persona_label: str,
        pace_info: str,
        additional_context: Optional[Dict] = None
    ) -> str:
        """
        Generate personalized advice menggunakan Gemini AI
        
        Args:
            user_name: Nama user
            persona_label: Label persona dari Model 1
            pace_info: Info kecepatan dari Model 3
            additional_context: Data tambahan (exam scores, stuck points, dll)
        
        Returns:
            str: Saran personal yang dihasilkan AI
        """
        if not self.gemini_api_key:
            # Fallback ke template-based advice jika Gemini tidak tersedia
            return self._generate_template_advice(user_name, persona_label, pace_info)
        
        try:
            # Build context untuk prompt
            context_parts = [
                f"Nama siswa: {user_name}",
                f"Tipe Pembelajar (Persona): {persona_label}",
                f"Kecepatan Belajar: {pace_info}"
            ]
            
            if additional_context:
                if 'avg_exam_score' in additional_context:
                    context_parts.append(f"Rata-rata nilai ujian: {additional_context['avg_exam_score']}")
                if 'stuck_topic' in additional_context:
                    context_parts.append(f"Kesulitan di topik: {additional_context['stuck_topic']}")
                if 'completion_rate' in additional_context:
                    context_parts.append(f"Tingkat penyelesaian: {additional_context['completion_rate']}%")
            
            context = "\n".join(context_parts)
            
            # Create prompt
            prompt = f"""Kamu adalah AI mentor pembelajaran yang empatik dan membantu. 
Berikan saran personal yang actionable dan motivasional untuk siswa berdasarkan data berikut:

{context}

Berikan saran dalam format berikut:
1. Sapa siswa dengan nama mereka
2. Akui pola belajar mereka (persona)
3. Berikan observasi tentang performa mereka
4. Berikan 2-3 saran konkret yang bisa diterapkan
5. Tutup dengan motivasi positif

Gunakan bahasa Indonesia yang ramah dan tidak formal. Maksimal 150 kata.
"""
            
            # Generate menggunakan Gemini
            model = genai.GenerativeModel('gemini-2.0-flash')
            response = model.generate_content(prompt)
            
            return response.text
            
        except Exception as e:
            print(f"Error generating advice with Gemini: {str(e)}")
            return self._generate_template_advice(user_name, persona_label, pace_info)
    
    def _generate_template_advice(self, user_name: str, persona_label: str, pace_info: str) -> str:
        """Fallback template-based advice generation"""
        templates = {
            "The Sprinter": f"Halo {user_name}! Kamu adalah tipe Fast Learner yang hebat! {pace_info}. Pertahankan momentum belajarmu dan coba bantu teman-teman yang kesulitan ya!",
            "The Deep Diver": f"Halo {user_name}! Kamu belajar dengan mendalam dan teliti. {pace_info}. Terus pertahankan kualitas pemahamanmu, kecepatan bukan segalanya!",
            "The Night Owl": f"Halo {user_name}! Kamu produktif di malam hari ya! {pace_info}. Jaga kesehatan dengan istirahat cukup, dan coba variasikan jam belajar sesekali.",
            "The Struggler": f"Halo {user_name}! Kami melihat kamu sedang menghadapi tantangan. {pace_info}. Jangan menyerah! Coba hubungi mentor atau join study group untuk bantuan.",
            "The Consistent": f"Halo {user_name}! Konsistensimu luar biasa! {pace_info}. Terus pertahankan rutinitas belajarmu yang sudah bagus ini!"
        }
        
        return templates.get(persona_label, f"Halo {user_name}! {pace_info}. Terus semangat dalam belajarmu!")


class PaceService(ModelService):
    """Service untuk Model 3: Learning Pace Analysis"""
    
    def analyze_pace(
        self, 
        user_duration: float,
        journey_stats: Dict
    ) -> Dict:
        """
        Analisis kecepatan belajar user dibanding populasi
        
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
        # Positif = lebih cepat, Negatif = lebih lambat
        pace_percentage = ((avg_duration - user_duration) / avg_duration) * 100 if avg_duration > 0 else 0
        
        # Determine pace label
        if pace_percentage > 15:
            pace_label = "Fast Learner"
        elif pace_percentage < -15:
            pace_label = "Slow but Thorough"
        else:
            pace_label = "Average Pace"
        
        # Calculate percentile (estimasi sederhana)
        # Dalam implementasi real, ini akan dihitung dari database
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
        pace_pct = pace_data['pace_percentage']
        
        if pace_pct > 15:
            return f"Kamu {abs(pace_pct):.1f}% lebih cepat dari rata-rata siswa"
        elif pace_pct < -15:
            return f"Kamu {abs(pace_pct):.1f}% lebih lambat dari rata-rata siswa, tapi itu tidak masalah!"
        else:
            return "Kamu belajar dengan pace yang normal dan sehat"


# Singleton instances
persona_service = PersonaService()
advice_service = AdviceService()
pace_service = PaceService()
