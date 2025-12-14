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
        api_key = os.getenv("OPENROUTER_API_KEY", "")
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
                model="mistralai/devstral-2512:free",
                messages=[{"role": "user", "content": prompt}]
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[ERROR] AI generation failed: {e}")
            return self._fallback_advice(name, pace_label, avg_score, progress, optimal_time)
    
    def _fallback_advice(self, name: str, pace_label: str, avg_score: float, 
                         progress: float, optimal_time: str) -> str:
        """Fallback advice - 5-6 kalimat"""
        
        pace_desc = self.PACE_DESC.get(pace_label, "belajar dengan baik")
        
        if avg_score < 60:
            return f"Hai {name}! 🌟 Senang melihat kamu terus berusaha dalam perjalanan belajarmu. Sebagai {pace_label}, kamu {pace_desc}. Nilai quiz ({avg_score:.0f}) masih bisa ditingkatkan - coba teknik active recall dan buat mind map untuk konsep penting. Waktu {optimal_time} adalah golden hour-mu, manfaatkan untuk review materi! Semangat terus, {name}! 💪"
        
        if progress < 30 and progress > 0:
            return f"Hai {name}! 🚀 Setiap perjalanan dimulai dari langkah pertama! Sebagai {pace_label}, kamu {pace_desc}. Progress {progress:.0f}% adalah awal yang bagus - tetapkan target 1-2 modul per hari. Waktu {optimal_time} adalah saat terbaikmu untuk fokus. Terus konsisten, {name}! 💪"
        
        if pace_label == "fast learner":
            return f"Hai {name}! 🚀 Keren banget! Sebagai fast learner, kamu {pace_desc}. Saatnya naik level - explore materi advanced atau bantu teman belajar. Waktu {optimal_time} adalah golden hour-mu untuk deep work. Keep pushing, {name}! 💪✨"
        
        elif pace_label == "reflective learner":
            return f"Hai {name}! 💡 Luar biasa! Sebagai reflective learner, kamu {pace_desc}. Maksimalkan ini dengan mind mapping dan journal refleksi setelah belajar. Waktu {optimal_time} sangat cocok untuk deep learning-mu. Terus pertahankan, {name}! 🌟✨"
        
        else:  # consistent learner
            return f"Hai {name}! 📊 Konsistensi adalah kuncimu! Sebagai consistent learner, kamu {pace_desc}. Coba teknik time-blocking dan set milestone mingguan untuk tracking. Waktu {optimal_time} sudah jadi sweet spot-mu - pertahankan! Keep inspiring, {name}! 💪🌟"
    
    def _build_prompt(self, name: str, pace_label: str, avg_score: float,
                      completed_modules: int, total_modules: int,
                      completion_speed: float, consistency_std: float,
                      total_courses: int, courses_completed: int,
                      optimal_time: str) -> str:
        """Build prompt untuk saran yang engaging dan actionable"""
        
        progress = (completed_modules / total_modules * 100) if total_modules > 0 else 0
        course_completion = (courses_completed / total_courses * 100) if total_courses > 0 else 0
        pace_desc = self.PACE_DESC.get(pace_label, "belajar dengan baik")
        
        # Determine strengths and areas for growth
        strengths = []
        growth_areas = []
        
        # Score analysis
        if avg_score >= 85:
            strengths.append(f"nilai quiz impresif ({avg_score:.0f}/100)")
        elif avg_score >= 70:
            strengths.append(f"nilai quiz solid ({avg_score:.0f}/100)")
        elif avg_score >= 50:
            growth_areas.append("tingkatkan nilai quiz dengan review materi")
        else:
            growth_areas.append("perkuat fondasi dengan review materi dasar")
        
        # Progress analysis
        if progress >= 70:
            strengths.append(f"progress luar biasa ({progress:.0f}%)")
        elif progress >= 40:
            strengths.append(f"progress konsisten ({progress:.0f}%)")
        elif progress > 0:
            growth_areas.append("tingkatkan frekuensi belajar")
        
        # Consistency analysis
        if consistency_std < 2:
            strengths.append("jadwal belajar sangat konsisten")
        elif consistency_std > 5:
            growth_areas.append(f"tetapkan jadwal rutin di {optimal_time}")
        
        # Course completion
        if courses_completed > 0:
            strengths.append(f"{courses_completed} kelas selesai")
        
        # Build context strings
        strengths_text = ", ".join(strengths) if strengths else "potensi besar"
        growth_text = "; ".join(growth_areas) if growth_areas else "pertahankan performa"
        
        # Pace-specific emoji and tips
        pace_config = {
            "fast learner": {"emoji": "🚀", "tip": "explore materi advanced"},
            "consistent learner": {"emoji": "📊", "tip": "jaga ritme belajar"},
            "reflective learner": {"emoji": "💡", "tip": "gunakan mind mapping"}
        }
        config = pace_config.get(pace_label, {"emoji": "✨", "tip": "terus semangat"})
        
        return f"""Kamu adalah learning coach yang hangat dan suportif. Berikan saran belajar personal.

PROFIL SISWA:
- Nama: {name}
- Tipe: {pace_label} {config['emoji']} ({pace_desc})
- Waktu Optimal: {optimal_time}
- Progress: {completed_modules}/{total_modules} modul ({progress:.0f}%)
- Nilai Quiz: {avg_score:.0f}/100
- Kelas Selesai: {courses_completed}/{total_courses}

KELEBIHAN: {strengths_text}
PENGEMBANGAN: {growth_text}

BUAT SARAN (5-6 kalimat) DENGAN STRUKTUR:
1. Sapa nama + apresiasi kelebihan (1 kalimat)
2. Jelaskan tipe pace dengan positif (1 kalimat)  
3. Berikan 2 tips praktis sesuai tipe: {config['tip']} (2 kalimat)
4. Motivasi + waktu optimal {optimal_time} (1-2 kalimat)

ATURAN:
- Bahasa Indonesia hangat, gunakan "kamu"
- Sertakan 2-3 emoji
- Fokus SOLUSI bukan masalah
- Paragraf mengalir, JANGAN bullet points

CONTOH:
"Hai Budi! 🌟 Nilai 85 dan progress 70% kamu membanggakan! Sebagai fast learner, kamu cepat menyerap materi. Saatnya naik level - coba explore materi advanced atau bantu teman belajar. Waktu Pagi adalah golden hour-mu, manfaatkan untuk hasil maksimal! Terus melangkah, {name}! 💪" """


# Singleton instances
pace_service = PaceService()
advice_service = AdviceService()
