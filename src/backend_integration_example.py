"""
Contoh Integrasi API untuk Tim Backend
File ini berisi template dan contoh code untuk integrasi ML API dengan backend
"""

import requests
from typing import Dict, List, Optional
import json


class MLAPIClient:
    """
    Client class untuk memanggil ML API
    Gunakan class ini di backend code Anda
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize ML API Client
        
        Args:
            base_url: Base URL dari ML API (default: http://localhost:8000)
        """
        self.base_url = base_url
        self.timeout = 30  # seconds
        
    def _make_request(self, method: str, endpoint: str, **kwargs):
        """Internal method untuk make HTTP request"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = requests.request(
                method=method,
                url=url,
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.ConnectionError:
            raise Exception(f"Cannot connect to ML API at {self.base_url}. Is the server running?")
        except requests.exceptions.Timeout:
            raise Exception(f"Request to ML API timed out after {self.timeout} seconds")
        except requests.exceptions.HTTPError as e:
            raise Exception(f"ML API returned error: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            raise Exception(f"Unexpected error calling ML API: {str(e)}")
    
    def health_check(self) -> Dict:
        """
        Check health status dari ML API
        
        Returns:
            Dict dengan status dan model loading info
        """
        return self._make_request("GET", "/health")
    
    def get_persona(self, user_id: int) -> Dict:
        """
        Get persona/cluster untuk user
        
        Args:
            user_id: ID user dari database
            
        Returns:
            Dict dengan persona_label, cluster_id, confidence, characteristics
        """
        return self._make_request(
            "POST",
            "/api/v1/persona/predict",
            json={"user_id": user_id}
        )
    
    def get_batch_persona(self, user_ids: List[int]) -> Dict:
        """
        Get persona untuk multiple users sekaligus
        
        Args:
            user_ids: List of user IDs (max 100)
            
        Returns:
            Dict dengan list of results dan total_processed
        """
        if len(user_ids) > 100:
            raise ValueError("Maximum 100 users per batch request")
            
        return self._make_request(
            "POST",
            "/api/v1/persona/batch",
            json={"user_ids": user_ids}
        )
    
    def generate_advice(self, user_id: int, name: str) -> Dict:
        """
        Generate personalized advice untuk user
        
        Args:
            user_id: ID user dari database
            name: Nama user untuk personalisasi
            
        Returns:
            Dict dengan advice_text, persona_context, pace_context, dll
        """
        return self._make_request(
            "POST",
            "/api/v1/advice/generate",
            json={"user_id": user_id, "name": name}
        )
    
    def analyze_pace(self, user_id: int, journey_id: int) -> Dict:
        """
        Analyze learning pace untuk user pada specific journey
        
        Args:
            user_id: ID user dari database
            journey_id: ID journey/course
            
        Returns:
            Dict dengan pace_label, pace_percentage, duration info, dll
        """
        return self._make_request(
            "POST",
            "/api/v1/pace/analyze",
            json={"user_id": user_id, "journey_id": journey_id}
        )
    
    def get_pace_summary(self, user_id: int) -> Dict:
        """
        Get overall pace summary untuk user
        
        Args:
            user_id: ID user dari database
            
        Returns:
            Dict dengan summary statistik
        """
        return self._make_request(
            "GET",
            f"/api/v1/pace/{user_id}/summary"
        )
    
    def get_complete_insights(self, user_id: int, user_name: str) -> Dict:
        """
        Get complete insights dari semua 3 model sekaligus
        
        Args:
            user_id: ID user dari database
            user_name: Nama user
            
        Returns:
            Dict dengan persona, learning_pace, dan personalized_advice
        """
        return self._make_request(
            "GET",
            f"/api/v1/insights/{user_id}",
            params={"user_name": user_name}
        )


# ============================================================
# CONTOH PENGGUNAAN
# ============================================================

def example_usage():
    """Contoh penggunaan ML API Client"""
    
    # Initialize client
    ml_api = MLAPIClient(base_url="http://localhost:8000")
    
    # 1. Check health
    print("=" * 60)
    print("1. Checking API Health...")
    print("=" * 60)
    health = ml_api.health_check()
    print(json.dumps(health, indent=2))
    
    # 2. Get persona untuk single user
    print("\n" + "=" * 60)
    print("2. Getting Persona for User 123...")
    print("=" * 60)
    persona = ml_api.get_persona(user_id=123)
    print(json.dumps(persona, indent=2, ensure_ascii=False))
    
    # 3. Get batch persona
    print("\n" + "=" * 60)
    print("3. Getting Persona for Multiple Users...")
    print("=" * 60)
    batch_persona = ml_api.get_batch_persona(user_ids=[123, 456, 789])
    print(json.dumps(batch_persona, indent=2, ensure_ascii=False))
    
    # 4. Generate advice
    print("\n" + "=" * 60)
    print("4. Generating Personalized Advice...")
    print("=" * 60)
    advice = ml_api.generate_advice(user_id=123, name="Budi")
    print(f"Advice: {advice['advice_text']}")
    
    # 5. Analyze pace
    print("\n" + "=" * 60)
    print("5. Analyzing Learning Pace...")
    print("=" * 60)
    pace = ml_api.analyze_pace(user_id=123, journey_id=45)
    print(json.dumps(pace, indent=2, ensure_ascii=False))
    
    # 6. Get complete insights
    print("\n" + "=" * 60)
    print("6. Getting Complete Insights...")
    print("=" * 60)
    insights = ml_api.get_complete_insights(user_id=123, user_name="Budi")
    print(json.dumps(insights, indent=2, ensure_ascii=False))


# ============================================================
# CONTOH INTEGRASI DENGAN FLASK BACKEND
# ============================================================

"""
# Contoh implementasi di Flask backend

from flask import Flask, jsonify, request
from ml_api_client import MLAPIClient

app = Flask(__name__)
ml_api = MLAPIClient()

@app.route('/api/student/<int:user_id>/dashboard')
def get_student_dashboard(user_id):
    '''
    Endpoint backend yang dipanggil frontend
    Mengembalikan complete dashboard data
    '''
    try:
        # Get user dari database
        user = db.get_user(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get insights dari ML API
        insights = ml_api.get_complete_insights(user_id, user['name'])
        
        # Combine dengan data lain dari database
        dashboard_data = {
            'user': {
                'id': user_id,
                'name': user['name'],
                'email': user['email']
            },
            'insights': insights,
            'recent_courses': db.get_recent_courses(user_id),
            'achievements': db.get_achievements(user_id)
        }
        
        return jsonify(dashboard_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/courses/<int:journey_id>/students')
def get_course_students_with_labels(journey_id):
    '''
    Endpoint untuk instructor/admin
    Menampilkan semua student dengan pace label
    '''
    try:
        # Get students dari database
        students = db.get_course_students(journey_id)
        
        # Add ML insights untuk setiap student
        for student in students:
            try:
                # Get persona
                persona = ml_api.get_persona(student['id'])
                student['persona_label'] = persona['persona_label']
                
                # Get pace
                pace = ml_api.analyze_pace(student['id'], journey_id)
                student['pace_label'] = pace['pace_label']
                student['pace_percentage'] = pace['pace_percentage']
                
            except Exception as e:
                # Jika ML API gagal untuk satu student, continue
                print(f"Error getting ML data for student {student['id']}: {e}")
                student['persona_label'] = 'Unknown'
                student['pace_label'] = 'Unknown'
        
        return jsonify({
            'journey_id': journey_id,
            'students': students
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/student/<int:user_id>/refresh-insights', methods=['POST'])
def refresh_student_insights(user_id):
    '''
    Endpoint untuk refresh/regenerate insights
    Misalnya dipanggil setelah user menyelesaikan course baru
    '''
    try:
        user = db.get_user(user_id)
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        # Get fresh insights
        insights = ml_api.get_complete_insights(user_id, user['name'])
        
        # Optional: Save to database untuk caching
        db.save_user_insights(user_id, insights)
        
        return jsonify({
            'message': 'Insights refreshed successfully',
            'insights': insights
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

"""


# ============================================================
# CONTOH INTEGRASI DENGAN EXPRESS.JS BACKEND (Node.js)
# ============================================================

"""
// ml-api-client.js
const axios = require('axios');

class MLAPIClient {
    constructor(baseUrl = 'http://localhost:8000') {
        this.baseUrl = baseUrl;
        this.timeout = 30000; // 30 seconds
    }
    
    async healthCheck() {
        const response = await axios.get(`${this.baseUrl}/health`, {
            timeout: this.timeout
        });
        return response.data;
    }
    
    async getPersona(userId) {
        const response = await axios.post(
            `${this.baseUrl}/api/v1/persona/predict`,
            { user_id: userId },
            { timeout: this.timeout }
        );
        return response.data;
    }
    
    async generateAdvice(userId, name) {
        const response = await axios.post(
            `${this.baseUrl}/api/v1/advice/generate`,
            { user_id: userId, name: name },
            { timeout: this.timeout }
        );
        return response.data;
    }
    
    async analyzePace(userId, journeyId) {
        const response = await axios.post(
            `${this.baseUrl}/api/v1/pace/analyze`,
            { user_id: userId, journey_id: journeyId },
            { timeout: this.timeout }
        );
        return response.data;
    }
    
    async getCompleteInsights(userId, userName) {
        const response = await axios.get(
            `${this.baseUrl}/api/v1/insights/${userId}`,
            {
                params: { user_name: userName },
                timeout: this.timeout
            }
        );
        return response.data;
    }
}

module.exports = MLAPIClient;

// ========================================
// routes/student.js
const express = require('express');
const router = express.Router();
const MLAPIClient = require('../ml-api-client');

const mlApi = new MLAPIClient();

router.get('/student/:userId/dashboard', async (req, res) => {
    try {
        const userId = parseInt(req.params.userId);
        
        // Get user from database
        const user = await db.getUser(userId);
        if (!user) {
            return res.status(404).json({ error: 'User not found' });
        }
        
        // Get insights from ML API
        const insights = await mlApi.getCompleteInsights(userId, user.name);
        
        // Combine with other data
        const dashboardData = {
            user: {
                id: userId,
                name: user.name,
                email: user.email
            },
            insights: insights,
            recentCourses: await db.getRecentCourses(userId),
            achievements: await db.getAchievements(userId)
        };
        
        res.json(dashboardData);
        
    } catch (error) {
        console.error('Error:', error);
        res.status(500).json({ error: error.message });
    }
});

module.exports = router;
"""


# ============================================================
# HELPER FUNCTIONS UNTUK DATABASE QUERY
# (Untuk tim backend - adjust sesuai database schema Anda)
# ============================================================

"""
import mysql.connector
from datetime import datetime
import numpy as np

def calculate_user_features(db_connection, user_id):
    '''
    Calculate semua features yang dibutuhkan untuk ML model
    
    Args:
        db_connection: Database connection object
        user_id: ID user
        
    Returns:
        Dict dengan semua features
    '''
    cursor = db_connection.cursor(dictionary=True)
    
    # 1. Average study hour
    cursor.execute('''
        SELECT AVG(HOUR(last_viewed)) as avg_hour
        FROM developer_journey_trackings
        WHERE developer_id = %s
    ''', (user_id,))
    result = cursor.fetchone()
    avg_study_hour = float(result['avg_hour'] or 12)
    
    # 2. Study consistency (std deviation of days between sessions)
    cursor.execute('''
        SELECT last_viewed 
        FROM developer_journey_trackings
        WHERE developer_id = %s
        ORDER BY last_viewed
    ''', (user_id,))
    sessions = cursor.fetchall()
    
    if len(sessions) > 1:
        days = [(sessions[i]['last_viewed'] - sessions[i-1]['last_viewed']).days 
                for i in range(1, len(sessions))]
        study_consistency_std = float(np.std(days)) if days else 0
    else:
        study_consistency_std = 0
    
    # 3. Completion speed
    cursor.execute('''
        SELECT AVG(study_duration) as avg_duration
        FROM developer_journey_completions
        WHERE developer_id = %s AND status = 'completed'
    ''', (user_id,))
    result = cursor.fetchone()
    completion_speed = float(result['avg_duration'] or 40)
    
    # 4. Average exam score
    cursor.execute('''
        SELECT AVG(score) as avg_score
        FROM exam_results
        WHERE developer_id = %s
    ''', (user_id,))
    result = cursor.fetchone()
    avg_exam_score = float(result['avg_score'] or 70)
    
    # 5. Submission fail rate
    cursor.execute('''
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
        FROM developer_journey_submissions
        WHERE developer_id = %s
    ''', (user_id,))
    result = cursor.fetchone()
    submission_fail_rate = (result['failed'] / result['total']) if result['total'] > 0 else 0
    
    # 6. Retry count
    cursor.execute('''
        SELECT SUM(enrolling_times - 1) as retries
        FROM developer_journey_completions
        WHERE developer_id = %s
    ''', (user_id,))
    result = cursor.fetchone()
    retry_count = int(result['retries'] or 0)
    
    cursor.close()
    
    return {
        'avg_study_hour': avg_study_hour,
        'study_consistency_std': study_consistency_std,
        'completion_speed': completion_speed,
        'avg_exam_score': avg_exam_score,
        'submission_fail_rate': float(submission_fail_rate),
        'retry_count': retry_count
    }


def get_journey_statistics(db_connection, journey_id):
    '''
    Get statistik untuk journey/course tertentu
    
    Args:
        db_connection: Database connection
        journey_id: ID journey
        
    Returns:
        Dict dengan journey stats
    '''
    cursor = db_connection.cursor(dictionary=True)
    
    # Get journey info
    cursor.execute('''
        SELECT id, title, hours_to_study
        FROM developer_journeys
        WHERE id = %s
    ''', (journey_id,))
    journey = cursor.fetchone()
    
    # Get average duration from all users
    cursor.execute('''
        SELECT AVG(study_duration) as avg_duration
        FROM developer_journey_completions
        WHERE journey_id = %s AND status = 'completed'
    ''', (journey_id,))
    result = cursor.fetchone()
    
    cursor.close()
    
    return {
        'journey_id': journey_id,
        'journey_name': journey['title'],
        'avg_duration': float(result['avg_duration'] or journey['hours_to_study']),
        'expected_duration': float(journey['hours_to_study'])
    }


def get_user_journey_duration(db_connection, user_id, journey_id):
    '''
    Get durasi user untuk specific journey
    
    Args:
        db_connection: Database connection
        user_id: ID user
        journey_id: ID journey
        
    Returns:
        Float durasi dalam jam
    '''
    cursor = db_connection.cursor(dictionary=True)
    
    cursor.execute('''
        SELECT study_duration
        FROM developer_journey_completions
        WHERE developer_id = %s AND journey_id = %s
        ORDER BY updated_at DESC
        LIMIT 1
    ''', (user_id, journey_id))
    
    result = cursor.fetchone()
    cursor.close()
    
    return float(result['study_duration']) if result else 0
"""


if __name__ == "__main__":
    print("=" * 60)
    print("ML API Client - Contoh Penggunaan")
    print("=" * 60)
    print("\nPastikan ML API sudah running di http://localhost:8000")
    print("Start dengan: cd src/api && python main.py\n")
    
    input("Press Enter untuk run contoh...")
    
    try:
        example_usage()
        print("\n" + "=" * 60)
        print("✓ Semua contoh berhasil dijalankan!")
        print("=" * 60)
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        print("\nTips:")
        print("- Pastikan ML API sedang running")
        print("- Check URL: http://localhost:8000/health")
