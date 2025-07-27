from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
import uuid
from datetime import datetime
import json
import base64
import io
import librosa
import numpy as np
import torch
from transformers import AutoFeatureExtractor, AutoModelForAudioClassification, Wav2Vec2Processor, Wav2Vec2ForSequenceClassification
from pydub import AudioSegment
import tempfile
import soundfile as sf

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Initialize audio analysis model
class AudioAnalyzer:
    def __init__(self):
        self.model_name = "facebook/wav2vec2-base-960h"
        self.processor = None
        self.model = None
        self.feature_extractor = None
        self.load_model()
    
    def load_model(self):
        try:
            # Using a simpler approach for demo - we'll create a mock classifier
            self.processor = Wav2Vec2Processor.from_pretrained(self.model_name)
            # For demo, we'll use a simple classification approach
            self.damage_categories = [
                "engine_knock", "brake_squeal", "transmission_grinding", 
                "exhaust_leak", "belt_squeal", "normal_operation"
            ]
        except Exception as e:
            logging.error(f"Model loading error: {e}")
            self.processor = None
    
    def analyze_audio(self, audio_data: bytes) -> Dict[str, Any]:
        """Analyze automobile sound for damage detection"""
        try:
            # Convert bytes to audio array
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                tmp_file.write(audio_data)
                tmp_file_path = tmp_file.name
            
            # Load audio with librosa
            y, sr = librosa.load(tmp_file_path, sr=16000)
            
            # Extract audio features for analysis
            features = self.extract_features(y, sr)
            
            # Mock damage classification (in real app, this would use trained model)
            damage_type, confidence = self.classify_damage(features)
            
            # Generate repair suggestions
            repair_suggestions = self.get_repair_suggestions(damage_type)
            
            # Clean up temp file
            os.unlink(tmp_file_path)
            
            return {
                "damage_type": damage_type,
                "confidence": confidence,
                "features": features,
                "repair_suggestions": repair_suggestions
            }
        except Exception as e:
            logging.error(f"Audio analysis error: {e}")
            return {
                "damage_type": "analysis_failed",
                "confidence": 0.0,
                "features": {},
                "repair_suggestions": {"temporary": [], "permanent": []}
            }
    
    def extract_features(self, audio, sr):
        """Extract relevant audio features"""
        try:
            # Extract various audio features
            mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=13)
            spectral_centroid = librosa.feature.spectral_centroid(y=audio, sr=sr)
            spectral_rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr)
            zero_crossing_rate = librosa.feature.zero_crossing_rate(audio)
            
            # Compute statistics
            features = {
                "mfcc_mean": np.mean(mfccs, axis=1).tolist(),
                "mfcc_std": np.std(mfccs, axis=1).tolist(),
                "spectral_centroid_mean": float(np.mean(spectral_centroid)),
                "spectral_rolloff_mean": float(np.mean(spectral_rolloff)),
                "zero_crossing_rate_mean": float(np.mean(zero_crossing_rate)),
                "duration": len(audio) / sr,
                "sample_rate": sr
            }
            
            return features
        except Exception as e:
            logging.error(f"Feature extraction error: {e}")
            return {}
    
    def classify_damage(self, features):
        """Mock damage classification based on features"""
        # Simple rule-based classification for demo
        if not features:
            return "unknown", 0.0
        
        # Mock classification logic
        mfcc_mean = features.get("mfcc_mean", [0])
        spectral_centroid = features.get("spectral_centroid_mean", 0)
        
        if spectral_centroid > 2000:
            if np.mean(mfcc_mean[:3]) > 0:
                return "brake_squeal", 0.85
            else:
                return "belt_squeal", 0.78
        elif spectral_centroid > 1000:
            if features.get("zero_crossing_rate_mean", 0) > 0.1:
                return "engine_knock", 0.82
            else:
                return "transmission_grinding", 0.75
        elif spectral_centroid > 500:
            return "exhaust_leak", 0.72
        else:
            return "normal_operation", 0.90
    
    def get_repair_suggestions(self, damage_type):
        """Get repair suggestions based on damage type"""
        suggestions = {
            "engine_knock": {
                "temporary": [
                    "Use higher octane fuel",
                    "Check and replace spark plugs",
                    "Ensure proper engine oil level"
                ],
                "permanent": [
                    "Engine timing adjustment",
                    "Carbon cleaning service",
                    "Replace worn engine components",
                    "Professional engine diagnostic"
                ]
            },
            "brake_squeal": {
                "temporary": [
                    "Clean brake rotors and pads",
                    "Check brake fluid level",
                    "Avoid hard braking when possible"
                ],
                "permanent": [
                    "Replace brake pads",
                    "Resurface or replace brake rotors",
                    "Brake system inspection",
                    "Replace brake hardware"
                ]
            },
            "transmission_grinding": {
                "temporary": [
                    "Check transmission fluid level",
                    "Avoid aggressive shifting",
                    "Let transmission warm up"
                ],
                "permanent": [
                    "Transmission fluid change",
                    "Replace clutch (manual)",
                    "Transmission rebuild",
                    "Professional transmission service"
                ]
            },
            "exhaust_leak": {
                "temporary": [
                    "Use exhaust paste for small leaks",
                    "Avoid high RPM driving",
                    "Check exhaust system regularly"
                ],
                "permanent": [
                    "Replace damaged exhaust components",
                    "Weld exhaust system repairs",
                    "Complete exhaust system inspection",
                    "Replace exhaust gaskets"
                ]
            },
            "belt_squeal": {
                "temporary": [
                    "Check belt tension",
                    "Clean belt and pulleys",
                    "Use belt dressing spray"
                ],
                "permanent": [
                    "Replace worn belts",
                    "Replace belt tensioner",
                    "Pulley alignment check",
                    "Replace damaged pulleys"
                ]
            },
            "normal_operation": {
                "temporary": [
                    "Continue regular maintenance",
                    "Monitor for any changes"
                ],
                "permanent": [
                    "Follow manufacturer's maintenance schedule",
                    "Regular inspections"
                ]
            }
        }
        
        return suggestions.get(damage_type, {
            "temporary": ["Consult a professional mechanic"],
            "permanent": ["Complete diagnostic by certified technician"]
        })

# Initialize audio analyzer
audio_analyzer = AudioAnalyzer()

# Create the main app
app = FastAPI(title="Automobile Sound Damage Detection API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class AudioAnalysisResult(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    audio_data: str  # base64 encoded audio
    damage_type: str
    confidence: float
    features: Dict[str, Any]
    repair_suggestions: Dict[str, List[str]]
    file_name: str
    file_size: int

class AudioAnalysisCreate(BaseModel):
    file_name: str
    file_size: int

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Automobile Sound Damage Detection API", "status": "operational"}

@api_router.post("/analyze-audio")
async def analyze_audio(
    file: UploadFile = File(...),
    metadata: str = Form(None)
):
    """Upload and analyze automobile sound for damage detection"""
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith('audio/'):
            raise HTTPException(status_code=400, detail="File must be an audio file")
        
        # Read audio file
        audio_data = await file.read()
        
        # Analyze audio
        analysis_result = audio_analyzer.analyze_audio(audio_data)
        
        # Convert audio to base64 for storage
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        
        # Create analysis record
        analysis_record = AudioAnalysisResult(
            audio_data=audio_b64,
            damage_type=analysis_result["damage_type"],
            confidence=analysis_result["confidence"],
            features=analysis_result["features"],
            repair_suggestions=analysis_result["repair_suggestions"],
            file_name=file.filename or "unknown.wav",
            file_size=len(audio_data)
        )
        
        # Save to database
        result = await db.audio_analyses.insert_one(analysis_record.dict())
        
        # Return analysis results
        return {
            "id": analysis_record.id,
            "damage_type": analysis_record.damage_type,
            "confidence": analysis_record.confidence,
            "repair_suggestions": analysis_record.repair_suggestions,
            "timestamp": analysis_record.timestamp,
            "file_name": analysis_record.file_name
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Audio analysis error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@api_router.get("/analysis-history")
async def get_analysis_history():
    """Get all previous audio analyses"""
    try:
        analyses = await db.audio_analyses.find().to_list(100)
        return [
            {
                "id": analysis["id"],
                "timestamp": analysis["timestamp"],
                "damage_type": analysis["damage_type"],
                "confidence": analysis["confidence"],
                "file_name": analysis["file_name"],
                "repair_suggestions": analysis["repair_suggestions"]
            }
            for analysis in analyses
        ]
    except Exception as e:
        logging.error(f"History retrieval error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve history")

@api_router.get("/analysis/{analysis_id}")
async def get_analysis_details(analysis_id: str):
    """Get detailed analysis results"""
    try:
        analysis = await db.audio_analyses.find_one({"id": analysis_id})
        if not analysis:
            raise HTTPException(status_code=404, detail="Analysis not found")
        
        return {
            "id": analysis["id"],
            "timestamp": analysis["timestamp"],
            "damage_type": analysis["damage_type"],
            "confidence": analysis["confidence"],
            "features": analysis["features"],
            "repair_suggestions": analysis["repair_suggestions"],
            "file_name": analysis["file_name"],
            "file_size": analysis["file_size"]
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Analysis retrieval error: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve analysis")

# Include the router in the main app
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()