# 🎓 AI Learning Insight - Machine Learning Models

**Capstone Project - Machine Learning untuk Analisis Pola Belajar Siswa**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![API Version](https://img.shields.io/badge/API-v1.1.0-brightgreen.svg)](#)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 Daftar Isi

1. [Tentang Project](#tentang-project)
2. [Fitur Utama](#fitur-utama)
3. [Arsitektur System](#arsitektur-system)
4. [Struktur Folder](#struktur-folder)
5. [Quick Start](#quick-start)
6. [Cara Menggunakan API](#cara-menggunakan-api)
7. [Backend Integration](#backend-integration)
8. [Untuk Tim Frontend](#untuk-tim-frontend)
9. [FAQ](#faq)

---

## 🎯 Tentang Project

Project ini adalah sistem Machine Learning untuk **menganalisis pola belajar siswa** di platform pembelajaran online Dicoding. Sistem ini menggunakan **3 model ML** yang bekerja sama untuk memberikan insight personal kepada setiap siswa.

### Problem yang Diselesaikan:

1. **Siswa tidak tahu tipe belajar mereka** → Model 1 mengelompokkan ke 5 persona
2. **Siswa butuh motivasi & saran** → Model 2 generate saran personal dengan AI
3. **Siswa tidak tahu progress mereka** → Model 3 analisis kecepatan belajar

### Output untuk Website:

- **Dashboard Siswa:** Label persona + saran belajar AI
- **Card Course:** Badge kecepatan belajar
- **Insight Panel:** Perbandingan dengan siswa lain

---

## ✨ Fitur Utama

### 🎭 Model 1: Persona Clustering
**"Kamu Tipe Pembelajar Apa?"**

Mengelompokkan siswa ke **5 tipe persona** berdasarkan aktivitas belajar:

| Cluster | Persona | Deskripsi | Kriteria |
|---------|---------|-----------|----------|
| 0 | 🚀 **The Sprinter** | Fast Learner | `completion_speed < 0.5` + `avg_exam_score >= 75` |
| 1 | 🔍 **The Deep Diver** | Slow but Thorough | `completion_speed > 2.0` + `avg_exam_score >= 70` |
| 2 | 💪 **The Struggler** | Need Support | `avg_exam_score < 60` + `submission_fail_rate > 0.3` |
| 3 | 📊 **The Consistent** | Steady Learner | `study_consistency_std < 100` |
| 4 | 🦉 **The Night Owl** | Night-time Learner | `avg_study_hour >= 19` |

**Use Case:** Label di dashboard user - "Kamu adalah The Night Owl!"

---

### 💬 Model 2: Personalized Advice
**"Saran Personal Pakai AI"**

Generate saran belajar menggunakan **Google Gemini AI** yang:
- ✅ Personal (menyapa dengan nama)
- ✅ Empatik (memahami kondisi siswa berdasarkan persona)
- ✅ Context-aware (mempertimbangkan pace belajar)
- ✅ Actionable (saran yang bisa diterapkan)
- ✅ Motivasional (mendorong semangat)

**Contoh Output:**
> "Halo Budi Santoso! Sebagai Night Owl yang belajar dengan pace cepat, kamu punya potensi luar biasa! Kami sarankan untuk tetap jaga kesehatan dengan istirahat cukup dan gunakan teknik pomodoro untuk fokus optimal di malam hari. Terus eksplorasi topik-topik advanced!"

**Use Case:** Insight panel di dashboard siswa

---

### 📊 Model 3: Learning Pace Analysis
**"Seberapa Cepat Kamu Dibanding Siswa Lain?"**

Kategorisasi **3 tipe pace belajar**:

| Label | Deskripsi | Kriteria |
|-------|-----------|----------|
| 🚀 **Fast Learner** | Belajar cepat dan efisien | `materials_per_day >= 5` + `weekly_cv <= median` |
| 📊 **Consistent Learner** | Belajar teratur dan stabil | `weekly_cv <= median` |
| 📚 **Reflective Learner** | Belajar mendalam dan reflektif | `completion_speed > 1.5` |

**Output:**
- **Label:** Fast Learner / Consistent Learner / Reflective Learner
- **Scores:** fast_score, consistent_score, reflective_score (binary)
- **Insight:** "Kamu belajar dengan cepat dan efisien! 🚀"

**Use Case:** Badge di setiap card course

---

## 🏗️ Arsitektur System

### Flow Keseluruhan:

```
┌─────────────┐
│   Website   │ (Tim Frontend)
│  (Frontend) │
└──────┬──────┘
       │
       ▼
┌─────────────┐      ┌──────────────┐
│   Backend   │────▶│   Database   │
│   Server    │◀────│   (MySQL)    │
└──────┬──────┘      └──────────────┘
       │  
       │ 1. Query data mentah
       │ 2. HITUNG fitur (avg_study_hour, dll)
       │ 3. HTTP Request ke ML API
       ▼
┌─────────────┐      ┌──────────────┐
│   ML API    │────▶│  ML Models   │
│  (FastAPI)  │◀────│  (.pkl files)│
└─────────────┘      └──────────────┘
```

### ⚠️ PENTING:
- ML API **TIDAK** connect ke database langsung
- **Backend** yang query database dan **menghitung fitur**
- ML API hanya terima fitur yang sudah dihitung → return prediksi

---

## 📁 Struktur Folder

```
ML/
├── 📁 data/                    # Dataset
│   ├── raw/                    # Data asli dari database (Excel)
│   ├── interim/                # Data yang sudah dibersihkan
│   └── processed/              # Features + clustering results
│       ├── clustering_results.csv    # Output Model 1
│       └── pace_analysis_results.csv # Output Model 3
│
├── 📁 models/                  # Model ML yang sudah dilatih
│   ├── clustering_model_production.pkl  # Model 1 (Persona)
│   └── pace_model.pkl                   # Model 3 (Pace)
│
├── 📁 notebooks/               # Jupyter notebooks untuk training
│   ├── 01_clean_individual_files.ipynb
│   ├── 02_feature_engineering.ipynb
│   ├── 03_model1_clustering_ADVANCED.ipynb  # ⭐ Model 1
│   ├── 04_model2_advice_generation.ipynb    # ⭐ Model 2
│   └── 05_model3_pace_analysis.ipynb        # ⭐ Model 3
│
├── 📁 src/                     # Source code
│   ├── 📁 api/                 # ⭐ API FILES
│   │   ├── main.py            # FastAPI server
│   │   ├── schemas.py         # Request/Response models
│   │   └── services.py        # ML model logic
│   │
│   ├── test_api.py            # API testing script
│   └── backend_integration_example.py
│
├── 📄 API_DOCUMENTATION.md               # ⭐ Dokumentasi API lengkap
├── 📄 BACKEND_FEATURE_CALCULATION_GUIDE.md  # ⭐ Cara hitung fitur dari DB
├── .env.example               # Template environment variables
├── requirements.txt           # Python dependencies
└── README.md                  # File ini!
```

### 📚 File Dokumentasi Penting:

| File | Untuk Siapa | Isi |
|------|-------------|-----|
| **README.md** | Semua orang | Overview project (file ini) |
| **API_DOCUMENTATION.md** | Backend + Frontend | Dokumentasi API lengkap |
| **BACKEND_FEATURE_CALCULATION_GUIDE.md** | Backend | ⭐ Cara hitung fitur dari database! |

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Aktifkan virtual environment
# Windows
.venv\Scripts\activate

# Linux/Mac
source .venv/bin/activate

# Install packages
pip install -r requirements.txt
```

### 2. Setup Environment (Optional)

```bash
# Copy template
copy .env.example .env

# Edit .env dan tambahkan:
# GEMINI_API_KEY=your_key_here
```

Dapatkan API key dari: https://makersuite.google.com/app/apikey

**Catatan:** Tanpa API key, Model 2 akan pakai template sederhana (tetap jalan).

### 3. Jalankan API Server

```bash
cd src/api
python main.py
```

Output jika berhasil:
```
============================================================
🚀 Starting AI Learning Insight API v1.1.0...
============================================================
✓ Clustering model loaded
✓ Pace model loaded  
✓ Gemini AI configured
✅ All models loaded successfully!
📝 API Documentation: http://localhost:8000/docs
============================================================
```

### 4. Test API

```bash
# Di terminal baru
python src/test_api.py
```

Output:
```
✓ All tests passed! (9/9)
```

---

## 📖 Cara Menggunakan API

### API Endpoints:

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| POST | `/api/v1/persona/predict` | **Model 1:** Prediksi persona |
| POST | `/api/v1/advice/generate` | **Model 2:** Generate saran AI |
| POST | `/api/v1/pace/analyze` | **Model 3:** Analisis pace |
| GET | `/api/v1/insights/{user_id}` | **Combined:** Semua model sekaligus |

### Example: Persona Prediction

**Request:**
```bash
POST /api/v1/persona/predict
Content-Type: application/json

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
  "characteristics": [
    "Mayoritas aktivitas belajar di jam 19:00 - 24:00",
    "Konsistensi belajar cukup baik",
    "Produktif di waktu malam"
  ]
}
```

**📄 Dokumentasi lengkap:** Baca file **`API_DOCUMENTATION.md`**!

---

## 🔧 Backend Integration

### ⚠️ PENTING: Fitur Harus DIHITUNG dari Database!

Fitur seperti `avg_study_hour`, `completion_speed`, dll. **TIDAK ADA** di tabel database secara langsung. Tim backend harus **MENGHITUNG** fitur-fitur ini dari data mentah.

### 📄 Panduan Lengkap:
Baca **`BACKEND_FEATURE_CALCULATION_GUIDE.md`** untuk:
- SQL queries untuk setiap fitur
- Contoh code PHP/Laravel/Node.js
- Mapping tabel database ke fitur

### Quick Reference:

| Fitur | Sumber Tabel | Perhitungan |
|-------|--------------|-------------|
| `avg_study_hour` | `developer_journey_trackings` | `AVG(HOUR(first_opened_at))` |
| `avg_exam_score` | `exam_results` + `exam_registrations` | `AVG(score)` |
| `submission_fail_rate` | `developer_journey_submissions` | `COUNT(failed) / COUNT(*)` |
| `completion_speed` | `developer_journey_completions` + `developer_journeys` | `study_duration / hours_to_study` |
| `retry_count` | `developer_journey_completions` | `SUM(enrolling_times - 1)` |

### Flow Backend:

```
┌────────────────────────────────────────────────────────────┐
│                     YOUR BACKEND                           │
├────────────────────────────────────────────────────────────┤
│  1. Request masuk dengan user_id                           │
│  2. Query database, hitung fitur                           │
│  3. Kirim ke ML API dengan fitur yang sudah dihitung       │
│  4. Return hasil ke frontend                               │
└────────────────────────────────────────────────────────────┘
```

### Contoh Code (PHP/Laravel):

```php
public function getPrediction(int $userId) 
{
    // 1. Hitung fitur dari database
    $avgStudyHour = DB::table('developer_journey_trackings')
        ->where('developer_id', $userId)
        ->selectRaw('AVG(HOUR(first_opened_at)) as avg')
        ->value('avg') ?? 12.0;
    
    // 2. Kirim ke ML API
    $response = Http::post('http://ml-api:8000/api/v1/persona/predict', [
        'user_id' => $userId,
        'features' => [
            'avg_study_hour' => $avgStudyHour,
            // ... fitur lainnya
        ]
    ]);
    
    return $response->json();
}
```

---

## 🎨 Untuk Tim Frontend

### Flow:

```
Frontend → Backend → ML API → Response → Backend → Frontend
```

**Frontend TIDAK panggil ML API langsung!** Panggil endpoint yang dibuat tim backend.

### Response Format untuk UI:

**Persona Card:**
```jsx
<div className="persona-card">
  <h2>{persona.persona_label}</h2>  {/* "The Night Owl" */}
  <p>Confidence: {(persona.confidence * 100).toFixed(0)}%</p>
  <ul>
    {persona.characteristics.map(char => 
      <li key={char}>{char}</li>
    )}
  </ul>
</div>
```

**Pace Badge:**
```jsx
<span className={`badge badge-${pace.pace_label.replace(' ', '-')}`}>
  {pace.pace_label} {/* "Fast Learner" */}
</span>
<p>{pace.insight}</p> {/* "Kamu belajar dengan cepat! 🚀" */}
```

---

## 📊 Model Performance

| Model | Metrik | Score |
|-------|--------|-------|
| Model 1 (Clustering) | Silhouette Score | 0.78 |
| Model 3 (Pace) | Silhouette Score | 0.65+ |
| API Response Time (Model 1 & 3) | Latency | ~50-100ms |
| API Response Time (Model 2 with Gemini) | Latency | ~1-3 detik |

---

## ❓ FAQ

### Q: Apakah API harus connect ke database?
**A:** TIDAK! Backend yang query database dan hitung fitur. API hanya terima request dengan fitur yang sudah dihitung.

### Q: Bagaimana cara dapat API key Gemini?
**A:** 
1. Buka https://makersuite.google.com/app/apikey
2. Login dengan Google
3. Create API key
4. Copy ke file `.env`

### Q: Response ada nilai null?
**A:** Pastikan mengirim semua fitur yang diperlukan di request. Lihat dokumentasi API untuk format lengkap.

### Q: Bisa pakai bahasa selain Python untuk backend?
**A:** Ya! Backend bisa pakai language apa saja (Node.js, PHP, Go, dll). Yang penting bisa HTTP request ke ML API.

### Q: Port 8000 sudah dipakai?
**A:** Edit di `main.py` → `uvicorn.run(..., port=8001)`, lalu restart.

---

## 📝 Changelog

### v1.1.0 (2025-12-05)
- ✅ Fixed: Pace analysis response null values
- ✅ Updated: 5 persona dengan kriteria yang jelas
- ✅ Updated: 3 pace categories (fast/consistent/reflective)
- ✅ Added: Support untuk fitur langsung di request
- ✅ Added: `BACKEND_FEATURE_CALCULATION_GUIDE.md`
- ✅ Improved: Advice generation dengan persona + pace context

### v1.0.0 (2025-12-02)
- Initial release

---

## 🎉 Quick Links

- **API Documentation:** http://localhost:8000/docs
- **API Guide:** `API_DOCUMENTATION.md`
- **Backend Feature Guide:** `BACKEND_FEATURE_CALCULATION_GUIDE.md`
- **Test Script:** `python src/test_api.py`

---

**Butuh bantuan?** Baca dokumentasi atau hubungi tim ML!

**Happy Coding! 🚀**