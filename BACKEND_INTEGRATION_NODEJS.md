# 🔗 Panduan Integrasi Backend (Node.js/Express) dengan ML API

**For Backend Team - Ready to Use!**

---

## 📋 Table of Contents

1. [Konsep Developer ID vs User ID](#konsep-developer-id-vs-user-id)
2. [Data yang Dibutuhkan](#data-yang-dibutuhkan)
3. [SQL Queries Lengkap](#sql-queries-lengkap)
4. [Implementasi Express.js](#implementasi-expressjs)
5. [Testing](#testing)

---

## 1. Konsep Developer ID vs User ID

### Penjelasan:

**Problem:**
- Tabel `users` punya sedikit data (31 users)
- Untuk ML perlu data lebih banyak
- Tabel tracking, submissions, dll pakai `developer_id` yang lebih banyak

**Solution:**
- Model ML dilatih menggunakan `developer_id` (bukan `users.id`)
- `developer_id` adalah ID developer/siswa yang ada di tabel tracking
- Bisa jadi **sama** dengan `users.id`, atau tidak

**Mapping:**

```javascript
// Di database:
// developer_id (dari trackings) bisa sama dengan users.id
// Contoh:
users.id = 3390  →  sama dengan developer_id = 3390 di trackings
users.id = 5774  →  sama dengan developer_id = 5774 di trackings

// TAPI: tidak semua developer_id ada di tabel users (31 users)!
// Ada banyak developer_id di trackings yang tidak ada di users table
```

**Untuk API:**

```javascript
// Input API tetap pakai "user_id" (untuk konsistensi)
// Tapi nilai yang dikirim adalah developer_id

const developer_id = 3390;  // ID dari trackings/submissions/dll

// Call API
await fetch('http://localhost:8000/api/v1/persona/predict', {
    method: 'POST',
    body: JSON.stringify({ user_id: developer_id })  // Kirim sebagai "user_id"
});
```

---

## 2. Data yang Dibutuhkan

### Untuk API ML (6 Fitur):

| No | Fitur | Tabel Sumber | Kolom Key | Deskripsi |
|----|-------|--------------|-----------|-----------|
| 1 | `avg_study_hour` | `developer_journey_trackings` | `developer_id` | Rata-rata jam akses (0-23) |
| 2 | `study_consistency_std` | `developer_journey_trackings` | `developer_id` | Standar deviasi hari belajar |
| 3 | `completion_speed` | `developer_journey_completions` | `user_id` | Rata-rata durasi selesaikan course |
| 4 | `avg_exam_score` | `exam_results` + `exam_registrations` | `examinees_id` | Rata-rata nilai ujian |
| 5 | `submission_fail_rate` | `developer_journey_submissions` | `submitter_id` | Rasio kegagalan submission |
| 6 | `retry_count` | `developer_journey_completions` | `user_id` | Jumlah mengulang kelas |

### Untuk Display (User Info):

| Data | Tabel Sumber | Kolom | Untuk Apa |
|------|--------------|-------|-----------|
| `name` | `users` | `display_name` | Nama user untuk advice |
| `journey_name` | `developer_journeys` | `name` | Nama course |
| `hours_to_study` | `developer_journeys` | `hours_to_study` | Ekspektasi durasi |

---

## 3. SQL Queries Lengkap

### Query 1: Get User Basic Info

```sql
-- Get user info (jika ada di tabel users)
SELECT 
    id,
    display_name,
    name,
    user_role
FROM users
WHERE id = ?;
```

### Query 2: Calculate avg_study_hour

```sql
-- Rata-rata jam belajar (0-23)
SELECT AVG(HOUR(last_viewed)) as avg_study_hour
FROM developer_journey_trackings
WHERE developer_id = ?
  AND last_viewed IS NOT NULL;
```

### Query 3: Calculate study_consistency_std

```sql
-- Standar deviasi konsistensi belajar
-- (Kompleks: butuh hitung gap antar session)

WITH study_sessions AS (
    SELECT 
        developer_id,
        DATE(last_viewed) as study_date,
        ROW_NUMBER() OVER (PARTITION BY developer_id ORDER BY DATE(last_viewed)) as rn
    FROM developer_journey_trackings
    WHERE developer_id = ?
      AND last_viewed IS NOT NULL
    GROUP BY developer_id, DATE(last_viewed)
),
date_gaps AS (
    SELECT 
        s1.developer_id,
        DATEDIFF(s2.study_date, s1.study_date) as day_gap
    FROM study_sessions s1
    JOIN study_sessions s2 
        ON s1.developer_id = s2.developer_id 
        AND s2.rn = s1.rn + 1
)
SELECT 
    COALESCE(STDDEV(day_gap), 0) as study_consistency_std
FROM date_gaps
WHERE developer_id = ?;
```

**Alternative (Simpler):**

```sql
-- Simplified version (count unique days vs total days)
SELECT 
    COALESCE(
        STDDEV(DATEDIFF(
            current_date,
            LAG(current_date) OVER (ORDER BY current_date)
        )),
        0
    ) as study_consistency_std
FROM (
    SELECT DISTINCT DATE(last_viewed) as current_date
    FROM developer_journey_trackings
    WHERE developer_id = ?
      AND last_viewed IS NOT NULL
    ORDER BY current_date
) dates;
```

### Query 4: Calculate completion_speed

```sql
-- Rata-rata durasi menyelesaikan course (dalam jam)
SELECT COALESCE(AVG(study_duration), 0) as completion_speed
FROM developer_journey_completions
WHERE user_id = ?
  AND study_duration IS NOT NULL
  AND study_duration > 0;
```

### Query 5: Calculate avg_exam_score

```sql
-- Rata-rata nilai ujian
SELECT COALESCE(AVG(res.score), 0) as avg_exam_score
FROM exam_results res
JOIN exam_registrations reg ON res.exam_registration_id = reg.id
WHERE reg.examinees_id = ?
  AND res.score IS NOT NULL;
```

### Query 6: Calculate submission_fail_rate

```sql
-- Rasio kegagalan submission
SELECT 
    COUNT(*) as total_submissions,
    SUM(CASE 
        WHEN status IN ('failed', 'rejected', 'revision_requested') 
        THEN 1 
        ELSE 0 
    END) as failed_submissions,
    CASE 
        WHEN COUNT(*) > 0 
        THEN SUM(CASE 
            WHEN status IN ('failed', 'rejected', 'revision_requested') 
            THEN 1 
            ELSE 0 
        END) / COUNT(*) 
        ELSE 0 
    END as submission_fail_rate
FROM developer_journey_submissions
WHERE submitter_id = ?;
```

### Query 7: Calculate retry_count

```sql
-- Jumlah mengulang kelas
SELECT COALESCE(SUM(enrolling_times - 1), 0) as retry_count
FROM developer_journey_completions
WHERE user_id = ?
  AND enrolling_times > 1;
```

### Query 8: Get Journey Info (untuk pace analysis)

```sql
-- Info course/journey
SELECT 
    id as journey_id,
    name as journey_name,
    hours_to_study,
    difficulty
FROM developer_journeys
WHERE id = ?;
```

### Query 9: Get User Journey Duration

```sql
-- Durasi user untuk specific journey
SELECT 
    study_duration,
    journey_id
FROM developer_journey_completions
WHERE user_id = ?
  AND journey_id = ?
ORDER BY updated_at DESC
LIMIT 1;
```

### Query 10: Get Average Journey Duration (Population)

```sql
-- Rata-rata durasi populasi untuk journey
SELECT 
    journey_id,
    COALESCE(AVG(study_duration), 0) as avg_duration,
    COUNT(*) as total_completions
FROM developer_journey_completions
WHERE journey_id = ?
  AND study_duration IS NOT NULL
  AND study_duration > 0
GROUP BY journey_id;
```

---

## 4. Implementasi Express.js

### Setup Project

```bash
# Install dependencies
npm install express axios mysql2 dotenv cors
```

### File Structure

```
backend/
├── config/
│   └── database.js          # Database connection
├── services/
│   ├── mlFeatures.js        # Calculate ML features
│   └── mlApiClient.js       # Call ML API
├── routes/
│   └── insights.js          # API routes
├── .env
└── server.js
```

### .env File

```env
# Database
DB_HOST=localhost
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_NAME=your_database_name
DB_PORT=3306

# ML API
ML_API_URL=http://localhost:8000

# Server
PORT=3000
```

### config/database.js

```javascript
const mysql = require('mysql2/promise');
require('dotenv').config();

const pool = mysql.createPool({
    host: process.env.DB_HOST,
    user: process.env.DB_USER,
    password: process.env.DB_PASSWORD,
    database: process.env.DB_NAME,
    port: process.env.DB_PORT,
    waitForConnections: true,
    connectionLimit: 10,
    queueLimit: 0
});

module.exports = pool;
```

### services/mlFeatures.js

```javascript
const db = require('../config/database');

class MLFeatureService {
    /**
     * Calculate all 6 features needed for ML API
     * @param {number} developerId - Developer ID (not users.id!)
     * @returns {Promise<Object>} Features object
     */
    static async calculateFeatures(developerId) {
        try {
            // Feature 1: avg_study_hour
            const avgStudyHour = await this.getAvgStudyHour(developerId);
            
            // Feature 2: study_consistency_std
            const studyConsistencyStd = await this.getStudyConsistencyStd(developerId);
            
            // Feature 3: completion_speed
            const completionSpeed = await this.getCompletionSpeed(developerId);
            
            // Feature 4: avg_exam_score
            const avgExamScore = await this.getAvgExamScore(developerId);
            
            // Feature 5: submission_fail_rate
            const submissionFailRate = await this.getSubmissionFailRate(developerId);
            
            // Feature 6: retry_count
            const retryCount = await this.getRetryCount(developerId);
            
            return {
                avg_study_hour: avgStudyHour,
                study_consistency_std: studyConsistencyStd,
                completion_speed: completionSpeed,
                avg_exam_score: avgExamScore,
                submission_fail_rate: submissionFailRate,
                retry_count: retryCount
            };
        } catch (error) {
            console.error('Error calculating features:', error);
            throw error;
        }
    }
    
    static async getAvgStudyHour(developerId) {
        const query = `
            SELECT COALESCE(AVG(HOUR(last_viewed)), 12) as avg_study_hour
            FROM developer_journey_trackings
            WHERE developer_id = ?
              AND last_viewed IS NOT NULL
        `;
        
        const [rows] = await db.query(query, [developerId]);
        return parseFloat(rows[0].avg_study_hour);
    }
    
    static async getStudyConsistencyStd(developerId) {
        // Simplified version
        const query = `
            WITH study_dates AS (
                SELECT DISTINCT DATE(last_viewed) as study_date
                FROM developer_journey_trackings
                WHERE developer_id = ?
                  AND last_viewed IS NOT NULL
                ORDER BY study_date
            ),
            date_gaps AS (
                SELECT 
                    DATEDIFF(
                        LEAD(study_date) OVER (ORDER BY study_date),
                        study_date
                    ) as gap
                FROM study_dates
            )
            SELECT COALESCE(STDDEV(gap), 0) as consistency_std
            FROM date_gaps
            WHERE gap IS NOT NULL
        `;
        
        const [rows] = await db.query(query, [developerId]);
        return parseFloat(rows[0].consistency_std || 0);
    }
    
    static async getCompletionSpeed(developerId) {
        const query = `
            SELECT COALESCE(AVG(study_duration), 40) as completion_speed
            FROM developer_journey_completions
            WHERE user_id = ?
              AND study_duration IS NOT NULL
              AND study_duration > 0
        `;
        
        const [rows] = await db.query(query, [developerId]);
        return parseFloat(rows[0].completion_speed);
    }
    
    static async getAvgExamScore(developerId) {
        const query = `
            SELECT COALESCE(AVG(res.score), 70) as avg_exam_score
            FROM exam_results res
            JOIN exam_registrations reg ON res.exam_registration_id = reg.id
            WHERE reg.examinees_id = ?
              AND res.score IS NOT NULL
        `;
        
        const [rows] = await db.query(query, [developerId]);
        return parseFloat(rows[0].avg_exam_score);
    }
    
    static async getSubmissionFailRate(developerId) {
        const query = `
            SELECT 
                COUNT(*) as total,
                SUM(CASE 
                    WHEN status IN ('failed', 'rejected', 'revision_requested') 
                    THEN 1 
                    ELSE 0 
                END) as failed,
                CASE 
                    WHEN COUNT(*) > 0 
                    THEN SUM(CASE 
                        WHEN status IN ('failed', 'rejected', 'revision_requested') 
                        THEN 1 
                        ELSE 0 
                    END) / COUNT(*) 
                    ELSE 0 
                END as fail_rate
            FROM developer_journey_submissions
            WHERE submitter_id = ?
        `;
        
        const [rows] = await db.query(query, [developerId]);
        return parseFloat(rows[0].fail_rate || 0);
    }
    
    static async getRetryCount(developerId) {
        const query = `
            SELECT COALESCE(SUM(enrolling_times - 1), 0) as retry_count
            FROM developer_journey_completions
            WHERE user_id = ?
              AND enrolling_times > 1
        `;
        
        const [rows] = await db.query(query, [developerId]);
        return parseInt(rows[0].retry_count);
    }
    
    /**
     * Get user info (if exists in users table)
     */
    static async getUserInfo(developerId) {
        const query = `
            SELECT 
                id,
                display_name,
                name
            FROM users
            WHERE id = ?
        `;
        
        const [rows] = await db.query(query, [developerId]);
        return rows[0] || { 
            id: developerId, 
            display_name: `User ${developerId}`,
            name: `User ${developerId}`
        };
    }
    
    /**
     * Get journey info for pace analysis
     */
    static async getJourneyInfo(journeyId) {
        const query = `
            SELECT 
                id,
                name,
                hours_to_study,
                difficulty
            FROM developer_journeys
            WHERE id = ?
        `;
        
        const [rows] = await db.query(query, [journeyId]);
        return rows[0];
    }
    
    /**
     * Get user journey duration
     */
    static async getUserJourneyDuration(developerId, journeyId) {
        const query = `
            SELECT study_duration
            FROM developer_journey_completions
            WHERE user_id = ?
              AND journey_id = ?
            ORDER BY updated_at DESC
            LIMIT 1
        `;
        
        const [rows] = await db.query(query, [developerId, journeyId]);
        return rows[0]?.study_duration || 0;
    }
    
    /**
     * Get average journey duration (population)
     */
    static async getAvgJourneyDuration(journeyId) {
        const query = `
            SELECT COALESCE(AVG(study_duration), 0) as avg_duration
            FROM developer_journey_completions
            WHERE journey_id = ?
              AND study_duration IS NOT NULL
              AND study_duration > 0
        `;
        
        const [rows] = await db.query(query, [journeyId]);
        return parseFloat(rows[0].avg_duration);
    }
}

module.exports = MLFeatureService;
```

### services/mlApiClient.js

```javascript
const axios = require('axios');

class MLAPIClient {
    constructor() {
        this.baseURL = process.env.ML_API_URL || 'http://localhost:8000';
        this.timeout = 30000; // 30 seconds
    }
    
    /**
     * Get persona prediction
     */
    async getPersona(userId) {
        try {
            const response = await axios.post(
                `${this.baseURL}/api/v1/persona/predict`,
                { user_id: userId },
                { timeout: this.timeout }
            );
            return response.data;
        } catch (error) {
            console.error('ML API Error (Persona):', error.message);
            throw new Error('Failed to get persona prediction');
        }
    }
    
    /**
     * Generate personalized advice
     */
    async generateAdvice(userId, userName) {
        try {
            const response = await axios.post(
                `${this.baseURL}/api/v1/advice/generate`,
                { 
                    user_id: userId,
                    name: userName
                },
                { timeout: this.timeout }
            );
            return response.data;
        } catch (error) {
            console.error('ML API Error (Advice):', error.message);
            throw new Error('Failed to generate advice');
        }
    }
    
    /**
     * Analyze learning pace
     */
    async analyzePace(userId, journeyId) {
        try {
            const response = await axios.post(
                `${this.baseURL}/api/v1/pace/analyze`,
                { 
                    user_id: userId,
                    journey_id: journeyId
                },
                { timeout: this.timeout }
            );
            return response.data;
        } catch (error) {
            console.error('ML API Error (Pace):', error.message);
            throw new Error('Failed to analyze pace');
        }
    }
    
    /**
     * Get complete insights (all models)
     */
    async getCompleteInsights(userId, userName) {
        try {
            const response = await axios.get(
                `${this.baseURL}/api/v1/insights/${userId}`,
                { 
                    params: { user_name: userName },
                    timeout: this.timeout 
                }
            );
            return response.data;
        } catch (error) {
            console.error('ML API Error (Complete Insights):', error.message);
            throw new Error('Failed to get complete insights');
        }
    }
    
    /**
     * Health check
     */
    async healthCheck() {
        try {
            const response = await axios.get(
                `${this.baseURL}/health`,
                { timeout: 5000 }
            );
            return response.data;
        } catch (error) {
            console.error('ML API Health Check Failed:', error.message);
            return { status: 'unhealthy', error: error.message };
        }
    }
}

module.exports = new MLAPIClient();
```

### routes/insights.js

```javascript
const express = require('express');
const router = express.Router();
const MLFeatureService = require('../services/mlFeatures');
const mlApiClient = require('../services/mlApiClient');

/**
 * GET /api/insights/health
 * Check ML API health
 */
router.get('/health', async (req, res) => {
    try {
        const health = await mlApiClient.healthCheck();
        res.json(health);
    } catch (error) {
        res.status(500).json({ error: error.message });
    }
});

/**
 * GET /api/insights/:developerId/dashboard
 * Get complete dashboard for student
 */
router.get('/:developerId/dashboard', async (req, res) => {
    try {
        const developerId = parseInt(req.params.developerId);
        
        // Get user info
        const userInfo = await MLFeatureService.getUserInfo(developerId);
        
        // Get complete insights from ML API
        const insights = await mlApiClient.getCompleteInsights(
            developerId,
            userInfo.display_name
        );
        
        res.json({
            user: {
                id: developerId,
                name: userInfo.display_name,
                full_name: userInfo.name
            },
            insights: insights
        });
        
    } catch (error) {
        console.error('Error getting dashboard:', error);
        res.status(500).json({ 
            error: 'Failed to get dashboard',
            message: error.message 
        });
    }
});

/**
 * GET /api/insights/:developerId/persona
 * Get only persona prediction
 */
router.get('/:developerId/persona', async (req, res) => {
    try {
        const developerId = parseInt(req.params.developerId);
        
        const persona = await mlApiClient.getPersona(developerId);
        
        res.json(persona);
        
    } catch (error) {
        console.error('Error getting persona:', error);
        res.status(500).json({ error: error.message });
    }
});

/**
 * GET /api/insights/:developerId/advice
 * Generate personalized advice
 */
router.get('/:developerId/advice', async (req, res) => {
    try {
        const developerId = parseInt(req.params.developerId);
        
        const userInfo = await MLFeatureService.getUserInfo(developerId);
        const advice = await mlApiClient.generateAdvice(
            developerId,
            userInfo.display_name
        );
        
        res.json(advice);
        
    } catch (error) {
        console.error('Error generating advice:', error);
        res.status(500).json({ error: error.message });
    }
});

/**
 * GET /api/insights/:developerId/pace/:journeyId
 * Get pace analysis for specific journey
 */
router.get('/:developerId/pace/:journeyId', async (req, res) => {
    try {
        const developerId = parseInt(req.params.developerId);
        const journeyId = parseInt(req.params.journeyId);
        
        const pace = await mlApiClient.analyzePace(developerId, journeyId);
        
        res.json(pace);
        
    } catch (error) {
        console.error('Error analyzing pace:', error);
        res.status(500).json({ error: error.message });
    }
});

/**
 * POST /api/insights/features/calculate
 * Calculate features for developer (for testing/debugging)
 */
router.post('/features/calculate', async (req, res) => {
    try {
        const { developer_id } = req.body;
        
        if (!developer_id) {
            return res.status(400).json({ error: 'developer_id is required' });
        }
        
        const features = await MLFeatureService.calculateFeatures(developer_id);
        
        res.json({
            developer_id: developer_id,
            features: features
        });
        
    } catch (error) {
        console.error('Error calculating features:', error);
        res.status(500).json({ error: error.message });
    }
});

module.exports = router;
```

### server.js

```javascript
const express = require('express');
const cors = require('cors');
require('dotenv').config();

const insightsRoutes = require('./routes/insights');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(cors());
app.use(express.json());

// Routes
app.use('/api/insights', insightsRoutes);

// Root endpoint
app.get('/', (req, res) => {
    res.json({
        message: 'AI Learning Insight Backend API',
        version: '1.0.0',
        endpoints: {
            health: '/api/insights/health',
            dashboard: '/api/insights/:developerId/dashboard',
            persona: '/api/insights/:developerId/persona',
            advice: '/api/insights/:developerId/advice',
            pace: '/api/insights/:developerId/pace/:journeyId'
        }
    });
});

// Error handler
app.use((err, req, res, next) => {
    console.error(err.stack);
    res.status(500).json({ 
        error: 'Something went wrong!',
        message: err.message 
    });
});

// Start server
app.listen(PORT, () => {
    console.log(`✅ Backend server running on http://localhost:${PORT}`);
    console.log(`📝 API Documentation: http://localhost:${PORT}`);
});
```

---

## 5. Testing

### Test dengan cURL

```bash
# 1. Health check
curl http://localhost:3000/api/insights/health

# 2. Get dashboard (developer_id = 3390)
curl http://localhost:3000/api/insights/3390/dashboard

# 3. Get persona only
curl http://localhost:3000/api/insights/3390/persona

# 4. Get advice
curl http://localhost:3000/api/insights/3390/advice

# 5. Get pace for journey
curl http://localhost:3000/api/insights/3390/pace/45

# 6. Calculate features (testing)
curl -X POST http://localhost:3000/api/insights/features/calculate \
  -H "Content-Type: application/json" \
  -d '{"developer_id": 3390}'
```

### Test dengan Postman

Import collection:

```json
{
  "info": {
    "name": "AI Learning Insight Backend",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "item": [
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "url": "http://localhost:3000/api/insights/health"
      }
    },
    {
      "name": "Get Dashboard",
      "request": {
        "method": "GET",
        "url": "http://localhost:3000/api/insights/3390/dashboard"
      }
    }
  ]
}
```

---

## 📝 Checklist Integration

- [ ] Setup database connection (.env)
- [ ] Test database queries individual
- [ ] Test ML API health check
- [ ] Test feature calculation for 1 developer
- [ ] Test complete dashboard endpoint
- [ ] Test error handling
- [ ] Deploy ke staging/production

---

## 🚀 Deployment

```bash
# Production dengan PM2
npm install -g pm2
pm2 start server.js --name "insights-backend"
pm2 save
pm2 startup
```

---

**Ready to use! Tinggal jalankan saja!** 🎉
