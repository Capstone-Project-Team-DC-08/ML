import os
import joblib
import pandas as pd
from typing import Dict, Optional
from openai import OpenAI
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")

load_dotenv(os.path.join(BASE_DIR, ".env"))


class PaceService:
    """Service untuk klasifikasi pace belajar siswa"""
    
    LABELS = {
        0: "consistent learner",
        1: "fast learner",
        2: "reflective learner"
    }
    
    INSIGHTS = {
        "fast learner": "Kamu belajar dengan cepat dan efisien. Pertahankan momentum ini!",
        "consistent learner": "Kamu belajar dengan konsisten dan teratur. Ritme yang bagus!",
        "reflective learner": "Kamu belajar dengan mendalam dan reflektif. Bagus untuk pemahaman konsep!"
    }
    
    def __init__(self):
        self.model = None
        self.scaler = None
        self.label_encoder = None
        self.feature_cols = [
            "completion_speed", "study_consistency_std", "avg_study_hour",
            "completed_modules", "total_modules_viewed"
        ]
    
    def load_model(self):
        """Load model pace classifier"""
        model_path = os.path.join(MODELS_DIR, "pace_classifier.pkl")
        
        if not os.path.exists(model_path):
            print(f"[WARN] Model not found: {model_path}")
            return False
        
        try:
            data = joblib.load(model_path)
            self.model = data.get("model")
            self.scaler = data.get("scaler")
            self.label_encoder = data.get("label_encoder")
            
            if data.get("feature_columns"):
                self.feature_cols = data["feature_columns"]
            
            print(f"[OK] Pace model loaded")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to load model: {e}")
            return False
    
    def predict(self, features: Dict) -> Dict:
        """Prediksi pace berdasarkan fitur"""
        
        # Ekstrak nilai fitur
        values = [features.get(col, 0) for col in self.feature_cols]
        
        # Jika model tersedia, gunakan ML
        if self.model:
            try:
                X = pd.DataFrame([values], columns=self.feature_cols)
                
                if self.scaler:
                    X_scaled = self.scaler.transform(X)
                else:
                    X_scaled = X.values
                
                pred = int(self.model.predict(X_scaled)[0])
                
                # Ambil confidence dari probability
                if hasattr(self.model, "predict_proba"):
                    proba = self.model.predict_proba(X_scaled)[0]
                    conf = float(proba[pred])
                else:
                    conf = 0.85
                
                # Ambil label
                if self.label_encoder:
                    label = self.label_encoder.inverse_transform([pred])[0]
                else:
                    label = self.LABELS.get(pred, "consistent learner")
                
                return {
                    "label": label,
                    "confidence": round(conf, 3),
                    "insight": self.INSIGHTS.get(label, "")
                }
            except Exception as e:
                print(f"[ERROR] Prediction failed: {e}")
        
        # Fallback: rule-based
        speed = features.get("completion_speed", 1.0)
        
        if speed < 0.55:
            label = "fast learner"
            conf = 0.80
        elif speed > 1.5:
            label = "reflective learner"
            conf = 0.75
        else:
            label = "consistent learner"
            conf = 0.70
        
        return {
            "label": label,
            "confidence": conf,
            "insight": self.INSIGHTS.get(label, "")
        }


class AdviceService:
    """Service untuk generate saran belajar personal secara umum"""
    
    PACE_DESC = {
        "fast learner": "cepat menyerap materi dan efisien dalam belajar",
        "consistent learner": "konsisten dan teratur dalam belajar",
        "reflective learner": "mendalam dan reflektif dalam memahami materi"
    }
    
    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY", "")
        self.client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        ) if api_key else None
    
    def generate(self, name: str, pace_label: str, avg_score: float = 75.0,
                 completed_modules: int = 0, total_modules: int = 0,
                 completion_speed: float = 1.0, consistency_std: float = 2.0,
                 total_courses: int = 0, courses_completed: int = 0,
                 optimal_time: str = "Pagi") -> str:
        """Generate saran personal untuk keseluruhan perjalanan belajar"""
        
        progress = (completed_modules / total_modules * 100) if total_modules > 0 else 0
        
        if not self.client:
            return self._fallback_advice(name, pace_label, avg_score, progress, optimal_time)
        
        try:
            prompt = self._build_prompt(
                name, pace_label, avg_score, completed_modules, total_modules,
                completion_speed, consistency_std, total_courses, courses_completed,
                optimal_time
            )
            
            response = self.client.chat.completions.create(
                model="google/gemini-2.0-flash-001",
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[ERROR] AI generation failed: {e}")
            return self._fallback_advice(name, pace_label, avg_score, progress, optimal_time)
    
    def _fallback_advice(self, name: str, pace_label: str, avg_score: float, 
                         progress: float, optimal_time: str) -> str:
        """Fallback advice yang membangun"""
        
        pace_desc = self.PACE_DESC.get(pace_label, "belajar dengan baik")
        
        if avg_score < 60:
            return f"Halo {name}, sebagai {pace_label} kamu {pace_desc}. Namun nilai quiz ({avg_score:.0f}) perlu ditingkatkan. Manfaatkan waktu belajar optimalmu di {optimal_time} untuk review materi lebih intensif."
        
        if progress < 30:
            return f"Halo {name}, kamu adalah {pace_label} yang {pace_desc}. Progress ({progress:.0f}%) masih bisa ditingkatkan. Coba konsisten belajar di waktu {optimal_time} yang merupakan waktu terbaikmu."
        
        if pace_label == "fast learner":
            return f"Halo {name}! Sebagai fast learner, kamu {pace_desc}. Waktu belajar optimalmu adalah {optimal_time}. Tantang dirimu dengan materi yang lebih kompleks!"
        elif pace_label == "reflective learner":
            return f"Halo {name}! Sebagai reflective learner, kamu {pace_desc}. Waktu {optimal_time} adalah saat terbaikmu untuk deep learning. Tetap jaga ritme ini!"
        else:
            return f"Halo {name}! Sebagai consistent learner, kamu {pace_desc}. Pertahankan rutinitas belajar di waktu {optimal_time}!"
    
    def _build_prompt(self, name: str, pace_label: str, avg_score: float,
                      completed_modules: int, total_modules: int,
                      completion_speed: float, consistency_std: float,
                      total_courses: int, courses_completed: int,
                      optimal_time: str) -> str:
        """Build prompt untuk saran umum yang membangun"""
        
        progress = (completed_modules / total_modules * 100) if total_modules > 0 else 0
        course_completion = (courses_completed / total_courses * 100) if total_courses > 0 else 0
        pace_desc = self.PACE_DESC.get(pace_label, "belajar dengan baik")
        
        # Analisis kondisi
        observations = []
        suggestions = []
        
        # Nilai
        if avg_score >= 85:
            observations.append(f"nilai quiz sangat baik ({avg_score:.0f})")
        elif avg_score >= 70:
            observations.append(f"nilai quiz baik ({avg_score:.0f})")
        elif avg_score >= 50:
            observations.append(f"nilai quiz perlu ditingkatkan ({avg_score:.0f})")
            suggestions.append("review materi sebelum mengerjakan quiz")
        else:
            observations.append(f"nilai quiz masih rendah ({avg_score:.0f})")
            suggestions.append("fokus perkuat pemahaman dasar sebelum lanjut ke materi berikutnya")
        
        # Progress
        if progress >= 70:
            observations.append(f"progress belajar sangat baik ({progress:.0f}%)")
        elif progress >= 40:
            observations.append(f"progress belajar cukup ({progress:.0f}%)")
        else:
            observations.append(f"progress masih perlu ditingkatkan ({progress:.0f}%)")
            suggestions.append(f"luangkan waktu belajar rutin di {optimal_time}")
        
        # Konsistensi
        if consistency_std < 2:
            observations.append("jam belajar sangat konsisten")
        elif consistency_std > 5:
            observations.append("jam belajar kurang konsisten")
            suggestions.append(f"coba tetapkan jadwal tetap di {optimal_time}")
        
        # Kecepatan berdasarkan pace
        if pace_label == "fast learner" and completion_speed < 0.6:
            observations.append("kecepatan belajar sesuai dengan tipe fast learner")
        elif pace_label == "reflective learner" and completion_speed > 1.3:
            observations.append("tempo belajar sesuai dengan tipe reflective learner")
        elif pace_label == "consistent learner":
            observations.append("ritme belajar stabil")
        
        observations_text = ", ".join(observations) if observations else "data masih terbatas"
        suggestions_text = "; ".join(suggestions) if suggestions else "pertahankan pola belajar saat ini"
        
        return f"""Kamu adalah learning coach yang memberikan saran MEMBANGUN untuk siswa.

PROFIL SISWA:
- Nama: {name}
- Tipe Pace: {pace_label} ({pace_desc})
- Waktu Belajar Optimal: {optimal_time}

STATISTIK KESELURUHAN:
- Total kelas diikuti: {total_courses} kelas
- Kelas selesai: {courses_completed} ({course_completion:.0f}%)
- Total modul dipelajari: {completed_modules}/{total_modules} ({progress:.0f}%)
- Rata-rata nilai quiz: {avg_score:.1f}/100
- Kecepatan belajar: {completion_speed:.2f} (< 0.55 = cepat, > 1.5 = reflektif)
- Konsistensi waktu: {consistency_std:.1f} (< 2 = sangat konsisten)

OBSERVASI: {observations_text}
SARAN POTENSIAL: {suggestions_text}

INSTRUKSI:
1. Sapa dengan nama siswa
2. Jelaskan tipe pace-nya dan apa artinya (1 kalimat)
3. Sebutkan waktu belajar optimalnya
4. Berikan 1-2 saran KONKRET dan MEMBANGUN berdasarkan data
5. Jika ada yang perlu diperbaiki, sampaikan dengan cara yang memotivasi
6. Akhiri dengan kalimat penyemangat yang singkat
7. Maksimal 4-5 kalimat, Bahasa Indonesia yang natural

FOKUS: Berikan saran yang actionable dan sesuai dengan tipe pace siswa."""


# Singleton instances
pace_service = PaceService()
advice_service = AdviceService()
