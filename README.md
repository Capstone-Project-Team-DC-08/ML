# 🎓 AI Learning Insight - Machine Learning Models

**Capstone Project - Machine Learning untuk Analisis Pola Belajar Siswa**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![API Version](https://img.shields.io/badge/API-v1.2.0-brightgreen.svg)](#)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 Daftar Isi

1. [Tentang Project](#tentang-project)
2. [Fitur Utama](#fitur-utama)
3. [Database Sources & Features](#database-sources--features)
4. [Arsitektur System](#arsitektur-system)
5. [Struktur Folder](#struktur-folder)
6. [Quick Start](#quick-start)
7. [Cara Menggunakan API](#cara-menggunakan-api)
8. [Backend Integration](#backend-integration)
9. [Untuk Tim Frontend](#untuk-tim-frontend)
10. [FAQ](#faq)

---

## 🎯 Tentang Project

Project ini adalah sistem Machine Learning untuk **menganalisis pola belajar siswa** di platform pembelajaran online Dicoding. Sistem ini menggunakan **3 model ML** yang bekerja sama untuk memberikan insight personal kepada setiap siswa.

### Problem yang Diselesaikan:

1. **Siswa tidak tahu tipe belajar mereka** → Model 1 mengklasifikasikan ke 5 persona
2. **Siswa butuh motivasi & saran** → Model 2 generate saran personal dengan AI
3. **Siswa tidak tahu progress mereka** → Model 3 analisis kecepatan belajar

### Output untuk Website:

- **Dashboard Siswa:** Label persona + saran belajar AI
- **Card Course:** Badge kecepatan belajar
- **Insight Panel:** Perbandingan dengan siswa lain

---

## ✨ Fitur Utama

### 🎭 Model 1: Persona Classification
**"Kamu Tipe Pembelajar Apa?"**

Mengklasifikasikan siswa ke **5 tipe persona** berdasarkan aktivitas belajar menggunakan **Random Forest Classifier**:

| Class | Persona | Deskripsi | Kriteria |
|-------|---------|-----------|----------|
| 0 | 📊 **The Consistent** | Steady Learner | `study_consistency_std` rendah |
| 1 | 🔍 **The Deep Diver** | Slow but Thorough | `completion_speed` tinggi + `avg_exam_score` tinggi |
| 2 | 🦉 **The Night Owl** | Night-time Learner | `avg_study_hour >= 19 OR < 6` |
| 3 | 🚀 **The Sprinter** | Fast Learner | `completion_speed` rendah + `avg_exam_score` tinggi |
| 4 | 💪 **The Struggler** | Need Support | `avg_exam_score` rendah + `submission_fail_rate` tinggi |

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

### 📊 Model 3: Learning Pace Classification
**"Seberapa Cepat Kamu Dibanding Siswa Lain?"**

Mengklasifikasikan **3 tipe pace belajar** menggunakan **Random Forest Classifier**:

| Class | Label | Deskripsi | Kriteria |
|-------|-------|-----------|----------|
| 0 | 📊 **Consistent Learner** | Belajar teratur dan stabil | `weekly_cv` rendah |
| 1 | 🚀 **Fast Learner** | Belajar cepat dan efisien | `completion_speed < 0.55` |
| 2 | 📚 **Reflective Learner** | Belajar mendalam dan reflektif | `completion_speed > 1.5` |

**Output:**
- **Label:** Fast Learner / Consistent Learner / Reflective Learner
- **Confidence:** Tingkat kepercayaan prediksi
- **Insight:** "Kamu belajar dengan cepat dan efisien! 🚀"

**Use Case:** Badge di setiap card course

---

## 📊 Database Sources & Features

### Tabel Database yang Digunakan

| Tabel | Deskripsi | Kolom Utama |
|-------|-----------|-------------|
| `users` | Data pengguna | `id`, `name`, `email` |
| `developer_journey_trackings` | Tracking aktivitas belajar | `developer_id`, `journey_id`, `tutorial_id`, `first_opened_at`, `completed_at`, `last_viewed` |
| `developer_journey_submissions` | Data pengumpulan tugas | `submitter_id`, `journey_id`, `status`, `rating`, `created_at` |
| `exam_results` | Hasil ujian | `exam_registration_id`, `score`, `is_passed` |
| `exam_registrations` | Registrasi ujian | `id`, `examinees_id`, `tutorial_id` |
| `developer_journey_completions` | Penyelesaian learning path | `user_id`, `journey_id`, `study_duration`, `enrolling_times` |
| `developer_journeys` | Informasi learning path | `id`, `name`, `difficulty`, `hours_to_study` |
| `tutorials` | Materi pembelajaran | `id`, `developer_journey_id`, `name` |

---

### 🎭 Model 1: Persona Classification - Data Sources

**Fitur yang Dibutuhkan:**

| Feature | Sumber Tabel | Kolom yang Digunakan | Perhitungan |
|---------|--------------|----------------------|-------------|
| `avg_study_hour` | `developer_journey_trackings` | `first_opened_at` | `AVG(HOUR(first_opened_at))` |
| `study_consistency_std` | `developer_journey_trackings` | `first_opened_at` | Standard deviasi dari aktivitas harian |
| `completion_speed` | `developer_journey_completions` + `developer_journeys` | `study_duration`, `hours_to_study` | `study_duration / hours_to_study` |
| `avg_exam_score` | `exam_results` + `exam_registrations` | `score`, `examinees_id` | `AVG(score)` |
| `submission_fail_rate` | `developer_journey_submissions` | `status`, `submitter_id` | `COUNT(failed) / COUNT(*)` |
| `retry_count` | `developer_journey_completions` | `enrolling_times` | `SUM(enrolling_times - 1)` |

---

### 💬 Model 2: Advice Generation - Data Sources

**Fitur yang Dibutuhkan:**

| Feature | Sumber | Deskripsi |
|---------|--------|-----------|
| `name` | `users.name` | Nama siswa untuk personalisasi |
| `persona_label` | Output Model 1 | Tipe persona dari prediksi |
| `pace_label` | Output Model 3 | Kecepatan belajar dari prediksi |
| `avg_exam_score` | Sama seperti Model 1 | Rata-rata nilai ujian |
| `course_name` | `developer_journeys.name` | Nama learning path |

---

### 📊 Model 3: Pace Classification - Data Sources

**Fitur yang Dibutuhkan:**

| Feature | Sumber Tabel | Kolom yang Digunakan | Perhitungan |
|---------|--------------|----------------------|-------------|
| `completion_speed` | `developer_journey_completions` + `developer_journeys` | `study_duration`, `hours_to_study` | `study_duration / hours_to_study` |
| `study_consistency_std` | `developer_journey_trackings` | `first_opened_at` | Standard deviasi dari aktivitas harian |
| `avg_study_hour` | `developer_journey_trackings` | `first_opened_at` | `AVG(HOUR(first_opened_at))` |
| `completed_modules` | `developer_journey_trackings` | `completed_at` | `COUNT(*)` where completed |
| `total_modules_viewed` | `developer_journey_trackings` | `first_opened_at` | `COUNT(*)` where viewed |

📄 **Detail lengkap:** Lihat `BACKEND_FEATURE_CALCULATION_GUIDE.md`

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
│   └── processed/              # Features + classification results
│       ├── clustering_results.csv    # Output Model 1
│       └── pace_analysis_results.csv # Output Model 3
│
├── 📁 models/                  # Model ML yang sudah dilatih
│   ├── persona_classifier.pkl        # Model 1 (Classification - PRIMARY)
│   ├── clustering_model_production.pkl  # Model 1 (Clustering - FALLBACK)
│   ├── pace_classifier.pkl           # Model 3 (Classification - PRIMARY)
│   └── pace_model.pkl                # Model 3 (Clustering - FALLBACK)
│
├── 📁 notebooks/               # Jupyter notebooks untuk training
│   ├── 01_clean_individual_files.ipynb
│   ├── 02_feature_engineering.ipynb
│   ├── 03_model1_clustering_ADVANCED.ipynb  
│   ├── 04_model2_advice_generation.ipynb        # ⭐ Model 2
│   ├── 05_model3_pace_analysis.ipynb        
│   ├── 06_model1_persona_classification.ipynb   # ⭐ Model 1
│   └── 07_model3_pace_classification.ipynb      # ⭐ Model 3
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
├── 📄 BACKEND_INTEGRATION_NODEJS.md         # ⭐ Contoh integrasi Node.js
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
| **BACKEND_INTEGRATION_NODEJS.md** | Backend (Node.js) | ⭐ Contoh lengkap integrasi Express.js |

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
[OK] Classification model loaded from models/persona_classifier.pkl
[OK] Pace classification model loaded from models/pace_classifier.pkl
[OK] Gemini AI configured
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
  "cluster_id": 2,
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

| Model | Metrik | Score | Tipe |
|-------|--------|-------|------|
| Model 1 (Persona) | Accuracy | ~85% | Classification (Random Forest) |
| Model 3 (Pace) | Accuracy | ~90% | Classification (Random Forest) |
| API Response Time (Model 1 & 3) | Latency | ~50-100ms | - |
| API Response Time (Model 2 with Gemini) | Latency | ~1-3 detik | - |

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

### Q: Apa bedanya Classification dan Clustering?
**A:** 
- **Clustering (lama):** Model unsupervised, mengelompokkan berdasarkan kemiripan
- **Classification (baru):** Model supervised, memprediksi label berdasarkan training data yang sudah berlabel

---

## 📝 Changelog

### v1.2.0 (2025-12-08)
- ✅ **UPDATED: Model 1 & 3 dari Clustering → Classification**
- ✅ Fixed: Mapping class persona sesuai LabelEncoder (0=Consistent, 1=Deep Diver, 2=Night Owl, 3=Sprinter, 4=Struggler)
- ✅ Fixed: Mapping class pace sesuai LabelEncoder (0=Consistent, 1=Fast, 2=Reflective)
- ✅ Added: Confidence score dari model Classification
- ✅ Added: Database Sources & Features section
- ✅ Updated: Dokumentasi lengkap

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
- **Node.js Integration:** `BACKEND_INTEGRATION_NODEJS.md`
- **Test Script:** `python src/test_api.py`

---

**Butuh bantuan?** Baca dokumentasi atau hubungi tim ML!

**Happy Coding! 🚀**