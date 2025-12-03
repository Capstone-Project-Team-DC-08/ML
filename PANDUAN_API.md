# 📘 Panduan Lengkap Menggunakan API

**AI Learning Insight API - Tutorial Step-by-Step**

> **Dokumen ini untuk:** Tim Backend & Frontend  
> **Level:** Pemula sampai Advanced  
> **Waktu baca:** ~15 menit

---

## 📋 Daftar Isi

**Part 1: Basics**
1. [Intro - Apa itu API ini?](#part-1-intro)
2. [Install & Setup](#part-2-install--setup)
3. [Test Pertama Kali](#part-3-test-pertama-kali)

**Part 2: Untuk Backend**
4. [Cara Kerja API](#part-4-cara-kerja-api)
5. [Query Database yang Benar](#part-5-query-database-yang-benar)
6. [Panggil API dari Backend](#part-6-panggil-api-dari-backend)

**Part 3: API Reference**
7. [Semua Endpoint](#part-7-semua-endpoint)
8. [Response Format](#part-8-response-format)

**Part 4: Advanced**
9. [Error Handling](#part-9-error-handling)
10. [Tips & Tricks](#part-10-tips--tricks)

---

# PART 1: BASICS

## Part 1: Intro

### Apa itu API ini?

API ini adalah **jembatan** antara website Anda dengan Model Machine Learning.

```
Website Anda  →  API ini  →  ML Models  →  Hasil Prediksi
```

### 3 Model yang Tersedia:

| Model | Input | Output | Untuk Apa? |
|-------|-------|--------|------------|
| **Model 1** | user_id | Persona label | Label di dashboard user |
| **Model 2** | user_id + name | Saran AI | Insight panel siswa |
| **Model 3** | user_id + journey_id | Label pace + % | Badge di card course |

### Prinsip Kerja:

✅ **API TIDAK terhubung ke database**  
✅ **Backend yang query database**  
✅ **Backend kirim data ke API**  
✅ **API return hasil prediksi**  
✅ **Backend kirim ke frontend**

---

## Part 2: Install & Setup

### Step 1: Pastikan Python Terinstall

```bash
python --version
# Harus 3.8 atau lebih tinggi
```

### Step 2: Aktifkan Virtual Environment

```bash
# Windows
cd d:\kuliah\sem7\asah\capstone\ML
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

Lihat `(venv)` di terminal? ✅ Sudah benar!

### Step 3: Install Library

```bash
pip install -r requirements.txt
```

Tunggu sampai selesai (~2-3 menit).

### Step 4: Setup API Key (Opsional)

```bash
# Copy template
copy .env.example .env
```

Edit file `.env`:
```env
GEMINI_API_KEY=your_api_key_here
```

**Cara dapat API key:**
1. Buka https://makersuite.google.com/app/apikey
2. Login Google → Create API key
3. Copy paste ke `.env`

**Tanpa API key?** Tetap jalan, tapi Model 2 pakai template simple.

### Step 5: Jalankan Server

```bash
cd src/api
python main.py
```

**Output yang benar:**
```
============================================================
🚀 Starting AI Learning Insight API...
============================================================
✓ Clustering model loaded from ...
✓ Pace model loaded from ...
✓ Gemini AI configured
✅ All models loaded successfully!
============================================================
📝 API Documentation available at: http://localhost:8000/docs
============================================================
```

**Jangan tutup terminal ini!** Biarkan running.

---

## Part 3: Test Pertama Kali

### Cara 1: Pakai Browser (Paling Mudah!)

1. Buka browser
2. Ketik: `http://localhost:8000/docs`
3. Anda akan lihat **Swagger UI** (interface interaktif)

### Test Health Check:

1. Cari endpoint `/health`
2. Klik "Try it out"
3. Klik "Execute"
4. Lihat response:

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

✅ Semua `true`? **API siap dipakai!**

### Cara 2: Pakai cURL (Terminal)

```bash
curl http://localhost:8000/health
```

### Cara 3: Pakai Python

```python
import requests

response = requests.get('http://localhost:8000/health')
print(response.json())
```

---

# PART 2: UNTUK BACKEND

## Part 4: Cara Kerja API

### Flow Lengkap:

```
1. USER buka website
   ↓
2. FRONTEND request ke backend: "Tampilkan dashboard user 123"
   ↓
3. BACKEND:
   a. Query database untuk user 123
   b. Hitung 6 fitur yang dibutuhkan
   c. Kirim HTTP request ke ML API
   ↓
4. ML API:
   a. Terima request
   b. Load model
   c. Prediksi
   d. Return hasil
   ↓
5. BACKEND:
   a. Terima hasil dari ML API
   b. Gabung dengan data lain
   c. Return ke frontend
   ↓
6. FRONTEND tampilkan ke user
```

### Yang HARUS Dilakukan Backend:

**Backend bertanggung jawab:**

1. ✅ Query database
2. ✅ Hitung fitur (6 fitur untuk Model 1)
3. ✅ Kirim HTTP request ke ML API
4. ✅ Handle response
5. ✅ Return ke frontend

**Backend TIDAK perlu:**

❌ Install scikit-learn  
❌ Load model ML  
❌ Paham ML algorithm  
❌ Train model

Semua ML logic ada di API!

---

## Part 5: Query Database yang Benar

### ⚠️ MASALAH: Nama Kolom Tidak Konsisten!

Database pakai nama kolom BEDA untuk user ID:

| Tabel | Kolom User ID |
|-------|---------------|
| `developer_journey_trackings` | `developer_id` ⚠️ |
| `developer_journey_submissions` | `submitter_id` ⚠️ |
| `developer_journey_completions` | `user_id` ✅ |
| `exam_registrations` | `examinees_id` ⚠️ |

**Semua nilai SAMA** (dari `users.id`), tapi **nama berbeda**!

### SQL Query yang BENAR:

#### Fitur 1: avg_study_hour

```sql
-- Rata-rata jam belajar (0-23)
SELECT AVG(HOUR(last_viewed)) as avg_study_hour
FROM developer_journey_trackings
WHERE developer_id = 123;  -- ⚠️ developer_id, bukan user_id!
```

#### Fitur 2: study_consistency_std

```sql
-- Standar deviasi konsistensi belajar
SELECT STDDEV(day_diff) as consistency_std
FROM (
    SELECT DATEDIFF(
        last_viewed, 
        LAG(last_viewed) OVER (ORDER BY last_viewed)
    ) as day_diff
    FROM developer_journey_trackings
    WHERE developer_id = 123  -- ⚠️ developer_id
) t 
WHERE day_diff IS NOT NULL;
```

#### Fitur 3: completion_speed

```sql
-- Rata-rata durasi menyelesaikan course
SELECT AVG(study_duration) as completion_speed
FROM developer_journey_completions
WHERE user_id = 123  -- ✅ user_id (ini berbeda!)
  AND study_duration IS NOT NULL;
```

#### Fitur 4: avg_exam_score

```sql
-- Rata-rata nilai ujian
SELECT AVG(res.score) as avg_exam_score
FROM exam_results res
JOIN exam_registrations reg ON res.exam_registration_id = reg.id
WHERE reg.examinees_id = 123;  -- ⚠️ examinees_id!
```

#### Fitur 5: submission_fail_rate

```sql
-- Rasio kegagalan submission (0-1)
SELECT 
    COUNT(*) as total,
    SUM(CASE WHEN status IN ('failed', 'rejected') THEN 1 ELSE 0 END) as failed,
    SUM(CASE WHEN status IN ('failed', 'rejected') THEN 1 ELSE 0 END) / COUNT(*) as fail_rate
FROM developer_journey_submissions
WHERE submitter_id = 123;  -- ⚠️ submitter_id!
```

#### Fitur 6: retry_count

```sql
-- Jumlah mengulang kelas
SELECT SUM(enrolling_times - 1) as retry_count
FROM developer_journey_completions
WHERE user_id = 123  -- ✅ user_id
  AND enrolling_times > 0;
```

### Contoh Function Backend (Python):

```python
def get_user_features(user_id):
    """
    Hitung semua fitur untuk user
    Return dict dengan 6 fitur
    """
    
    # Fitur 1: avg_study_hour
    result = db.execute("""
        SELECT AVG(HOUR(last_viewed)) 
        FROM developer_journey_trackings 
        WHERE developer_id = %s
    """, [user_id])
    avg_study_hour = result.fetchone()[0] or 12.0
    
    # Fitur 2: study_consistency_std
    result = db.execute("""
        SELECT STDDEV(day_diff) FROM (
            SELECT DATEDIFF(
                last_viewed, 
                LAG(last_viewed) OVER (ORDER BY last_viewed)
            ) as day_diff
            FROM developer_journey_trackings
            WHERE developer_id = %s
        ) t WHERE day_diff IS NOT NULL
    """, [user_id])
    study_consistency_std = result.fetchone()[0] or 0.0
    
    # Fitur 3: completion_speed
    result = db.execute("""
        SELECT AVG(study_duration)
        FROM developer_journey_completions
        WHERE user_id = %s
    """, [user_id])
    completion_speed = result.fetchone()[0] or 40.0
    
    # Fitur 4: avg_exam_score
    result = db.execute("""
        SELECT AVG(res.score)
        FROM exam_results res
        JOIN exam_registrations reg ON res.exam_registration_id = reg.id
        WHERE reg.examinees_id = %s
    """, [user_id])
    avg_exam_score = result.fetchone()[0] or 70.0
    
    # Fitur 5: submission_fail_rate
    result = db.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status IN ('failed', 'rejected') THEN 1 ELSE 0 END) as failed
        FROM developer_journey_submissions
        WHERE submitter_id = %s
    """, [user_id])
    row = result.fetchone()
    submission_fail_rate = (row['failed'] / row['total']) if row['total'] > 0 else 0.0
    
    # Fitur 6: retry_count
    result = db.execute("""
        SELECT SUM(enrolling_times - 1)
        FROM developer_journey_completions
        WHERE user_id = %s
    """, [user_id])
    retry_count = result.fetchone()[0] or 0
    
    return {
        'avg_study_hour': float(avg_study_hour),
        'study_consistency_std': float(study_consistency_std),
        'completion_speed': float(completion_speed),
        'avg_exam_score': float(avg_exam_score),
        'submission_fail_rate': float(submission_fail_rate),
        'retry_count': int(retry_count)
    }
```

**⚠️ INGAT:** Nama kolom berbeda untuk setiap tabel!

---

## Part 6: Panggil API dari Backend

### Python (Flask/Django):

```python
import requests

def get_student_dashboard(user_id):
    """
    Backend endpoint untuk dashboard siswa
    """
    
    # 1. Get user info dari database
    user = db.query("SELECT * FROM users WHERE id = %s", [user_id])
    
    # 2. Call ML API untuk complete insights
    ml_response = requests.get(
        'http://localhost:8000/api/v1/insights/' + str(user_id),
        params={'user_name': user['display_name']}
    )
    
    # 3. Handle error
    if ml_response.status_code != 200:
        return {'error': 'ML API error'}, 500
    
    insights = ml_response.json()
    
    # 4. Return ke frontend
    return {
        'user': {
            'id': user_id,
            'name': user['display_name'],
            'email': user['email']
        },
        'persona': insights['persona'],
        'pace': insights['learning_pace'],
        'advice': insights['personalized_advice']
    }
```

### Node.js (Express):

```javascript
const axios = require('axios');

async function getStudentDashboard(userId) {
    // 1. Get user from database
    const user = await db.query('SELECT * FROM users WHERE id = ?', [userId]);
    
    // 2. Call ML API
    const mlResponse = await axios.get(
        `http://localhost:8000/api/v1/insights/${userId}`,
        { params: { user_name: user.display_name } }
    );
    
    // 3. Return to frontend
    return {
        user: {
            id: userId,
            name: user.display_name,
            email: user.email
        },
        persona: mlResponse.data.persona,
        pace: mlResponse.data.learning_pace,
        advice: mlResponse.data.personalized_advice
    };
}
```

### PHP (Laravel):

```php
use Illuminate\Support\Facades\Http;

function getStudentDashboard($userId) {
    // 1. Get user
    $user = User::find($userId);
    
    // 2. Call ML API
    $response = Http::get("http://localhost:8000/api/v1/insights/{$userId}", [
        'user_name' => $user->display_name
    ]);
    
    $insights = $response->json();
    
    // 3. Return
    return [
        'user' => [
            'id' => $userId,
            'name' => $user->display_name,
            'email' => $user->email
        ],
        'persona' => $insights['persona'],
        'pace' => $insights['learning_pace'],
        'advice' => $insights['personalized_advice']
    ];
}
```

---

# PART 3: API REFERENCE

## Part 7: Semua Endpoint

### 1. Health Check

**URL:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-03T08:00:00",
  "models_loaded": {
    "clustering_model": true,
    "pace_model": true,
    "advice_generator": true
  }
}
```

**Kapan dipakai:** Cek apakah API running dengan baik.

---

### 2. Get Persona (Model 1)

**URL:** `POST /api/v1/persona/predict`

**Request:**
```json
{
  "user_id": 123
}
```

**Response:**
```json
{
  "user_id": 123,
  "persona_label": "The Night Owl",
  "cluster_id": 2,
  "confidence": 0.85,
  "characteristics": [
    "Aktif belajar di malam hari (19:00-24:00)",
    "Konsistensi belajar tinggi",
    "Nilai ujian rata-rata baik"
  ]
}
```

**Kapan dipakai:** 
- Tampilkan label persona di dashboard user
- "Kamu adalah The Night Owl!"

---

### 3. Generate Advice (Model 2)

**URL:** `POST /api/v1/advice/generate`

**Request:**
```json
{
  "user_id": 123,
  "name": "Budi"
}
```

**Response:**
```json
{
  "user_id": 123,
  "name": "Budi",
  "advice_text": "Halo Budi! Kamu adalah tipe Night Owl yang suka belajar di malam hari. Kamu menyelesaikan course 20% lebih cepat dari rata-rata siswa, luar biasa! Namun, nilai ujianmu bisa lebih baik lagi. Coba luangkan waktu ekstra untuk review materi sebelum ujian, dan jangan ragu bertanya di forum jika ada yang kurang jelas. Semangat terus belajarnya! 🚀",
  "persona_context": "The Night Owl",
  "pace_context": "20% lebih cepat dari rata-rata",
  "generated_at": "2025-12-03T08:00:00"
}
```

**Kapan dipakai:**
- Insight panel di dashboard siswa
- Motivational message

---

### 4. Analyze Pace (Model 3)

**URL:** `POST /api/v1/pace/analyze`

**Request:**
```json
{
  "user_id": 123,
  "journey_id": 45
}
```

**Response:**
```json
{
  "user_id": 123,
  "journey_id": 45,
  "journey_name": "Belajar Machine Learning",
  "pace_label": "Fast Learner",
  "pace_percentage": 25.5,
  "user_duration_hours": 30.0,
  "avg_duration_hours": 40.0,
  "expected_duration_hours": 50.0,
  "percentile_rank": 75.5
}
```

**Kapan dipakai:**
- Badge di card course
- "Fast Learner" badge with green color

---

### 5. Complete Insights (ALL MODELS) ⭐

**URL:** `GET /api/v1/insights/{user_id}?user_name=Budi`

**Response:**
```json
{
  "user_id": 123,
  "user_name": "Budi",
  "generated_at": "2025-12-03T08:00:00",
  "persona": {
    "label": "The Night Owl",
    "cluster_id": 2,
    "confidence": 0.85,
    "characteristics": ["..."]
  },
  "learning_pace": {
    "label": "Fast Learner",
    "percentage": 25.5,
    "insight": "Kamu 25.5% lebih cepat dari rata-rata siswa"
  },
  "personalized_advice": {
    "text": "Halo Budi! ...",
    "context": {
      "persona": "The Night Owl",
      "pace": "25.5% lebih cepat dari rata-rata"
    }
  }
}
```

**Kapan dipakai:**
- Dashboard utama siswa
- Paling efisien! 1 call dapat semua data

---

## Part 8: Response Format

### Success Response

**Status Code:** 200 OK

**Format:**
```json
{
  "field1": "value1",
  "field2": 123,
  "field3": ["array", "values"]
}
```

### Error Response

**Status Code:** 4xx atau 5xx

**Format:**
```json
{
  "error": "ErrorType",
  "message": "Detail error message",
  "timestamp": "2025-12-03T08:00:00"
}
```

**Common Errors:**

| Code | Error | Penyebab | Solusi |
|------|-------|----------|--------|
| 400 | Bad Request | Request format salah | Cek JSON format |
| 404 | Not Found | Endpoint salah | Cek URL |
| 500 | Internal Error | Error di server | Cek logs |
| 503 | Service Unavailable | Model not loaded | Restart API |

---

# PART 4: ADVANCED

## Part 9: Error Handling

### Di Backend:

```python
import requests

def call_ml_api_safe(user_id):
    try:
        response = requests.get(
            f'http://localhost:8000/api/v1/insights/{user_id}',
            params={'user_name': 'User'},
            timeout=10  # 10 detik timeout
        )
        
        if response.status_code == 200:
            return response.json()
        else:
            # Handle error response
            error = response.json()
            print(f"ML API Error: {error['message']}")
            return None
            
    except requests.exceptions.Timeout:
        print("ML API timeout")
        return None
        
    except requests.exceptions.ConnectionError:
        print("Cannot connect to ML API")
        return None
        
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return None
```

### Fallback Strategy:

```python
def get_insights_with_fallback(user_id):
    # Try ML API
    insights = call_ml_api_safe(user_id)
    
    if insights:
        return insights
    
    # Fallback: return default
    return {
        'persona': {
            'label': 'The Learner',
            'characteristics': ['Keep learning!']
        },
        'pace': {
            'label': 'Average',
            'insight': 'You are doing great!'
        },
        'advice': {
            'text': 'Keep up the good work!'
        }
    }
```

---

## Part 10: Tips & Tricks

### 1. Caching Response

```python
from functools import lru_cache
from datetime import datetime, timedelta

# Cache untuk 5 menit
cache = {}
CACHE_DURATION = timedelta(minutes=5)

def get_persona_cached(user_id):
    # Check cache
    if user_id in cache:
        cached_time, cached_data = cache[user_id]
        if datetime.now() - cached_time < CACHE_DURATION:
            return cached_data
    
    # Call API
    response = requests.post(
        'http://localhost:8000/api/v1/persona/predict',
        json={'user_id': user_id}
    )
    data = response.json()
    
    # Save to cache
    cache[user_id] = (datetime.now(), data)
    
    return data
```

### 2. Batch Processing

```python
# Jika perlu banyak user sekaligus
user_ids = [123, 456, 789]

response = requests.post(
    'http://localhost:8000/api/v1/persona/batch',
    json={'user_ids': user_ids}
)

results = response.json()['results']
for result in results:
    print(f"User {result['user_id']}: {result['persona_label']}")
```

### 3. Async Requests (Python)

```python
import asyncio
import aiohttp

async def get_insights_async(user_id):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f'http://localhost:8000/api/v1/insights/{user_id}'
        ) as response:
            return await response.json()

# Call multiple users parallel
async def get_multiple_insights(user_ids):
    tasks = [get_insights_async(uid) for uid in user_ids]
    return await asyncio.gather(*tasks)
```

### 4. Monitoring

```python
import time

def call_api_with_monitoring(endpoint, data):
    start_time = time.time()
    
    response = requests.post(endpoint, json=data)
    
    duration = time.time() - start_time
    
    # Log
    print(f"API Call: {endpoint}")
    print(f"Duration: {duration:.2f}s")
    print(f"Status: {response.status_code}")
    
    return response.json()
```

---

## 📝 Checklist Integration

### Untuk Tim Backend:

- [ ] API server running di http://localhost:8000
- [ ] Health check return status "healthy"
- [ ] Sudah paham SQL query untuk 6 fitur
- [ ] Sudah test panggil API dari backend code
- [ ] Sudah implement error handling
- [ ] Sudah test dengan data real

### Untuk Tim Frontend:

- [ ] Sudah koordinasi dengan backend untuk endpoint URLs
- [ ] Sudah dapat contoh response format
- [ ] Sudah bikin mock data untuk development
- [ ] UI component sudah siap untuk display data

---

## 🚀 Next Steps

1. **Test API** dengan Swagger UI
2. **Implement** query database di backend
3. **Integrate** dengan backend endpoints
4. **Test** dengan data real
5. **Deploy** ke production!

---

## 📞 Butuh Bantuan?

- **Swagger UI:** http://localhost:8000/docs
- **Main README:** `README.md`
- **Contoh Code:** `src/backend_integration_example.py`

**Happy Coding! 🎉**
