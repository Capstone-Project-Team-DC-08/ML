"""
Test Script untuk Learning Pace API
Script ini untuk testing semua endpoint API

UPDATED: v2.0.0 (2025-12-14)
- Model 1 (Persona): TIDAK AKTIF
- Model 2 (Advice): OpenRouter (Mistral AI devstral-2512:free)
- Model 3 (Pace): Classification dengan 3 pace labels

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
            print_success(f"Timestamp: {data['timestamp']}")
            print_success(f"Model Loaded: {data['model_loaded']}")
            
            print_response(data, "Health Check Response")
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
            print_success(f"API Name: {data['name']}")
            print_success(f"Version: {data['version']}")
            print_success(f"Endpoints: {list(data['endpoints'].keys())}")
            print_response(data)
            return True
        else:
            print_error(f"Root endpoint returned status {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def test_pace_analysis():
    """Test pace analysis endpoint (Model 3 - Classification)"""
    print_header("Test 3: Learning Pace Analysis (Model 3)")
    
    try:
        # Payload dengan 5 fitur untuk Pace Classification
        payload = {
            "user_id": 123,
            "features": {
                "completion_speed": 0.3,
                "study_consistency_std": 25.0,
                "avg_study_hour": 14.0,
                "completed_modules": 50,
                "total_modules_viewed": 60
            }
        }
        
        print(f"Testing pace for user {payload['user_id']}")
        print(f"Features: completion_speed={payload['features']['completion_speed']}")
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/pace/analyze",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"User ID: {data['user_id']}")
            print_success(f"Pace Label: {data['pace_label']}")
            print_success(f"Confidence: {data['confidence']}")
            print_success(f"Insight: {data['insight']}")
            
            print_response(data, "Pace Analysis Response")
            return True
        else:
            print_error(f"Pace analysis failed with status {response.status_code}")
            print_response(response.json(), "Error Response")
            return False
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def test_pace_fast_learner():
    """Test pace dengan data yang seharusnya menghasilkan fast learner"""
    print_header("Test 4: Pace - Fast Learner Scenario")
    
    try:
        payload = {
            "user_id": 456,
            "features": {
                "completion_speed": 0.3,  # < 0.55 = fast
                "study_consistency_std": 15.0,
                "avg_study_hour": 10.0,
                "completed_modules": 80,
                "total_modules_viewed": 90
            }
        }
        
        print(f"Testing fast learner scenario (completion_speed=0.3)")
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/pace/analyze",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            expected = "fast learner"
            actual = data['pace_label'].lower()
            
            if expected in actual:
                print_success(f"Correct! Predicted: {data['pace_label']}")
            else:
                print_warning(f"Expected 'fast learner', got: {data['pace_label']}")
            
            print_success(f"Confidence: {data['confidence']}")
            print_response(data, "Fast Learner Scenario Response")
            return True
        else:
            print_error(f"Test failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def test_pace_reflective_learner():
    """Test pace dengan data yang seharusnya menghasilkan reflective learner"""
    print_header("Test 5: Pace - Reflective Learner Scenario")
    
    try:
        payload = {
            "user_id": 789,
            "features": {
                "completion_speed": 2.0,  # > 1.5 = reflective
                "study_consistency_std": 80.0,
                "avg_study_hour": 22.0,
                "completed_modules": 30,
                "total_modules_viewed": 50
            }
        }
        
        print(f"Testing reflective learner scenario (completion_speed=2.0)")
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/pace/analyze",
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            expected = "reflective learner"
            actual = data['pace_label'].lower()
            
            if expected in actual:
                print_success(f"Correct! Predicted: {data['pace_label']}")
            else:
                print_warning(f"Expected 'reflective learner', got: {data['pace_label']}")
            
            print_success(f"Confidence: {data['confidence']}")
            print_response(data, "Reflective Learner Scenario Response")
            return True
        else:
            print_error(f"Test failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def test_advice_generation():
    """Test advice generation endpoint (Model 2 - OpenRouter Mistral AI)"""
    print_header("Test 6: Advice Generation (Model 2 - OpenRouter)")
    
    try:
        # Payload lengkap untuk advice generation
        payload = {
            "user_id": 123,
            "name": "Budi Santoso",
            "pace_label": "fast learner",
            "avg_exam_score": 85.0,
            "completed_modules": 50,
            "total_modules_viewed": 60,
            "completion_speed": 0.4,
            "study_consistency_std": 1.5,
            "total_courses_enrolled": 5,
            "courses_completed": 3,
            "optimal_study_time": "Pagi"
        }
        
        print(f"Testing advice for: {payload['name']} (ID: {payload['user_id']})")
        print(f"Pace: {payload['pace_label']}, Score: {payload['avg_exam_score']}")
        print("Note: This may take 1-3 seconds if using OpenRouter AI...")
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/advice/generate",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Advice generated successfully!")
            print_success(f"User: {data['name']}")
            print_success(f"Pace Context: {data['pace_context']}")
            print_success(f"Advice length: {len(data['advice_text'])} characters")
            
            print(f"\n{Colors.YELLOW}Generated Advice:{Colors.END}")
            print(f"{Colors.GREEN}{data['advice_text']}{Colors.END}")
            
            print_response(data, "Advice Response")
            return True
        else:
            print_error(f"Advice generation failed with status {response.status_code}")
            print_response(response.json(), "Error Response")
            return False
            
    except requests.exceptions.Timeout:
        print_error("Request timeout. OpenRouter API might be slow.")
        print_warning("Check your OPENROUTER_API_KEY in .env file")
        return False
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def test_advice_low_score():
    """Test advice dengan skor rendah untuk lihat saran improvement"""
    print_header("Test 7: Advice - Low Score Scenario")
    
    try:
        payload = {
            "user_id": 456,
            "name": "Andi Wijaya",
            "pace_label": "consistent learner",
            "avg_exam_score": 55.0,
            "completed_modules": 20,
            "total_modules_viewed": 50,
            "completion_speed": 0.9,
            "study_consistency_std": 4.0,
            "total_courses_enrolled": 3,
            "courses_completed": 1,
            "optimal_study_time": "Malam"
        }
        
        print(f"Testing advice for low score scenario (score: {payload['avg_exam_score']})")
        
        response = requests.post(
            f"{API_BASE_URL}/api/v1/advice/generate",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Advice generated successfully!")
            print_success(f"User: {data['name']}")
            
            print(f"\n{Colors.YELLOW}Generated Advice:{Colors.END}")
            print(f"{Colors.GREEN}{data['advice_text']}{Colors.END}")
            
            return True
        else:
            print_error(f"Test failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print_error(f"Error: {str(e)}")
        return False


def test_swagger_docs():
    """Test if Swagger documentation is accessible"""
    print_header("Test 8: API Documentation")
    
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
    print("  Learning Pace API - Test Suite v2.0.0")
    print("  Model 2: OpenRouter (Mistral AI) + Model 3: Pace")
    print("="*60)
    print(f"{Colors.END}")
    print(f"Testing API at: {API_BASE_URL}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Health Check", test_health_check),
        ("Root Endpoint", test_root_endpoint),
        ("Pace Analysis", test_pace_analysis),
        ("Pace - Fast Learner", test_pace_fast_learner),
        ("Pace - Reflective Learner", test_pace_reflective_learner),
        ("Advice Generation (OpenRouter)", test_advice_generation),
        ("Advice - Low Score", test_advice_low_score),
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
    print("  Model 2: OpenRouter (Mistral AI devstral-2512:free)")
    print("  Model 3: Pace Classification")
    print("  Model 1: TIDAK AKTIF")
    print("="*60)
    print("\nMake sure the API server is running before testing!")
    print("To start server: cd src/api && python main.py\n")
    
    input("Press Enter to start tests...")
    
    # Run tests
    success = run_all_tests()
    
    # Exit code
    exit(0 if success else 1)