"""
Test Script untuk AI Learning Insight API
Script ini untuk testing semua endpoint API
Run: python test_api.py
"""

import requests
import json
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"

# Colors untuk terminal output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'


def print_header(text):
    """Print section header"""
    print(f"\n{Colors.BLUE}{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}{Colors.END}\n")


def print_success(text):
    """Print success message"""
    print(f"{Colors.GREEN}✓ {text}{Colors.END}")


def print_error(text):
    """Print error message"""
    print(f"{Colors.RED}✗ {text}{Colors.END}")


def print_warning(text):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.END}")


def print_response(response_data, title="Response"):
    """Pretty print JSON response"""
    print(f"\n{Colors.YELLOW}{title}:{Colors.END}")
    print(json.dumps(response_data, indent=2, ensure_ascii=False))


def test_health_check():
    """Test health check endpoint"""
    print_header("Test 1: Health Check")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"API Status: {data['status']}")
            print_success(f"Version: {data['version']}")
            
            # Check each model
            models_status = data['models_loaded']
            for model_name, status in models_status.items():
                if status:
                    print_success(f"{model_name}: Loaded")
                else:
                    print_warning(f"{model_name}: Not loaded")
            
            print_response(data, "Full Health Check Response")
            return True
        else:
            print_error(f"Health check failed with status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print_error("Cannot connect to API. Is the server running?")
        print_warning(f"Make sure API is running at {API_BASE_URL}")
        print_warning("Start with: cd src/api && python main.py")
        return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def test_root_endpoint():
    """Test root endpoint"""
    print_header("Test 2: Root Endpoint")
    
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print_success("Root endpoint accessible")
            print_response(data)
            return True
        else:
            print_error(f"Root endpoint returned status {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def test_persona_prediction():
    """Test persona prediction endpoint"""
    print_header("Test 3: Persona Prediction (Model 1)")
    
    try:
        # Test data dengan features lengkap
        payload = {
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
        
        print(f"Testing with user_id: {payload['user_id']}")
        print(f"Features: avg_study_hour={payload['features']['avg_study_hour']}, avg_exam_score={payload['features']['avg_exam_score']}")
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/persona/predict",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Persona: {data['persona_label']}")
            print_success(f"Cluster ID: {data['cluster_id']}")
            print_success(f"Confidence: {data['confidence']}")
            if 'description' in data:
                print_success(f"Description: {data['description']}")
            print_success(f"Characteristics: {len(data['characteristics'])} items")
            
            print_response(data, "Persona Prediction Response")
            return True
        else:
            print_error(f"Persona prediction failed with status {response.status_code}")
            print_response(response.json(), "Error Response")
            return False
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def test_batch_persona():
    """Test batch persona prediction"""
    print_header("Test 4: Batch Persona Prediction")
    
    try:
        payload = {
            "user_ids": [123, 456, 789]
        }
        
        print(f"Testing with {len(payload['user_ids'])} users")
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/persona/batch",
            json=payload,
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Processed {data['total_processed']} users")
            
            for result in data['results']:
                print_success(f"  User {result['user_id']}: {result['persona_label']}")
            
            print_response(data, "Batch Persona Response")
            return True
        else:
            print_error(f"Batch persona failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def test_advice_generation():
    """Test advice generation endpoint"""
    print_header("Test 5: Personalized Advice Generation (Model 2)")
    
    try:
        # Updated payload dengan persona dan pace label
        payload = {
            "user_id": 123,
            "name": "Budi Santoso",
            "persona_label": "The Night Owl",
            "pace_label": "fast learner",
            "avg_exam_score": 78.5,
            "course_name": "Belajar Machine Learning"
        }
        
        print(f"Testing advice for: {payload['name']} (ID: {payload['user_id']})")
        print(f"Persona: {payload['persona_label']}, Pace: {payload['pace_label']}")
        print("Note: This may take 1-3 seconds if using Gemini AI...")
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/advice/generate",
            json=payload,
            timeout=30  # Longer timeout untuk Gemini API
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Advice generated successfully")
            print_success(f"Advice length: {len(data['advice_text'])} characters")
            print_success(f"Persona context: {data['persona_context']}")
            print_success(f"Pace context: {data['pace_context']}")
            
            print(f"\n{Colors.YELLOW}Generated Advice:{Colors.END}")
            print(f"{Colors.GREEN}{data['advice_text']}{Colors.END}")
            
            print_response(data, "Full Advice Response")
            return True
        else:
            print_error(f"Advice generation failed with status {response.status_code}")
            print_response(response.json(), "Error Response")
            return False
            
    except requests.exceptions.Timeout:
        print_error("Request timeout. Gemini API might be slow or unavailable.")
        print_warning("Check your GEMINI_API_KEY in .env file")
        return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def test_pace_analysis():
    """Test pace analysis endpoint"""
    print_header("Test 6: Learning Pace Analysis (Model 3)")
    
    try:
        # Updated payload dengan features
        payload = {
            "user_id": 123,
            "journey_id": 45,
            "features": {
                "materials_per_day": 6.5,
                "weekly_cv": 0.3,
                "completion_speed": 0.8
            }
        }
        
        print(f"Testing pace for user {payload['user_id']} on journey {payload['journey_id']}")
        print(f"Features: materials_per_day={payload['features']['materials_per_day']}")
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/pace/analyze",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Journey ID: {data.get('journey_id', 'N/A')}")
            print_success(f"Journey Name: {data.get('journey_name', 'N/A')}")
            print_success(f"Pace Label: {data['pace_label']}")
            if 'scores' in data and data['scores']:
                print_success(f"Scores: fast={data['scores'].get('fast_score', 'N/A')}, consistent={data['scores'].get('consistent_score', 'N/A')}")
            if data.get('pace_percentage') is not None:
                print_success(f"Pace Percentage: {data['pace_percentage']}%")
            if data.get('user_duration_hours') is not None:
                print_success(f"User Duration: {data['user_duration_hours']} hours")
            if data.get('avg_duration_hours') is not None:
                print_success(f"Avg Duration: {data['avg_duration_hours']} hours")
            if data.get('percentile_rank') is not None:
                print_success(f"Percentile Rank: {data['percentile_rank']}")
            if 'insight' in data:
                # Handle emoji for Windows
                insight = data['insight'].encode('ascii', 'ignore').decode('ascii').strip()
                print_success(f"Insight: {insight}")
            
            print_response(data, "Pace Analysis Response")
            return True
        else:
            print_error(f"Pace analysis failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def test_pace_summary():
    """Test pace summary endpoint"""
    print_header("Test 7: Pace Summary")
    
    try:
        user_id = 123
        
        response = requests.get(
            f"{API_BASE_URL}/api/v1/pace/{user_id}/summary",
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Total Courses: {data['total_courses_completed']}")
            print_success(f"Dominant Pace: {data.get('dominant_pace_label', 'N/A')}")
            if 'pace_distribution' in data:
                print_success(f"Pace Distribution: {data['pace_distribution']}")
            if 'insight' in data:
                print_success(f"Insight: {data['insight']}")
            
            print_response(data, "Pace Summary Response")
            return True
        else:
            print_error(f"Pace summary failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def test_complete_insights():
    """Test complete insights endpoint (all models combined)"""
    print_header("Test 8: Complete Insights (All Models)")
    
    try:
        user_id = 123
        user_name = "Budi"
        
        print(f"Getting complete insights for: {user_name} (ID: {user_id})")
        print("This combines all 3 models, may take a few seconds...")
        
        response = requests.get(
            f"{API_BASE_URL}/api/v1/insights/{user_id}",
            params={"user_name": user_name},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Complete insights retrieved")
            print_success(f"Persona: {data['persona']['label']}")
            print_success(f"Pace: {data['learning_pace']['label']}")
            print_success(f"Advice generated: {len(data['personalized_advice']['text'])} chars")
            
            print_response(data, "Complete Insights Response")
            return True
        else:
            print_error(f"Complete insights failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def test_swagger_docs():
    """Test if Swagger documentation is accessible"""
    print_header("Test 9: API Documentation")
    
    try:
        response = requests.get(f"{API_BASE_URL}/docs", timeout=5)
        
        if response.status_code == 200:
            print_success("Swagger UI is accessible")
            print_success(f"URL: {API_BASE_URL}/docs")
            return True
        else:
            print_error("Swagger UI not accessible")
            return False
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def run_all_tests():
    """Run all tests"""
    print(f"\n{Colors.BLUE}")
    print("="*60)
    print("  AI Learning Insight API - Test Suite")
    print("="*60)
    print(f"{Colors.END}")
    print(f"Testing API at: {API_BASE_URL}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Health Check", test_health_check),
        ("Root Endpoint", test_root_endpoint),
        ("Persona Prediction", test_persona_prediction),
        ("Batch Persona", test_batch_persona),
        ("Advice Generation", test_advice_generation),
        ("Pace Analysis", test_pace_analysis),
        ("Pace Summary", test_pace_summary),
        ("Complete Insights", test_complete_insights),
        ("API Documentation", test_swagger_docs),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"Test crashed: {str(e)}")
            results.append((test_name, False))
    
    # Summary
    print_header("Test Summary")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        if result:
            print_success(f"{test_name}")
        else:
            print_error(f"{test_name}")
    
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    
    if passed == total:
        print(f"{Colors.GREEN}✓ All tests passed! ({passed}/{total}){Colors.END}")
    else:
        print(f"{Colors.YELLOW}⚠ {passed}/{total} tests passed{Colors.END}")
    
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")
    
    return passed == total


if __name__ == "__main__":
    # Intro
    print("\n" + "="*60)
    print("  Starting API Tests...")
    print("="*60)
    print("\nMake sure the API server is running before testing!")
    print("To start server: cd src/api && python main.py\n")
    
    input("Press Enter to start tests...")
    
    # Run tests
    success = run_all_tests()
    
    # Exit code
    exit(0 if success else 1)
