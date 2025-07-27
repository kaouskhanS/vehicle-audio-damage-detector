import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [isRecording, setIsRecording] = useState(false);
  const [audioFile, setAudioFile] = useState(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysisResult, setAnalysisResult] = useState(null);
  const [analysisHistory, setAnalysisHistory] = useState([]);
  const [activeTab, setActiveTab] = useState('upload');
  const mediaRecorderRef = useRef(null);
  const recordedChunksRef = useRef([]);
  const audioStreamRef = useRef(null);

  useEffect(() => {
    fetchAnalysisHistory();
  }, []);

  const fetchAnalysisHistory = async () => {
    try {
      const response = await axios.get(`${API}/analysis-history`);
      setAnalysisHistory(response.data);
    } catch (error) {
      console.error('Failed to fetch analysis history:', error);
    }
  };

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioStreamRef.current = stream;
      
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      recordedChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          recordedChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const blob = new Blob(recordedChunksRef.current, { type: 'audio/wav' });
        const file = new File([blob], 'recorded_audio.wav', { type: 'audio/wav' });
        setAudioFile(file);
        
        // Stop all tracks
        if (audioStreamRef.current) {
          audioStreamRef.current.getTracks().forEach(track => track.stop());
        }
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (error) {
      console.error('Error starting recording:', error);
      alert('Error accessing microphone. Please check permissions.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      setAudioFile(file);
    }
  };

  const analyzeAudio = async () => {
    if (!audioFile) {
      alert('Please upload or record an audio file first');
      return;
    }

    setIsAnalyzing(true);
    setAnalysisResult(null);

    try {
      const formData = new FormData();
      formData.append('file', audioFile);

      const response = await axios.post(`${API}/analyze-audio`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });

      setAnalysisResult(response.data);
      fetchAnalysisHistory(); // Refresh history
    } catch (error) {
      console.error('Analysis failed:', error);
      alert('Analysis failed. Please try again.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const getDamageTypeColor = (damageType) => {
    const colors = {
      'normal_operation': 'text-green-600',
      'engine_knock': 'text-red-600',
      'brake_squeal': 'text-orange-600',
      'transmission_grinding': 'text-red-700',
      'exhaust_leak': 'text-yellow-600',
      'belt_squeal': 'text-blue-600'
    };
    return colors[damageType] || 'text-gray-600';
  };

  const getDamageTypeIcon = (damageType) => {
    const icons = {
      'normal_operation': '✅',
      'engine_knock': '🔧',
      'brake_squeal': '🛑',
      'transmission_grinding': '⚙️',
      'exhaust_leak': '💨',
      'belt_squeal': '🔧'
    };
    return icons[damageType] || '❓';
  };

  const formatDamageType = (damageType) => {
    return damageType.split('_').map(word => 
      word.charAt(0).toUpperCase() + word.slice(1)
    ).join(' ');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            🚗 Automobile Sound Analyzer
          </h1>
          <p className="text-gray-600 text-lg">
            Detect vehicle damage through sound analysis using AI
          </p>
        </div>

        {/* Navigation Tabs */}
        <div className="flex justify-center mb-8">
          <div className="bg-white rounded-lg shadow-md p-1">
            <button
              onClick={() => setActiveTab('upload')}
              className={`px-6 py-3 rounded-lg font-medium transition-colors ${
                activeTab === 'upload'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-600 hover:text-blue-600'
              }`}
            >
              Upload Audio
            </button>
            <button
              onClick={() => setActiveTab('record')}
              className={`px-6 py-3 rounded-lg font-medium transition-colors ${
                activeTab === 'record'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-600 hover:text-blue-600'
              }`}
            >
              Record Audio
            </button>
            <button
              onClick={() => setActiveTab('history')}
              className={`px-6 py-3 rounded-lg font-medium transition-colors ${
                activeTab === 'history'
                  ? 'bg-blue-600 text-white'
                  : 'text-gray-600 hover:text-blue-600'
              }`}
            >
              History
            </button>
          </div>
        </div>

        {/* Main Content */}
        <div className="max-w-4xl mx-auto">
          {/* Upload Tab */}
          {activeTab === 'upload' && (
            <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
              <h2 className="text-2xl font-bold text-gray-800 mb-6">Upload Audio File</h2>
              <div className="space-y-6">
                <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-400 transition-colors">
                  <input
                    type="file"
                    accept="audio/*"
                    onChange={handleFileUpload}
                    className="hidden"
                    id="audio-upload"
                  />
                  <label
                    htmlFor="audio-upload"
                    className="cursor-pointer block"
                  >
                    <div className="text-4xl mb-4">📁</div>
                    <p className="text-gray-600 mb-2">Click to select audio file</p>
                    <p className="text-sm text-gray-500">
                      Supported formats: MP3, WAV, OGG, M4A
                    </p>
                  </label>
                </div>
                
                {audioFile && (
                  <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-sm text-gray-600">
                      Selected: <span className="font-medium">{audioFile.name}</span>
                    </p>
                    <p className="text-sm text-gray-500">
                      Size: {(audioFile.size / 1024 / 1024).toFixed(2)} MB
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Record Tab */}
          {activeTab === 'record' && (
            <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
              <h2 className="text-2xl font-bold text-gray-800 mb-6">Record Audio</h2>
              <div className="text-center space-y-6">
                <div className="text-6xl mb-4">
                  {isRecording ? '🎙️' : '🎤'}
                </div>
                <p className="text-gray-600">
                  {isRecording
                    ? 'Recording... Click stop when finished'
                    : 'Click the button below to start recording'}
                </p>
                <button
                  onClick={isRecording ? stopRecording : startRecording}
                  className={`px-8 py-4 rounded-lg font-medium text-white transition-colors ${
                    isRecording
                      ? 'bg-red-600 hover:bg-red-700'
                      : 'bg-green-600 hover:bg-green-700'
                  }`}
                >
                  {isRecording ? 'Stop Recording' : 'Start Recording'}
                </button>
                
                {audioFile && !isRecording && (
                  <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-sm text-gray-600">
                      Recorded: <span className="font-medium">{audioFile.name}</span>
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* History Tab */}
          {activeTab === 'history' && (
            <div className="bg-white rounded-lg shadow-lg p-8 mb-8">
              <h2 className="text-2xl font-bold text-gray-800 mb-6">Analysis History</h2>
              <div className="space-y-4">
                {analysisHistory.length === 0 ? (
                  <p className="text-gray-500 text-center py-8">No analysis history yet</p>
                ) : (
                  analysisHistory.map((analysis, index) => (
                    <div key={index} className="border rounded-lg p-4 hover:bg-gray-50">
                      <div className="flex justify-between items-start">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            <span className="text-2xl">{getDamageTypeIcon(analysis.damage_type)}</span>
                            <h3 className={`font-medium ${getDamageTypeColor(analysis.damage_type)}`}>
                              {formatDamageType(analysis.damage_type)}
                            </h3>
                            <span className="text-sm text-gray-500">
                              ({(analysis.confidence * 100).toFixed(1)}% confidence)
                            </span>
                          </div>
                          <p className="text-sm text-gray-600 mb-1">
                            File: {analysis.file_name}
                          </p>
                          <p className="text-sm text-gray-500">
                            {new Date(analysis.timestamp).toLocaleString()}
                          </p>
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* Analysis Button */}
          {(activeTab === 'upload' || activeTab === 'record') && audioFile && (
            <div className="text-center mb-8">
              <button
                onClick={analyzeAudio}
                disabled={isAnalyzing}
                className={`px-8 py-4 rounded-lg font-medium text-white transition-colors ${
                  isAnalyzing
                    ? 'bg-gray-400 cursor-not-allowed'
                    : 'bg-blue-600 hover:bg-blue-700'
                }`}
              >
                {isAnalyzing ? 'Analyzing...' : 'Analyze Audio'}
              </button>
            </div>
          )}

          {/* Analysis Results */}
          {analysisResult && (
            <div className="bg-white rounded-lg shadow-lg p-8">
              <h2 className="text-2xl font-bold text-gray-800 mb-6">Analysis Results</h2>
              
              {/* Damage Type */}
              <div className="mb-6">
                <div className="flex items-center space-x-3 mb-2">
                  <span className="text-3xl">{getDamageTypeIcon(analysisResult.damage_type)}</span>
                  <h3 className={`text-xl font-bold ${getDamageTypeColor(analysisResult.damage_type)}`}>
                    {formatDamageType(analysisResult.damage_type)}
                  </h3>
                </div>
                <p className="text-gray-600">
                  Confidence: <span className="font-medium">{(analysisResult.confidence * 100).toFixed(1)}%</span>
                </p>
              </div>

              {/* Repair Suggestions */}
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <h4 className="text-lg font-semibold text-gray-800 mb-3">🔧 Temporary Fixes</h4>
                  <ul className="space-y-2">
                    {analysisResult.repair_suggestions.temporary.map((suggestion, index) => (
                      <li key={index} className="flex items-start space-x-2">
                        <span className="text-yellow-500 mt-1">•</span>
                        <span className="text-gray-700">{suggestion}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                
                <div>
                  <h4 className="text-lg font-semibold text-gray-800 mb-3">🛠️ Permanent Solutions</h4>
                  <ul className="space-y-2">
                    {analysisResult.repair_suggestions.permanent.map((suggestion, index) => (
                      <li key={index} className="flex items-start space-x-2">
                        <span className="text-green-500 mt-1">•</span>
                        <span className="text-gray-700">{suggestion}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Disclaimer */}
              <div className="mt-8 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <p className="text-sm text-yellow-800">
                  <strong>⚠️ Disclaimer:</strong> This is an AI-powered analysis tool. 
                  For accurate diagnosis and repairs, please consult with a qualified mechanic.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;