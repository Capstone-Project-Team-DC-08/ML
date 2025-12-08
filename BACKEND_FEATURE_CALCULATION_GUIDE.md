# 📊 Backend Integration Guide: Calculating Features from Database

## Overview

API ML membutuhkan **fitur yang dihitung** dari data mentah di database. Proses:
```
Database Tables → Calculate Features → Call ML API → Get Prediction
```

---

## 🔢 Model 1: Persona Classification - Feature Calculations

**⚠️ Model 1 menggunakan Classification (Random Forest Classifier)**

### 5 Persona Categories (LabelEncoder Order):

| Class | Persona | Deskripsi |
|-------|---------|-----------|
| 0 | The Consistent | Steady Learner |
| 1 | The Deep Diver | Slow but Thorough |
| 2 | The Night Owl | Night-time Learner |
| 3 | The Sprinter | Fast Learner |
| 4 | The Struggler | Need Support |

### Request yang dibutuhkan:
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

### Cara menghitung setiap fitur:

---

### 1. `avg_study_hour` - Rata-rata Jam Belajar

**Sumber**: `developer_journey_trackings.first_opened_at`

**Logika**: Ekstrak jam dari waktu akses materi, lalu rata-ratakan.

```sql
-- SQL Query
SELECT 
    developer_id,
    AVG(HOUR(first_opened_at)) as avg_study_hour
FROM developer_journey_trackings
WHERE developer_id = :user_id
  AND first_opened_at IS NOT NULL
GROUP BY developer_id;
```

**PHP/Laravel Example**:
```php
$avgStudyHour = DeveloperJourneyTracking::where('developer_id', $userId)
    ->whereNotNull('first_opened_at')
    ->selectRaw('AVG(HOUR(first_opened_at)) as avg_hour')
    ->value('avg_hour') ?? 12.0;
```

**Catatan**: Nilai berkisar 0-23 (jam dalam sehari)

---

### 2. `study_consistency_std` - Standar Deviasi Konsistensi Belajar

**Sumber**: `developer_journey_trackings`

**Logika**: Hitung jumlah aktivitas per hari, lalu hitung standar deviasinya.

```sql
-- Step 1: Hitung aktivitas per hari
WITH daily_activity AS (
    SELECT 
        developer_id,
        DATE(first_opened_at) as study_date,
        COUNT(*) as materials_accessed
    FROM developer_journey_trackings
    WHERE developer_id = :user_id
      AND first_opened_at IS NOT NULL
    GROUP BY developer_id, DATE(first_opened_at)
)
-- Step 2: Hitung standar deviasi
SELECT 
    developer_id,
    STDDEV(materials_accessed) as study_consistency_std
FROM daily_activity
GROUP BY developer_id;
```

**PHP/Laravel Example**:
```php
// Get daily activity counts
$dailyActivities = DeveloperJourneyTracking::where('developer_id', $userId)
    ->whereNotNull('first_opened_at')
    ->selectRaw('DATE(first_opened_at) as date, COUNT(*) as count')
    ->groupBy('date')
    ->pluck('count')
    ->toArray();

// Calculate standard deviation
$stdDev = $this->calculateStdDev($dailyActivities);

private function calculateStdDev(array $numbers): float
{
    if (count($numbers) < 2) return 0;
    $mean = array_sum($numbers) / count($numbers);
    $variance = array_sum(array_map(fn($x) => pow($x - $mean, 2), $numbers)) / count($numbers);
    return sqrt($variance);
}
```

**Catatan**: 
- Nilai rendah = konsisten (bagus)
- Nilai tinggi = tidak konsisten

---

### 3. `completion_speed` - Kecepatan Penyelesaian

**Sumber**: `developer_journey_completions` + `developer_journeys`

**Logika**: Bandingkan durasi user dengan ekspektasi (`hours_to_study`)

```sql
SELECT 
    djc.user_id,
    djc.study_duration,
    dj.hours_to_study,
    -- Rasio: < 1 = lebih cepat, > 1 = lebih lambat
    CASE 
        WHEN dj.hours_to_study > 0 THEN djc.study_duration / dj.hours_to_study
        ELSE 1.0
    END as completion_speed
FROM developer_journey_completions djc
JOIN developer_journeys dj ON djc.journey_id = dj.id
WHERE djc.user_id = :user_id;

-- Rata-rata untuk semua journey yang diselesaikan
SELECT 
    user_id,
    AVG(
        CASE 
            WHEN dj.hours_to_study > 0 THEN djc.study_duration / dj.hours_to_study
            ELSE 1.0
        END
    ) as avg_completion_speed
FROM developer_journey_completions djc
JOIN developer_journeys dj ON djc.journey_id = dj.id
WHERE djc.user_id = :user_id
GROUP BY user_id;
```

**PHP/Laravel Example**:
```php
$completionSpeed = DB::table('developer_journey_completions as djc')
    ->join('developer_journeys as dj', 'djc.journey_id', '=', 'dj.id')
    ->where('djc.user_id', $userId)
    ->where('dj.hours_to_study', '>', 0)
    ->selectRaw('AVG(djc.study_duration / dj.hours_to_study) as speed')
    ->value('speed') ?? 1.0;
```

**Catatan**:
- `< 1.0` = lebih cepat dari ekspektasi (Sprinter potential)
- `= 1.0` = sesuai ekspektasi
- `> 1.0` = lebih lambat (Deep Diver potential)

---

### 4. `avg_exam_score` - Rata-rata Nilai Ujian

**Sumber**: `exam_results` + `exam_registrations`

```sql
SELECT 
    er_reg.examinees_id as user_id,
    AVG(er.score) as avg_exam_score
FROM exam_results er
JOIN exam_registrations er_reg ON er.exam_registration_id = er_reg.id
WHERE er_reg.examinees_id = :user_id
GROUP BY er_reg.examinees_id;
```

**PHP/Laravel Example**:
```php
$avgExamScore = DB::table('exam_results as er')
    ->join('exam_registrations as er_reg', 'er.exam_registration_id', '=', 'er_reg.id')
    ->where('er_reg.examinees_id', $userId)
    ->avg('er.score') ?? 75.0;
```

**Catatan**: Nilai 0-100

---

### 5. `submission_fail_rate` - Rasio Kegagalan Submission

**Sumber**: `developer_journey_submissions`

**Logika**: Hitung persentase submission yang gagal

```sql
SELECT 
    submitter_id as user_id,
    COUNT(CASE WHEN status = 'failed' OR status = 'revision_requested' THEN 1 END) as failed,
    COUNT(*) as total,
    COUNT(CASE WHEN status = 'failed' OR status = 'revision_requested' THEN 1 END) * 1.0 / COUNT(*) as fail_rate
FROM developer_journey_submissions
WHERE submitter_id = :user_id
GROUP BY submitter_id;
```

**PHP/Laravel Example**:
```php
$submissions = DeveloperJourneySubmission::where('submitter_id', $userId)
    ->selectRaw('
        COUNT(*) as total,
        SUM(CASE WHEN status IN ("failed", "revision_requested") THEN 1 ELSE 0 END) as failed
    ')
    ->first();

$failRate = ($submissions->total > 0) 
    ? $submissions->failed / $submissions->total 
    : 0.0;
```

**Catatan**: Nilai 0-1 (0 = tidak pernah gagal, 1 = selalu gagal)

---

### 6. `retry_count` - Jumlah Pengulangan

**Sumber**: `developer_journey_completions.enrolling_times`

```sql
SELECT 
    user_id,
    SUM(enrolling_times - 1) as total_retries,  -- -1 karena enrollment pertama bukan retry
    AVG(enrolling_times - 1) as avg_retries
FROM developer_journey_completions
WHERE user_id = :user_id
GROUP BY user_id;
```

**PHP/Laravel Example**:
```php
$retryCount = DeveloperJourneyCompletion::where('user_id', $userId)
    ->sum(DB::raw('GREATEST(enrolling_times - 1, 0)')) ?? 0;
```

---

## 🚀 Model 3: Pace Classification - Feature Calculations

**⚠️ UPDATED: Model 3 sekarang menggunakan Classification (Random Forest), bukan Clustering!**

### 3 Pace Categories (LabelEncoder Order):

| Class | Label | Deskripsi |
|-------|-------|-----------|
| 0 | Consistent Learner | Belajar teratur dan stabil |
| 1 | Fast Learner | Belajar cepat dan efisien |
| 2 | Reflective Learner | Belajar mendalam dan reflektif |

### Request yang dibutuhkan:
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

---

### 1. `completion_speed` - Kecepatan Penyelesaian

**Sama seperti Model 1** - lihat bagian di atas.

---

### 2. `study_consistency_std` - Standar Deviasi Konsistensi

**Sama seperti Model 1** - lihat bagian di atas.

---

### 3. `avg_study_hour` - Rata-rata Jam Belajar

**Sama seperti Model 1** - lihat bagian di atas.

---

### 4. `completed_modules` - Jumlah Modul Selesai

**Sumber**: `developer_journey_trackings`

```sql
SELECT COUNT(*) as completed_modules
FROM developer_journey_trackings
WHERE developer_id = :user_id
  AND journey_id = :journey_id
  AND completed_at IS NOT NULL;
```

**PHP/Laravel Example**:
```php
$completedModules = DeveloperJourneyTracking::where('developer_id', $userId)
    ->where('journey_id', $journeyId)
    ->whereNotNull('completed_at')
    ->count();
```

---

### 5. `total_modules_viewed` - Total Modul yang Dilihat

**Sumber**: `developer_journey_trackings`

```sql
SELECT COUNT(*) as total_modules_viewed
FROM developer_journey_trackings
WHERE developer_id = :user_id
  AND journey_id = :journey_id
  AND first_opened_at IS NOT NULL;
```

**PHP/Laravel Example**:
```php
$totalModulesViewed = DeveloperJourneyTracking::where('developer_id', $userId)
    ->where('journey_id', $journeyId)
    ->whereNotNull('first_opened_at')
    ->count();
```

---

## 🔄 Complete Backend Integration Flow

### PHP/Laravel Service Example:

```php
<?php

namespace App\Services;

use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\DB;

class MLApiService
{
    private string $apiBaseUrl = 'http://localhost:8000';
    
    /**
     * Get persona prediction for a user
     */
    public function getPrediction(int $userId): array
    {
        // Step 1: Calculate all features from database
        $features = $this->calculatePersonaFeatures($userId);
        
        // Step 2: Call ML API
        $response = Http::post("{$this->apiBaseUrl}/api/v1/persona/predict", [
            'user_id' => $userId,
            'features' => $features
        ]);
        
        return $response->json();
    }
    
    /**
     * Calculate persona features from database
     */
    private function calculatePersonaFeatures(int $userId): array
    {
        return [
            'avg_study_hour' => $this->getAvgStudyHour($userId),
            'study_consistency_std' => $this->getStudyConsistencyStd($userId),
            'completion_speed' => $this->getCompletionSpeed($userId),
            'avg_exam_score' => $this->getAvgExamScore($userId),
            'submission_fail_rate' => $this->getSubmissionFailRate($userId),
            'retry_count' => $this->getRetryCount($userId),
        ];
    }
    
    private function getAvgStudyHour(int $userId): float
    {
        return DB::table('developer_journey_trackings')
            ->where('developer_id', $userId)
            ->whereNotNull('first_opened_at')
            ->selectRaw('AVG(HOUR(first_opened_at)) as avg_hour')
            ->value('avg_hour') ?? 12.0;
    }
    
    private function getAvgExamScore(int $userId): float
    {
        return DB::table('exam_results as er')
            ->join('exam_registrations as reg', 'er.exam_registration_id', '=', 'reg.id')
            ->where('reg.examinees_id', $userId)
            ->avg('er.score') ?? 75.0;
    }
    
    // ... implement other methods similarly
}
```

---

## 📋 Quick Reference Table

### Model 1: Persona Classification Features

| Feature | Source Table(s) | Key Columns | Calculation |
|---------|-----------------|-------------|-------------|
| `avg_study_hour` | `developer_journey_trackings` | `first_opened_at` | AVG(HOUR(first_opened_at)) |
| `study_consistency_std` | `developer_journey_trackings` | `first_opened_at` | STDDEV of daily activity count |
| `completion_speed` | `developer_journey_completions` + `developer_journeys` | `study_duration`, `hours_to_study` | study_duration / hours_to_study |
| `avg_exam_score` | `exam_results` + `exam_registrations` | `score`, `examinees_id` | AVG(score) |
| `submission_fail_rate` | `developer_journey_submissions` | `status`, `submitter_id` | COUNT(failed) / COUNT(total) |
| `retry_count` | `developer_journey_completions` | `enrolling_times` | SUM(enrolling_times - 1) |

### Model 3: Pace Classification Features

| Feature | Source Table(s) | Key Columns | Calculation |
|---------|-----------------|-------------|-------------|
| `completion_speed` | Same as Model 1 | | |
| `study_consistency_std` | Same as Model 1 | | |
| `avg_study_hour` | Same as Model 1 | | |
| `completed_modules` | `developer_journey_trackings` | `completed_at` | COUNT where completed_at IS NOT NULL |
| `total_modules_viewed` | `developer_journey_trackings` | `first_opened_at` | COUNT where first_opened_at IS NOT NULL |

---

## ⚠️ Edge Cases / Default Values

Jika data tidak tersedia, gunakan default values:

```php
// Model 1: Persona Features
$personaDefaults = [
    'avg_study_hour' => 12.0,       // Tengah hari
    'study_consistency_std' => 100.0, // Cukup konsisten
    'completion_speed' => 1.0,       // Rata-rata
    'avg_exam_score' => 75.0,        // Score menengah
    'submission_fail_rate' => 0.1,   // 10% fail rate
    'retry_count' => 0,              // Tidak pernah retry
];

// Model 3: Pace Features
$paceDefaults = [
    'completion_speed' => 1.0,
    'study_consistency_std' => 100.0,
    'avg_study_hour' => 14.0,
    'completed_modules' => 30,
    'total_modules_viewed' => 50,
];
```

---

## 🎯 Summary: API Call Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                        YOUR BACKEND                             │
├─────────────────────────────────────────────────────────────────┤
│  1. Receive request with user_id                                │
│  2. Query database tables:                                      │
│     - developer_journey_trackings                               │
│     - developer_journey_completions                             │
│     - developer_journey_submissions                             │
│     - exam_results + exam_registrations                         │
│  3. Calculate features (avg_study_hour, etc.)                   │
│  4. Send to ML API with calculated features                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         ML API                                  │
├─────────────────────────────────────────────────────────────────┤
│  POST /api/v1/persona/predict                                   │
│  {                                                              │
│    "user_id": 123,                                              │
│    "features": { calculated from your database }                │
│  }                                                              │
│                                                                 │
│  Returns: persona_label, confidence, characteristics            │
└─────────────────────────────────────────────────────────────────┘
```