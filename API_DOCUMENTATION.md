# AI Learning Insight API - Documentation

## 📋 Overview

API ini menyediakan layanan Machine Learning untuk platform pembelajaran dengan 3 model utama:

1. **Model 1: Persona Classification** - Mengklasifikasikan tipe pembelajar (Random Forest)
2. **Model 2: Advice Generation** - Menghasilkan saran personal dengan AI (Gemini)
3. **Model 3: Pace Classification** - Mengklasifikasikan kecepatan belajar (Random Forest)

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Setup Environment
```bash
cp .env.example .env
# Edit .env dan tambahkan GEMINI_API_KEY
```

### 3. Run API Server
```bash
cd src/api
python main.py
```

### 4. Test API
```bash
python src/test_api.py
```

## 📌 Endpoints

### Health Check
```
GET /health
```
Response:
```json
{
  "status": "healthy",
  "models_loaded": {
    "clustering_model": true,
    "pace_model": true,
    "advice_generator": true
  }
}
```

---

### Model 1: Persona Classification

**POST** `/api/v1/persona/predict`

**Request:**
```json
{
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
```

**Response:**
```json
{
  "user_id": 123,
  "persona_label": "The Night Owl",
  "cluster_id": 2,
  "confidence": 0.85,
  "description": "Night-time Learner - Aktif belajar di malam hari",
  "criteria": "avg_study_hour >= 19",
  "characteristics": [
    "Mayoritas aktivitas belajar di jam 19:00 - 24:00",
    "Konsistensi belajar cukup baik",
    "Produktif di waktu malam"
  ]
}
```

**5 Persona yang tersedia (Classification Model - LabelEncoder Order):**

| Class | Persona | Deskripsi | Kriteria |
|-------|---------|-----------|----------|
| 0 | The Consistent | Steady Learner | `study_consistency_std` rendah |
| 1 | The Deep Diver | Slow but Thorough | `completion_speed` tinggi + `avg_exam_score` tinggi |
| 2 | The Night Owl | Night-time Learner | `avg_study_hour >= 19` |
| 3 | The Sprinter | Fast Learner | `completion_speed` rendah + `avg_exam_score` tinggi |
| 4 | The Struggler | Need Support | `avg_exam_score` rendah + `submission_fail_rate` tinggi |

---

### Model 2: Advice Generation

**POST** `/api/v1/advice/generate`

**Request:**
```json
{
  "user_id": 123,
  "name": "Budi Santoso",
  "persona_label": "The Night Owl",
  "pace_label": "fast learner",
  "avg_exam_score": 78.5,
  "course_name": "Belajar Machine Learning"
}
```

**Response:**
```json
{
  "user_id": 123,
  "name": "Budi Santoso",
  "advice_text": "Halo Budi Santoso! Sebagai Night Owl yang belajar dengan pace cepat...",
  "persona_context": "The Night Owl",
  "pace_context": "fast learner",
  "generated_at": "2025-12-05T22:30:00"
}
```

---

### Model 3: Pace Classification

**POST** `/api/v1/pace/analyze`

**Request:**
```json
{
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
```

**Response:**
```json
{
  "user_id": 123,
  "journey_id": 45,
  "journey_name": "Belajar Machine Learning",
  "pace_label": "fast learner",
  "cluster_id": 1,
  "confidence": 0.92,
  "pace_percentage": 70.0,
  "user_duration_hours": 75.0,
  "avg_duration_hours": 90.0,
  "expected_duration_hours": 120.0,
  "percentile_rank": 85,
  "insight": "Kamu belajar dengan cepat dan efisien! 🚀"
}
```

**3 Pace Categories (Classification Model - LabelEncoder Order):**

| Class | Label | Deskripsi | Kriteria |
|-------|-------|-----------|----------|
| 0 | Consistent Learner | Belajar teratur dan stabil | `weekly_cv` rendah |
| 1 | Fast Learner | Belajar cepat dan efisien | `completion_speed < 0.55` |
| 2 | Reflective Learner | Belajar mendalam dan reflektif | `completion_speed > 1.5` |

---

### Combined Insights

**GET** `/api/v1/insights/{user_id}?user_name=Budi`

Menggabungkan semua 3 model dalam satu response.

---

## 🔧 Backend Integration Guide

### ⚠️ PENTING: Fitur Harus Dihitung dari Database

Fitur seperti `avg_study_hour`, `completion_speed`, dll. **TIDAK ADA** di tabel database secara langsung. 
Fitur-fitur ini harus **DIHITUNG** dari data mentah. 

📄 **Lihat panduan lengkap di**: `BACKEND_FEATURE_CALCULATION_GUIDE.md`

### Flow Integrasi:

```
┌────────────────────────────────────────────────────────────┐
│                     YOUR BACKEND                           │
├────────────────────────────────────────────────────────────┤
│  1. Request masuk dengan user_id                           │
│  2. Query database:                                        │
│     - developer_journey_trackings → avg_study_hour         │
│     - exam_results → avg_exam_score                        │
│     - developer_journey_submissions → submission_fail_rate │
│     - developer_journey_completions → completion_speed     │
│  3. Hitung fitur menggunakan SQL/PHP                       │
│  4. Kirim ke ML API                                        │
└────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌────────────────────────────────────────────────────────────┐
│                       ML API                               │
│  Terima fitur yang sudah dihitung → Return prediction      │
└────────────────────────────────────────────────────────────┘
```

### Quick SQL Reference:

| Feature | Query |
|---------|-------|
| `avg_study_hour` | `AVG(HOUR(first_opened_at))` dari `developer_journey_trackings` |
| `avg_exam_score` | `AVG(score)` dari `exam_results` JOIN `exam_registrations` |
| `submission_fail_rate` | `COUNT(failed) / COUNT(*)` dari `developer_journey_submissions` |
| `completion_speed` | `study_duration / hours_to_study` dari `developer_journey_completions` JOIN `developer_journeys` |
| `retry_count` | `SUM(enrolling_times - 1)` dari `developer_journey_completions` |

### Default Values (jika data tidak tersedia):

```json
{
  "avg_study_hour": 12.0,
  "study_consistency_std": 100.0,
  "completion_speed": 1.0,
  "avg_exam_score": 75.0,
  "submission_fail_rate": 0.1,
  "retry_count": 0
}
```

---

## 🔑 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| GEMINI_API_KEY | API key untuk Gemini AI | Yes (for advice) |

---

## 📊 Model Info

### Model 1: Persona Classification
- **Algorithm:** Random Forest Classifier
- **Classes:** 5 (The Consistent, The Deep Diver, The Night Owl, The Sprinter, The Struggler)
- **Features:** 6 (avg_study_hour, study_consistency_std, completion_speed, avg_exam_score, submission_fail_rate, retry_count)
- **File:** `models/persona_classifier.pkl`

### Model 3: Pace Classification
- **Algorithm:** Random Forest Classifier
- **Classes:** 3 (Consistent Learner, Fast Learner, Reflective Learner)
- **Features:** 5 (completion_speed, study_consistency_std, avg_study_hour, completed_modules, total_modules_viewed)
- **File:** `models/pace_classifier.pkl`

---

## 📝 Changelog

### v1.2.0 (2025-12-08)
- Updated Model 1 & 3 from Clustering to Classification
- Fixed class mapping to match LabelEncoder order
- Added confidence scores

### v1.1.0 (2025-12-05)
- Fixed pace analysis null values
- Added support for features in request body

---

**For more details, see:** `BACKEND_FEATURE_CALCULATION_GUIDE.md` and `BACKEND_INTEGRATION_NODEJS.md`