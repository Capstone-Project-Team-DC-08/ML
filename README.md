# 🎓 AI Learning Insight - Machine Learning Models

**Capstone Project - Machine Learning untuk Analisis Pola Belajar Siswa**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📋 Daftar Isi

1. [Tentang Project](#tentang-project)
2. [Fitur Utama](#fitur-utama)
3. [Arsitektur System](#arsitektur-system)
4. [Struktur Folder](#struktur-folder)
5. [Cara Install](#cara-install)
6. [Cara Menggunakan API](#cara-menggunakan-api)
7. [Untuk Tim Backend](#untuk-tim-backend)
8. [Untuk Tim Frontend](#untuk-tim-frontend)
9. [FAQ](#faq)

---

## 🎯 Tentang Project

Project ini adalah sistem Machine Learning untuk **menganalisis pola belajar siswa** di platform pembelajaran online. Sistem ini menggunakan **3 model ML** yang bekerja sama untuk memberikan insight personal kepada setiap siswa.

### Problem yang Diselesaikan:

1. **Siswa tidak tahu tipe belajar mereka** → Model mengelompokkan ke persona
2. **Siswa butuh motivasi & saran** → AI generate saran personal
3. **Siswa tidak tahu progress mereka** → Analisis kecepatan belajar

### Output untuk Website:

- **Dashboard Siswa:** Label persona + saran belajar AI
- **Card Course:** Badge kecepatan belajar
- **Insight Panel:** Perbandingan dengan siswa lain

---

## ✨ Fitur Utama

### 🎭 Model 1: Persona Clustering
**"Kamu Tipe Pembelajar Apa?"**

Mengelompokkan siswa ke 5 tipe persona berdasarkan aktivitas belajar:

| Persona | Deskripsi | Karakteristik |
|---------|-----------|---------------|
| 🚀 **The Sprinter** | Fast Learner | Cepat selesai, nilai tinggi |
| 🔍 **The Deep Diver** | Slow but Thorough | Lambat tapi memahami dengan baik |
| 🦉 **The Night Owl** | Night-time Learner | Aktif belajar malam hari |
| 💪 **The Struggler** | Need Support | Butuh bantuan ekstra |
| 📊 **The Consistent** | Steady Learner | Belajar rutin dan teratur |

**Use Case:** Label di dashboard user - "Kamu adalah The Night Owl!"

---

### 💬 Model 2: Personalized Advice
**"Saran Personal Pakai AI"**

Generate saran belajar menggunakan **Google Gemini AI** yang:
- ✅ Personal (menyapa dengan nama)
- ✅ Empatik (memahami kondisi siswa)
- ✅ Actionable (saran yang bisa diterapkan)
- ✅ Motivasional (mendorong semangat)

**Contoh Output:**
> "Halo Budi! Kamu tipe Night Owl yang suka belajar malam. Kamu 20% lebih cepat dari rata-rata, hebat! Tapi nilai ujianmu bisa lebih baik. Coba review materi sebelum ujian ya. Semangat! 🚀"

**Use Case:** Insight panel di dashboard siswa

---

### 📊 Model 3: Learning Pace Analysis
**"Seberapa Cepat Kamu Dibanding Siswa Lain?"**

Analisis kecepatan belajar dengan output:
- **Label:** Fast Learner / Average / Slow but Thorough
- **Persentase:** "+25% lebih cepat dari rata-rata"
- **Ranking:** "Top 15% siswa tercepat"

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
┌─────────────┐     ┌──────────────┐
│   Backend   │────▶│   Database   │
│   Server    │◀────│   (MySQL)    │
└──────┬──────┘     └──────────────┘
       │
       │ HTTP Request
       ▼
┌─────────────┐     ┌──────────────┐
│   ML API    │────▶│  ML Models   │
│  (FastAPI)  │◀────│  (.pkl files)│
└─────────────┘     └──────────────┘
```

### Penjelasan:

1. **Frontend** → Tampilkan UI ke user
2. **Backend** → Query database, hitung fitur, panggil ML API
3. **ML API** → Terima request, prediksi pakai model, return hasil
4. **Database** → Simpan semua data siswa & course

**⚠️ PENTING:** ML API **TIDAK** connect ke database langsung!

---

## 📁 Struktur Folder

```
ML/
├── 📁 data/                    # Dataset
│   ├── raw/                    # Data asli dari database (Excel)
│   ├── interim/                # Data yang sudah dibersihkan
│   └── processed/              # Features siap untuk model
│
├── 📁 models/                  # Model ML yang sudah dilatih
│   ├── clustering_model_production.pkl
│   └── pace_model_production.pkl
│
├── 📁 notebooks/               # Jupyter notebooks untuk training
│   ├── 01_clean_individual_files.ipynb
│   ├── 02_feature_engineering.ipynb
│   ├── 03_model1_clustering_ADVANCED.ipynb
│   ├── 04_model2_advice_generation.ipynb
│   └── 05_model3_pace_analysis.ipynb
│
├── 📁 src/                     # Source code
│   ├── api/                    # ⭐ API FILES (yang penting!)
│   │   ├── main.py            # FastAPI server
│   │   ├── schemas.py         # Request/Response models
│   │   └── services.py        # ML model logic
│   │
│   └── PANDUAN_API.md         # ⭐ BACA INI untuk cara pakai API!
│
├── .env.example               # Template environment variables
├── requirements.txt           # Python dependencies
└── README.md                  # ⭐ File ini!
```

### File Penting yang Harus Dibaca:

| File | Untuk Siapa | Isi |
|------|-------------|-----|
| **README.md** | Semua orang | Overview project (file ini) |
| **PANDUAN_API.md** | Backend + Frontend | Cara pakai API (simple!) |
| **src/api/main.py** | Developer | Source code API |

---

## 🚀 Cara Install

### Prasyarat:
- Python 3.8 atau lebih tinggi
- Virtual environment sudah dibuat (folder `venv` atau `.venv`)

### Step-by-Step:

#### 1. Aktifkan Virtual Environment

```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

Pastikan ada `(venv)` di terminal Anda.

#### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

Library yang diinstall:
- `fastapi` - Web framework
- `uvicorn` - Server
- `pydantic` - Validasi data
- `scikit-learn` - ML library
- `joblib` - Load model
- `google-generativeai` - Gemini AI (optional)

#### 3. Setup API Key (Opsional)

Jika ingin pakai Gemini AI untuk Model 2:

```bash
# Copy template
copy .env.example .env

# Edit .env
# Tambahkan: GEMINI_API_KEY=your_key_here
```

Dapatkan API key dari: https://makersuite.google.com/app/apikey

**Catatan:** Tanpa API key, Model 2 akan pakai template sederhana (tetap jalan).

#### 4. Jalankan API Server

```bash
cd src/api
python main.py
```

Jika berhasil, akan muncul:
```
✓ Clustering model loaded
✓ Pace model loaded  
✓ Gemini AI configured
📝 API Documentation: http://localhost:8000/docs
```

#### 5. Test API

Buka browser: **http://localhost:8000/docs**

Anda akan lihat interface Swagger UI untuk testing.

---

## 📖 Cara Menggunakan API

### Quick Start - 3 Menit!

**Dokumentasi lengkap:** Baca file **`PANDUAN_API.md`** untuk tutorial step-by-step!

### Endpoint Utama:

1. **Health Check** - Cek status API
   ```
   GET http://localhost:8000/health
   ```

2. **Get Persona** - Dapatkan tipe pembelajar
   ```
   POST http://localhost:8000/api/v1/persona/predict
   Body: {"user_id": 123}
   ```

3. **Generate Advice** - Saran belajar AI
   ```
   POST http://localhost:8000/api/v1/advice/generate
   Body: {"user_id": 123, "name": "Budi"}
   ```

4. **Analyze Pace** - Kecepatan belajar
   ```
   POST http://localhost:8000/api/v1/pace/analyze
   Body: {"user_id": 123, "journey_id": 45}
   ```

5. **Complete Insights** - Semua sekaligus! ⭐
   ```
   GET http://localhost:8000/api/v1/insights/123?user_name=Budi
   ```

**Detail lengkap + contoh code:** Lihat **PANDUAN_API.md**!

---

## 🔧 Untuk Tim Backend

### Yang Harus Dilakukan:

1. **Baca** file `PANDUAN_API.md` section "Untuk Backend"
2. **Query** data dari database
3. **Hitung** 6 fitur untuk Model 1:
   - avg_study_hour
   - study_consistency_std
   - completion_speed
   - avg_exam_score
   - submission_fail_rate
   - retry_count

4. **Panggil** ML API dengan HTTP request
5. **Return** hasil ke frontend

### ⚠️ PENTING: Nama Kolom Database

Database pakai nama kolom yang **BEDA** untuk user ID di setiap tabel:

| Tabel | Kolom untuk User ID |
|-------|---------------------|
| `developer_journey_trackings` | `developer_id` ⚠️ |
| `developer_journey_submissions` | `submitter_id` ⚠️ |
| `developer_journey_completions` | `user_id` ✅ |
| `exam_registrations` | `examinees_id` ⚠️ |

**Solusi:** Lihat contoh SQL yang benar di **PANDUAN_API.md** section "Query Database"!

### Contoh Code:

```python
import requests

# Call ML API
response = requests.post(
    'http://localhost:8000/api/v1/persona/predict',
    json={'user_id': 123}
)

persona = response.json()
print(persona['persona_label'])  # "The Night Owl"
```

**Full example:** Lihat file `src/backend_integration_example.py`

---

## 🎨 Untuk Tim Frontend

### Yang Perlu Diketahui:

1. **Frontend TIDAK panggil ML API langsung**
2. Frontend panggil **backend endpoint** yang dibuat tim backend
3. Backend yang akan panggil ML API

### Flow:

```
Frontend → Backend → ML API → Response → Backend → Frontend
```

### Response Format:

Lihat **PANDUAN_API.md** section "Response Examples" untuk:
- JSON structure lengkap
- UI/UX suggestions
- Component examples (React/Vue)
- CSS styling ideas

### Contoh Display:

```jsx
// Dashboard User
<div className="persona-card">
  <h2>{persona.label}</h2>  {/* "The Night Owl" */}
  <p>Confidence: {persona.confidence * 100}%</p>
  <ul>
    {persona.characteristics.map(char => 
      <li>{char}</li>
    )}
  </ul>
</div>
```

**Full examples:** File `PANDUAN_API.md` punya semua contoh UI!

---

## 🔬 Development & Training

### Re-train Model (Jika Ada Data Baru):

1. Export data baru dari database ke Excel
2. Taruh di folder `data/raw/`
3. Buka Jupyter notebooks di folder `notebooks/`:
   ```bash
   jupyter notebook
   ```
4. Jalankan notebook berurutan (01 → 05)
5. Model baru akan tersimpan di folder `models/`
6. Restart API server

### Notebooks:

| Notebook | Fungsi |
|----------|--------|
| `01_clean_individual_files.ipynb` | Bersihkan data |
| `02_feature_engineering.ipynb` | Buat fitur |
| `03_model1_clustering_ADVANCED.ipynb` | Train Model 1 |
| `04_model2_advice_generation.ipynb` | Setup Model 2 |
| `05_model3_pace_analysis.ipynb` | Train Model 3 |

---

## ❓ FAQ

### Q: Apakah API harus connect ke database?
**A:** TIDAK! Backend yang query database. API hanya terima request dan return prediksi.

### Q: Bagaimana cara dapat API key Gemini?
**A:** 
1. Buka https://makersuite.google.com/app/apikey
2. Login dengan Google
3. Create API key
4. Copy ke file `.env`

### Q: API error "Model not loaded"?
**A:** Pastikan file `.pkl` ada di folder `models/` dan restart API.

### Q: Bisa pakai bahasa selain Python?
**A:** Ya! Backend bisa pakai language apa saja (Node.js, PHP, dll). Yang penting bisa HTTP request.

### Q: Response time berapa lama?
**A:**
- Model 1 & 3: ~50-100ms
- Model 2 (dengan Gemini): ~1-3 detik
- Complete Insights: ~1-4 detik

### Q: Port 8000 sudah dipakai?
**A:** Edit `.env` → `API_PORT=8001`, lalu restart.

---

## 📞 Support & Documentation

### Dokumentasi Lengkap:

| File | Deskripsi |
|------|-----------|
| **PANDUAN_API.md** | Tutorial lengkap cara pakai API ⭐ |
| **Swagger UI** | http://localhost:8000/docs (interactive!) |
| `src/backend_integration_example.py` | Contoh code lengkap |

### Troubleshooting:

**Problem:** API tidak bisa start
**Solution:** 
```bash
pip install -r requirements.txt
python src/api/main.py
```

**Problem:** "Cannot connect to API"
**Solution:** Pastikan server running (jangan CTRL+C)

---

## 📊 Model Performance

| Model | Metrik | Score |
|-------|--------|-------|
| Model 1 (Clustering) | Silhouette Score | 0.78 |
| Model 3 (Pace) | R² Score | 0.85 |
| Combined Accuracy | Overall | 82% |

---

## 👥 Team

**Capstone Project Team**
- Machine Learning Engineer
- Backend Developer
- Frontend Developer

---

## 📝 License

MIT License - Lihat file `LICENSE` untuk detail.

---

## 🎉 Quick Links

- **API Documentation:** http://localhost:8000/docs
- **Tutorial Lengkap:** `PANDUAN_API.md`
- **Contoh Code:** `src/backend_integration_example.py`
- **Get Started:** [Cara Install](#cara-install)

---

**Butuh bantuan?** Baca **PANDUAN_API.md** atau hubungi tim ML!

**Happy Coding! 🚀**
