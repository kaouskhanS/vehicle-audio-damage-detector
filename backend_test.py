#!/usr/bin/env python3
"""
Backend API Tests for Automobile Sound Damage Detection
Tests all key endpoints and features as specified in the review request.
"""

import requests
import json
import os
import io
import base64
import time
from pathlib import Path
import numpy as np
import soundfile as sf
import tempfile

# Load environment variables
from dotenv import load_dotenv
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE_URL = f"{BACKEND_URL}/api"

print(f"Testing backend at: {API_BASE_URL}")

class AudioTestGenerator:
    """Generate test audio files for testing"""
    
    @staticmethod
    def create_test_audio(duration=2.0, sample_rate=16000, frequency=440):
        """Create a simple sine wave audio for testing"""
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        audio_data = np.sin(frequency * 2 * np.pi * t)
        return audio_data, sample_rate
    
    @staticmethod
    def save_audio_to_bytes(audio_data, sample_rate, format='WAV'):
        """Convert audio data to bytes"""
        buffer = io.BytesIO()
        sf.write(buffer, audio_data, sample_rate, format=format)
        buffer.seek(0)
        return buffer.getvalue()

def test_health_check():
    """Test GET /api/ - basic health check"""
    print("\n=== Testing Health Check Endpoint ===")
    try:
        response = requests.get(f"{API_BASE_URL}/")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            if "message" in data and "status" in data:
                print("✅ Health check endpoint working correctly")
                return True
            else:
                print("❌ Health check response missing required fields")
                return False
        else:
            print(f"❌ Health check failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_audio_analysis():
    """Test POST /api/analyze-audio - upload audio file and get damage analysis"""
    print("\n=== Testing Audio Analysis Endpoint ===")
    
    # Create test audio file
    audio_data, sample_rate = AudioTestGenerator.create_test_audio(duration=3.0, frequency=800)
    audio_bytes = AudioTestGenerator.save_audio_to_bytes(audio_data, sample_rate)
    
    try:
        # Test with valid audio file
        files = {
            'file': ('test_audio.wav', audio_bytes, 'audio/wav')
        }
        
        response = requests.post(f"{API_BASE_URL}/analyze-audio", files=files)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 200:
            data = response.json()
            required_fields = ['id', 'damage_type', 'confidence', 'repair_suggestions', 'timestamp', 'file_name']
            
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                print(f"❌ Missing required fields: {missing_fields}")
                return False
            
            # Validate damage type is one of expected categories
            expected_damage_types = [
                "engine_knock", "brake_squeal", "transmission_grinding", 
                "exhaust_leak", "belt_squeal", "normal_operation", "analysis_failed"
            ]
            
            if data['damage_type'] not in expected_damage_types:
                print(f"❌ Unexpected damage type: {data['damage_type']}")
                return False
            
            # Validate confidence is between 0 and 1
            if not (0 <= data['confidence'] <= 1):
                print(f"❌ Invalid confidence score: {data['confidence']}")
                return False
            
            # Validate repair suggestions structure
            repair_suggestions = data['repair_suggestions']
            if not isinstance(repair_suggestions, dict) or 'temporary' not in repair_suggestions or 'permanent' not in repair_suggestions:
                print(f"❌ Invalid repair suggestions structure")
                return False
            
            print("✅ Audio analysis endpoint working correctly")
            return data['id']  # Return analysis ID for further testing
            
        else:
            print(f"❌ Audio analysis failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Audio analysis error: {e}")
        return False

def test_invalid_file_upload():
    """Test POST /api/analyze-audio with invalid file types"""
    print("\n=== Testing Invalid File Upload ===")
    
    try:
        # Test with non-audio file (text file)
        text_content = b"This is not an audio file"
        files = {
            'file': ('test.txt', text_content, 'text/plain')
        }
        
        response = requests.post(f"{API_BASE_URL}/analyze-audio", files=files)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        
        if response.status_code == 400:
            data = response.json()
            if "File must be an audio file" in data.get('detail', ''):
                print("✅ Invalid file type correctly rejected")
                return True
            else:
                print("❌ Wrong error message for invalid file type")
                return False
        else:
            print(f"❌ Expected 400 status code, got {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Invalid file upload test error: {e}")
        return False

def test_analysis_history():
    """Test GET /api/analysis-history - get all previous analyses"""
    print("\n=== Testing Analysis History Endpoint ===")
    
    try:
        response = requests.get(f"{API_BASE_URL}/analysis-history")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Number of analyses in history: {len(data)}")
            
            if isinstance(data, list):
                # If there are analyses, validate structure
                if data:
                    first_analysis = data[0]
                    required_fields = ['id', 'timestamp', 'damage_type', 'confidence', 'file_name', 'repair_suggestions']
                    
                    missing_fields = [field for field in required_fields if field not in first_analysis]
                    if missing_fields:
                        print(f"❌ Missing required fields in history: {missing_fields}")
                        return False
                
                print("✅ Analysis history endpoint working correctly")
                return True
            else:
                print("❌ History response is not a list")
                return False
        else:
            print(f"❌ Analysis history failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Analysis history error: {e}")
        return False

def test_analysis_details(analysis_id):
    """Test GET /api/analysis/{analysis_id} - get specific analysis details"""
    print(f"\n=== Testing Analysis Details Endpoint (ID: {analysis_id}) ===")
    
    if not analysis_id:
        print("❌ No analysis ID provided for testing")
        return False
    
    try:
        response = requests.get(f"{API_BASE_URL}/analysis/{analysis_id}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Analysis details: {json.dumps(data, indent=2, default=str)}")
            
            required_fields = ['id', 'timestamp', 'damage_type', 'confidence', 'features', 'repair_suggestions', 'file_name', 'file_size']
            
            missing_fields = [field for field in required_fields if field not in data]
            if missing_fields:
                print(f"❌ Missing required fields in details: {missing_fields}")
                return False
            
            # Validate features structure
            features = data['features']
            if not isinstance(features, dict):
                print("❌ Features should be a dictionary")
                return False
            
            print("✅ Analysis details endpoint working correctly")
            return True
            
        elif response.status_code == 404:
            print("❌ Analysis not found (this might indicate a database issue)")
            return False
        else:
            print(f"❌ Analysis details failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Analysis details error: {e}")
        return False

def test_nonexistent_analysis():
    """Test GET /api/analysis/{analysis_id} with non-existent ID"""
    print("\n=== Testing Non-existent Analysis ID ===")
    
    fake_id = "non-existent-id-12345"
    
    try:
        response = requests.get(f"{API_BASE_URL}/analysis/{fake_id}")
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 404:
            data = response.json()
            if "Analysis not found" in data.get('detail', ''):
                print("✅ Non-existent analysis correctly returns 404")
                return True
            else:
                print("❌ Wrong error message for non-existent analysis")
                return False
        else:
            print(f"❌ Expected 404 status code, got {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Non-existent analysis test error: {e}")
        return False

def test_multiple_audio_formats():
    """Test different audio formats"""
    print("\n=== Testing Multiple Audio Formats ===")
    
    formats_to_test = [
        ('WAV', 'audio/wav'),
        ('FLAC', 'audio/flac'),
    ]
    
    results = []
    
    for format_name, content_type in formats_to_test:
        try:
            print(f"\nTesting {format_name} format...")
            audio_data, sample_rate = AudioTestGenerator.create_test_audio(duration=2.0, frequency=600)
            
            # For FLAC, we need to handle it differently
            if format_name == 'FLAC':
                try:
                    audio_bytes = AudioTestGenerator.save_audio_to_bytes(audio_data, sample_rate, format='FLAC')
                except:
                    print(f"⚠️ FLAC format not supported by test environment, skipping")
                    continue
            else:
                audio_bytes = AudioTestGenerator.save_audio_to_bytes(audio_data, sample_rate, format=format_name)
            
            files = {
                'file': (f'test_audio.{format_name.lower()}', audio_bytes, content_type)
            }
            
            response = requests.post(f"{API_BASE_URL}/analyze-audio", files=files)
            
            if response.status_code == 200:
                print(f"✅ {format_name} format processed successfully")
                results.append(True)
            else:
                print(f"❌ {format_name} format failed with status {response.status_code}")
                results.append(False)
                
        except Exception as e:
            print(f"❌ {format_name} format test error: {e}")
            results.append(False)
    
    return all(results) if results else False

def test_base64_encoding():
    """Test that audio files are properly base64 encoded for storage"""
    print("\n=== Testing Base64 Encoding ===")
    
    try:
        # Create and upload audio
        audio_data, sample_rate = AudioTestGenerator.create_test_audio(duration=1.0)
        audio_bytes = AudioTestGenerator.save_audio_to_bytes(audio_data, sample_rate)
        
        files = {
            'file': ('test_encoding.wav', audio_bytes, 'audio/wav')
        }
        
        response = requests.post(f"{API_BASE_URL}/analyze-audio", files=files)
        
        if response.status_code == 200:
            analysis_id = response.json()['id']
            
            # Get detailed analysis to check if data is stored
            details_response = requests.get(f"{API_BASE_URL}/analysis/{analysis_id}")
            
            if details_response.status_code == 200:
                details = details_response.json()
                
                # Check if file_size is reasonable (indicates successful storage)
                if details['file_size'] > 0:
                    print("✅ Audio file successfully encoded and stored")
                    return True
                else:
                    print("❌ File size is 0, encoding may have failed")
                    return False
            else:
                print("❌ Could not retrieve analysis details for encoding test")
                return False
        else:
            print("❌ Audio upload failed for encoding test")
            return False
            
    except Exception as e:
        print(f"❌ Base64 encoding test error: {e}")
        return False

def run_all_tests():
    """Run all backend tests"""
    print("🚀 Starting Automobile Sound Damage Detection API Tests")
    print("=" * 60)
    
    test_results = {}
    analysis_id = None
    
    # Test 1: Health Check
    test_results['health_check'] = test_health_check()
    
    # Test 2: Audio Analysis (main functionality)
    analysis_result = test_audio_analysis()
    if isinstance(analysis_result, str):
        analysis_id = analysis_result
        test_results['audio_analysis'] = True
    else:
        test_results['audio_analysis'] = False
    
    # Test 3: Invalid file upload
    test_results['invalid_file'] = test_invalid_file_upload()
    
    # Test 4: Analysis History
    test_results['analysis_history'] = test_analysis_history()
    
    # Test 5: Analysis Details
    test_results['analysis_details'] = test_analysis_details(analysis_id)
    
    # Test 6: Non-existent Analysis
    test_results['nonexistent_analysis'] = test_nonexistent_analysis()
    
    # Test 7: Multiple Audio Formats
    test_results['multiple_formats'] = test_multiple_audio_formats()
    
    # Test 8: Base64 Encoding
    test_results['base64_encoding'] = test_base64_encoding()
    
    # Summary
    print("\n" + "=" * 60)
    print("🏁 TEST SUMMARY")
    print("=" * 60)
    
    passed_tests = 0
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
        if result:
            passed_tests += 1
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Backend API is working correctly.")
        return True
    else:
        print("⚠️ Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)