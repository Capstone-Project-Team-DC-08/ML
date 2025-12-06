# AI Learning Insight API - Documentation

## 📋 Overview

API ini menyediakan layanan Machine Learning untuk platform pembelajaran dengan 3 model utama:

1. **Model 1: Persona Clustering** - Mengidentifikasi tipe pembelajar
2. **Model 2: Advice Generation** - Menghasilkan saran personal dengan AI
3. **Model 3: Pace Analysis** - Menganalisis kecepatan belajar

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

### Model 1: Persona Prediction

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
```

**5 Persona yang tersedia:**

| Cluster | Persona | Kriteria |
|---------|---------|----------|
| 0 | The Sprinter | completion_speed < 0.5 + avg_exam_score >= 75 |
| 1 | The Deep Diver | completion_speed > 2.0 + avg_exam_score >= 70 |
| 2 | The Struggler | avg_exam_score < 60 + submission_fail_rate > 0.3 |
| 3 | The Consistent | study_consistency_std < 100 |
| 4 | The Night Owl | avg_study_hour >= 19 |

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

### Model 3: Pace Analysis

**POST** `/api/v1/pace/analyze`

**Request:**
```json
{
  "user_id": 123,
  "journey_id": 45,
  "features": {
    "materials_per_day": 6.5,
    "weekly_cv": 0.3,
    "completion_speed": 0.8
  }
}
```

**Response:**
```json
{
  "user_id": 123,
  "pace_label": "fast learner",
  "cluster_id": 0,
  "scores": {
    "fast_score": 1,
    "consistent_score": 1,
    "reflective_score": 0
  },
  "insight": "Kamu belajar dengan cepat dan efisien! 🚀"
}
```

**3 Pace Categories:**

| Label | Kriteria |
|-------|----------|
| Fast Learner | materials_per_day >= 5 + weekly_cv <= median |
| Consistent Learner | weekly_cv <= median |
| Reflective Learner | completion_speed > 1.5 |

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