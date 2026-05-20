import React, { useState, useEffect } from 'react';
import api, { API_BASE_URL } from '../services/api';
import { useAuth } from '../context/AuthContext';
import { 
  Camera, Leaf, Loader, FileText, CheckCircle, Clock, AlertCircle, 
  MapPin, Phone, Globe, ChevronRight, BookOpen, AlertTriangle, Eye 
} from 'lucide-react';

const PatientDashboard = () => {
  const { user } = useAuth();
  
  // Navigation tabs
  const [activeTab, setActiveTab] = useState('wizard'); // 'wizard' | 'plans' | 'scans' | 'shops'

  // Wizard state
  const [wizardStep, setWizardStep] = useState(1); // 1: Scan, 2: Quiz, 3: Profile, 4: Result
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState('');
  const [scanLoading, setScanLoading] = useState(false);
  const [scanResult, setScanResult] = useState(null);
  
  // Quiz variables
  const [quizQuestions, setQuizQuestions] = useState([]);
  const [quizAnswers, setQuizAnswers] = useState({
    body_frame: 'medium',
    hunger: 'very_strong',
    sleep: 'sound',
    feeling: 'hot',
    digestion: 'burning',
    mood: 'focused_irritable',
  });
  
  // Profile specifics state
  const [skinType, setSkinType] = useState('normal');
  const [ageGroup, setAgeGroup] = useState('21-30');
  const [season, setSeason] = useState('summer');
  const [lifestyle, setLifestyle] = useState([]);

  // Output plan state
  const [generatedPlan, setGeneratedPlan] = useState(null);
  const [genLoading, setGenLoading] = useState(false);
  const [genError, setGenError] = useState('');

  // Histories state
  const [planHistory, setPlanHistory] = useState([]);
  const [plansLoading, setPlansLoading] = useState(false);
  const [scanHistory, setScanHistory] = useState([]);
  const [scansLoading, setScansLoading] = useState(false);

  // Shop locator state
  const [shops, setShops] = useState([]);
  const [shopsMessage, setShopsMessage] = useState('');
  const [shopsLoading, setShopsLoading] = useState(false);
  const [shopsError, setShopsError] = useState('');
  const [manualLat, setManualLat] = useState('');
  const [manualLon, setManualLon] = useState('');
  const [showManualEntry, setShowManualEntry] = useState(false);

  // Selected plan detail modal
  const [selectedPlanDetail, setSelectedPlanDetail] = useState(null);

  // Fetch histories and questions on mount
  useEffect(() => {
    fetchQuestions();
    fetchPlanHistory();
    fetchScanHistory();
  }, []);

  const fetchQuestions = async () => {
    try {
      const response = await api.get('/plan/questions');
      setQuizQuestions(response.data);
    } catch (err) {
      console.error('Error fetching quiz questions:', err);
    }
  };

  const fetchPlanHistory = async () => {
    setPlansLoading(true);
    try {
      const response = await api.get('/plan/history');
      setPlanHistory(response.data);
    } catch (err) {
      console.error('Error fetching plan history:', err);
    } finally {
      setPlansLoading(false);
    }
  };

  const fetchScanHistory = async () => {
    setScansLoading(true);
    try {
      const response = await api.get('/predict/history');
      if (response.data?.status === 'success') {
        setScanHistory(response.data.history);
      }
    } catch (err) {
      console.error('Error fetching scan history:', err);
    } finally {
      setScansLoading(false);
    }
  };

  // Image upload handler
  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        alert('File size exceeds 5MB limit.');
        return;
      }
      setImageFile(file);
      setImagePreview(URL.createObjectURL(file));
      setScanResult(null);
    }
  };

  // Trigger skin scan API
  const handleScanSubmit = async (e) => {
    e.preventDefault();
    if (!imageFile) return;

    setScanLoading(true);
    const formData = new FormData();
    formData.append('file', imageFile);

    try {
      const response = await api.post('/predict', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      setScanResult(response.data);
      // Move to quiz questions step
      setWizardStep(2);
    } catch (err) {
      console.error('Scan error:', err);
      alert(err.response?.data?.detail || 'Scan prediction failed. Please try a different image.');
    } finally {
      setScanLoading(false);
    }
  };

  // Quiz Option mapping helper
  const handleQuizAnswer = (questionId, optionKey) => {
    setQuizAnswers(prev => ({
      ...prev,
      [questionId]: optionKey
    }));
  };

  // Multi-select lifestyle habits
  const handleLifestyleChange = (habit) => {
    if (lifestyle.includes(habit)) {
      setLifestyle(lifestyle.filter(item => item !== habit));
    } else {
      setLifestyle([...lifestyle, habit]);
    }
  };

  // Generate Plan API
  const handleGeneratePlan = async () => {
    if (!scanResult?.prediction_id) {
      alert('Please perform skin analysis first.');
      setWizardStep(1);
      return;
    }

    setGenLoading(true);
    setGenError('');

    try {
      const payload = {
        prediction_id: scanResult.prediction_id,
        dosha_answers: quizAnswers,
        skin_type: skinType,
        age_group: ageGroup,
        season: season,
        lifestyle: lifestyle
      };

      const response = await api.post('/plan/generate', payload);
      setGeneratedPlan(response.data);
      setWizardStep(4);
      // Refresh histories
      fetchPlanHistory();
      fetchScanHistory();
    } catch (err) {
      console.error('Plan generation failed:', err);
      setGenError(err.response?.data?.detail || 'Plan generation failed. Please check inputs.');
    } finally {
      setGenLoading(false);
    }
  };

  // Geolocation shop finder API
  const handleFindShops = (manualCoords = null) => {
    setShopsLoading(true);
    setShopsError('');
    setShops([]);
    setShopsMessage('');

    const searchAction = async (lat, lon) => {
      try {
        const response = await api.post('/shops/nearby', {
          latitude: lat,
          longitude: lon,
          radius_km: 5
        });
        if (response.data.status === 'success') {
          setShops(response.data.shops);
          setShopsMessage(response.data.message);
        } else {
          setShopsError('Failed to fetch nearby shops.');
        }
      } catch (err) {
        console.error(err);
        setShopsError(err.response?.data?.detail || 'OSM servers are busy. Please retry.');
      } finally {
        setShopsLoading(false);
      }
    };

    if (manualCoords) {
      searchAction(manualCoords.lat, manualCoords.lon);
      return;
    }

    if (!navigator.geolocation) {
      setShopsError('Geolocation is not supported by your browser.');
      setShopsLoading(false);
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        searchAction(position.coords.latitude, position.coords.longitude);
      },
      (error) => {
        setShopsError('Location permission denied. Try manual search instead.');
        setShopsLoading(false);
      },
      { timeout: 15000 }
    );
  };

  // Reset wizard flow
  const handleResetWizard = () => {
    setImageFile(null);
    setImagePreview('');
    setScanResult(null);
    setGeneratedPlan(null);
    setWizardStep(1);
  };

  return (
    <div className="min-h-screen bg-stone-50 pt-16 pb-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* Welcome Dashboard Banner */}
        <div className="bg-white border border-stone-200 p-6 sm:p-8 rounded-2xl shadow-sm mb-8 flex flex-col md:flex-row md:items-center md:justify-between gap-4 mt-6">
          <div className="space-y-1">
            <h1 className="text-3xl font-bold tracking-tight text-stone-900">
              Namaste, <span className="text-emerald-700">{user?.full_name}</span>
            </h1>
            <p className="text-stone-500 text-sm">
              Your holistic Ayurvedic skincare portal. Let's analyze and optimize your skin health today.
            </p>
          </div>
          <div className="bg-emerald-50 border border-emerald-100 px-4 py-3 rounded-xl flex items-center gap-3 self-start md:self-center">
            <Leaf className="w-6 h-6 text-emerald-800 animate-pulse shrink-0" />
            <div className="text-xs text-stone-700">
              <span className="font-semibold block text-emerald-900">Role: Patient Member</span>
              Vetted by our clinical Ayurveda network
            </div>
          </div>
        </div>

        {/* Dashboard Tabs */}
        <div className="flex border-b border-stone-200 mb-8 overflow-x-auto gap-6 scrollbar-hide">
          <button
            onClick={() => setActiveTab('wizard')}
            className={`pb-4 text-sm font-semibold whitespace-nowrap border-b-2 transition-colors ${
              activeTab === 'wizard'
                ? 'border-emerald-600 text-emerald-800 font-bold'
                : 'border-transparent text-stone-500 hover:text-stone-700'
            }`}
          >
            Create Treatment Plan
          </button>
          <button
            onClick={() => setActiveTab('plans')}
            className={`pb-4 text-sm font-semibold whitespace-nowrap border-b-2 transition-colors ${
              activeTab === 'plans'
                ? 'border-emerald-600 text-emerald-800 font-bold'
                : 'border-transparent text-stone-500 hover:text-stone-700'
            }`}
          >
            My Saved Plans ({planHistory.length})
          </button>
          <button
            onClick={() => setActiveTab('scans')}
            className={`pb-4 text-sm font-semibold whitespace-nowrap border-b-2 transition-colors ${
              activeTab === 'scans'
                ? 'border-emerald-600 text-emerald-800 font-bold'
                : 'border-transparent text-stone-500 hover:text-stone-700'
            }`}
          >
            Scan Log ({scanHistory.length})
          </button>
          <button
            onClick={() => setActiveTab('shops')}
            className={`pb-4 text-sm font-semibold whitespace-nowrap border-b-2 transition-colors ${
              activeTab === 'shops'
                ? 'border-emerald-600 text-emerald-800 font-bold'
                : 'border-transparent text-stone-500 hover:text-stone-700'
            }`}
          >
            Nearby Ayurvedic Shops
          </button>
        </div>

        {/* ==================== TAB 1: GENERATION WIZARD ==================== */}
        {activeTab === 'wizard' && (
          <div className="bg-white border border-stone-200 rounded-2xl shadow-sm overflow-hidden">
            {/* Wizard Steps indicator header */}
            <div className="bg-stone-50/50 border-b border-stone-200 py-4 px-6 grid grid-cols-4 text-center text-xs font-semibold text-stone-400">
              <span className={wizardStep >= 1 ? 'text-emerald-700 font-bold' : ''}>1. Skin Scan</span>
              <span className={wizardStep >= 2 ? 'text-emerald-700 font-bold' : ''}>2. Dosha Test</span>
              <span className={wizardStep >= 3 ? 'text-emerald-700 font-bold' : ''}>3. Personalize</span>
              <span className={wizardStep >= 4 ? 'text-emerald-700 font-bold' : ''}>4. Results</span>
            </div>

            <div className="p-6 sm:p-8">
              {/* STEP 1: SKIN SCAN UPLOAD */}
              {wizardStep === 1 && (
                <div className="max-w-xl mx-auto space-y-6">
                  <div className="text-center space-y-2">
                    <h3 className="text-xl font-bold text-stone-900">Upload Facial Skin Scan</h3>
                    <p className="text-stone-500 text-sm">
                      Our PyTorch deep learning model will analyze your facial image to detect skin issues like acne, blackheads, spots, pores, or wrinkles.
                    </p>
                  </div>

                  <form onSubmit={handleScanSubmit} className="space-y-6">
                    <div className="flex flex-col items-center justify-center border-2 border-dashed border-stone-300 rounded-2xl p-6 bg-stone-50/50 hover:bg-stone-50 transition-colors relative group min-h-[220px]">
                      {imagePreview ? (
                        <div className="relative w-full max-h-[280px] flex justify-center">
                          <img
                            src={imagePreview}
                            alt="Skin preview"
                            className="max-h-[240px] rounded-xl object-contain shadow-md"
                          />
                          <button
                            type="button"
                            onClick={() => {
                              setImageFile(null);
                              setImagePreview('');
                            }}
                            className="absolute -top-2 -right-2 bg-rose-600 text-white rounded-full p-1.5 hover:bg-rose-700 shadow-md transition active:scale-95 text-xs font-bold"
                          >
                            Remove
                          </button>
                        </div>
                      ) : (
                        <label className="cursor-pointer flex flex-col items-center space-y-3">
                          <div className="w-14 h-14 bg-emerald-50 rounded-full flex items-center justify-center text-emerald-800 shadow-sm border border-emerald-100 group-hover:bg-emerald-100 transition-colors">
                            <Camera className="w-7 h-7" />
                          </div>
                          <div className="text-center">
                            <span className="text-sm font-semibold text-emerald-700 hover:text-emerald-800">
                              Upload Face Scan
                            </span>
                            <p className="text-stone-400 text-xs mt-1">JPG / PNG / WEBP, Max 5MB</p>
                          </div>
                          <input
                            type="file"
                            accept="image/*"
                            onChange={handleImageChange}
                            className="hidden"
                            required
                          />
                        </label>
                      )}
                    </div>

                    <button
                      type="submit"
                      disabled={!imageFile || scanLoading}
                      className="w-full flex items-center justify-center gap-2 py-3 px-4 rounded-xl text-sm font-semibold text-white bg-emerald-700 hover:bg-emerald-800 disabled:opacity-50 disabled:pointer-events-none active:scale-98 transition shadow-md"
                    >
                      {scanLoading ? (
                        <>
                          <Loader className="w-4 h-4 animate-spin" />
                          Analyzing facial scan (Running ML Model)...
                        </>
                      ) : (
                        'Analyze Skin Condition'
                      )}
                    </button>
                  </form>
                </div>
              )}

              {/* STEP 2: DOSHA QUIZ */}
              {wizardStep === 2 && (
                <div className="max-w-2xl mx-auto space-y-6">
                  <div className="text-center space-y-2">
                    <h3 className="text-xl font-bold text-stone-900">Quick-6 Prakriti Quiz</h3>
                    <p className="text-stone-500 text-sm">
                      Select options that best describe your regular constitutional state to compute your dominant Dosha focus.
                    </p>
                  </div>

                  {/* Display quiz scan results metadata */}
                  {scanResult && (
                    <div className="p-4 rounded-xl bg-emerald-50/50 border border-emerald-100 flex items-start gap-3">
                      <CheckCircle className="w-5 h-5 text-emerald-700 shrink-0 mt-0.5" />
                      <div className="text-xs text-stone-700">
                        <span className="font-semibold text-emerald-900 block">Skin Diagnostic Successful!</span>
                        Detected: <span className="font-bold underline">{scanResult.detected_conditions.join(', ') || 'Normal/None'}</span>.
                        <p className="text-[10px] text-stone-400 mt-1">ID: {scanResult.prediction_id}</p>
                      </div>
                    </div>
                  )}

                  <div className="space-y-6">
                    {/* Render static questions list */}
                    {quizQuestions.length > 0 ? (
                      quizQuestions.map((q) => (
                        <div key={q.id} className="p-5 border border-stone-200 rounded-xl space-y-3 bg-stone-50/20">
                          <h4 className="font-semibold text-stone-850 text-sm flex gap-2">
                            <span className="text-emerald-700 font-bold">Q:</span>
                            {q.question}
                          </h4>
                          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
                            {Object.entries(q.options).map(([key, label]) => {
                              const isChecked = quizAnswers[q.id] === key;
                              return (
                                <button
                                  key={key}
                                  onClick={() => handleQuizAnswer(q.id, key)}
                                  className={`p-3 text-xs border rounded-xl font-medium transition-all text-left flex items-start gap-2 ${
                                    isChecked
                                      ? 'border-emerald-600 bg-emerald-50/50 text-emerald-900 shadow-sm'
                                      : 'border-stone-200 bg-white text-stone-600 hover:bg-stone-50'
                                  }`}
                                >
                                  <input
                                    type="radio"
                                    name={q.id}
                                    checked={isChecked}
                                    onChange={() => {}}
                                    className="mt-0.5 accent-emerald-700"
                                  />
                                  <span>{label}</span>
                                </button>
                              );
                            })}
                          </div>
                        </div>
                      ))
                    ) : (
                      <div className="flex justify-center p-6">
                        <Loader className="w-6 h-6 animate-spin text-stone-400" />
                      </div>
                    )}
                  </div>

                  <div className="flex gap-4">
                    <button
                      onClick={() => setWizardStep(1)}
                      className="w-1/3 py-3 border border-stone-300 rounded-xl text-sm font-semibold text-stone-700 hover:bg-stone-50 transition active:scale-95"
                    >
                      Back
                    </button>
                    <button
                      onClick={() => setWizardStep(3)}
                      className="w-2/3 py-3 rounded-xl text-sm font-semibold text-white bg-emerald-700 hover:bg-emerald-800 transition active:scale-95 shadow-md flex justify-center items-center gap-1.5"
                    >
                      Continue to Profile Specifics
                      <ChevronRight className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              )}

              {/* STEP 3: PROFILE SPECIFICS */}
              {wizardStep === 3 && (
                <div className="max-w-xl mx-auto space-y-6">
                  <div className="text-center space-y-2">
                    <h3 className="text-xl font-bold text-stone-900">Personalize Your Rules</h3>
                    <p className="text-stone-500 text-sm">
                      Specify environmental variables to customize daily routines and diet ingredient swaps.
                    </p>
                  </div>

                  <div className="space-y-4">
                    <div>
                      <label className="block text-sm font-semibold text-stone-700 mb-1">
                        Current Skin Type
                      </label>
                      <select
                        value={skinType}
                        onChange={(e) => setSkinType(e.target.value)}
                        className="block w-full px-3 py-3 border border-stone-300 rounded-xl bg-stone-50/50 text-stone-950 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent text-sm"
                      >
                        <option value="oily">Oily</option>
                        <option value="dry">Dry</option>
                        <option value="sensitive">Sensitive</option>
                        <option value="combination">Combination</option>
                        <option value="normal">Normal</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-stone-700 mb-1">
                        Age Group
                      </label>
                      <select
                        value={ageGroup}
                        onChange={(e) => setAgeGroup(e.target.value)}
                        className="block w-full px-3 py-3 border border-stone-300 rounded-xl bg-stone-50/50 text-stone-950 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent text-sm"
                      >
                        <option value="10-20">10-20 Years</option>
                        <option value="21-30">21-30 Years</option>
                        <option value="31-40">31-40 Years</option>
                        <option value="40+">40+ Years</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-stone-700 mb-1">
                        Current Season
                      </label>
                      <select
                        value={season}
                        onChange={(e) => setSeason(e.target.value)}
                        className="block w-full px-3 py-3 border border-stone-300 rounded-xl bg-stone-50/50 text-stone-950 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent text-sm"
                      >
                        <option value="summer">Summer</option>
                        <option value="winter">Winter</option>
                        <option value="monsoon">Monsoon</option>
                        <option value="autumn">Autumn</option>
                      </select>
                    </div>

                    <div>
                      <label className="block text-sm font-semibold text-stone-700 mb-2">
                        Lifestyle & Physiological Conditions (Multi-select)
                      </label>
                      <div className="grid grid-cols-2 gap-3">
                        {[
                          { key: 'high_stress', val: 'High Stress Environment' },
                          { key: 'low_water', val: 'Low Daily Water Intake' },
                          { key: 'vegan', val: 'Strict Vegan Diet' },
                          { key: 'female', val: 'Female Physiological Cycle' },
                          { key: 'poor_sleep', val: 'Poor/Irregular Sleep' }
                        ].map(item => {
                          const isSelected = lifestyle.includes(item.key);
                          return (
                            <button
                              key={item.key}
                              type="button"
                              onClick={() => handleLifestyleChange(item.key)}
                              className={`p-3 text-left text-xs border rounded-xl font-medium transition-all flex items-center gap-2 ${
                                isSelected 
                                  ? 'border-emerald-600 bg-emerald-50/50 text-emerald-900 shadow-sm'
                                  : 'border-stone-200 bg-white text-stone-600 hover:bg-stone-50'
                              }`}
                            >
                              <input
                                type="checkbox"
                                checked={isSelected}
                                onChange={() => {}}
                                className="accent-emerald-700"
                              />
                              {item.val}
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  </div>

                  {genError && (
                    <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 flex items-start gap-3 text-rose-800 text-sm">
                      <AlertCircle className="w-5 h-5 shrink-0" />
                      <div>{genError}</div>
                    </div>
                  )}

                  <div className="flex gap-4 pt-2">
                    <button
                      onClick={() => setWizardStep(2)}
                      className="w-1/3 py-3 border border-stone-300 rounded-xl text-sm font-semibold text-stone-700 hover:bg-stone-50 transition active:scale-95"
                    >
                      Back
                    </button>
                    <button
                      onClick={handleGeneratePlan}
                      disabled={genLoading}
                      className="w-2/3 py-3 rounded-xl text-sm font-semibold text-white bg-emerald-700 hover:bg-emerald-800 transition active:scale-95 shadow-md flex justify-center items-center gap-1.5"
                    >
                      {genLoading ? (
                        <>
                          <Loader className="w-4 h-4 animate-spin" />
                          Assembling Treatment Plan...
                        </>
                      ) : (
                        <>
                          Generate 7-Day Plan
                          <Leaf className="w-4 h-4" />
                        </>
                      )}
                    </button>
                  </div>
                </div>
              )}

              {/* STEP 4: VIEW GENERATED PLAN */}
              {wizardStep === 4 && generatedPlan && (
                <div className="space-y-8">
                  <div className="text-center space-y-3">
                    <div className="mx-auto w-12 h-12 bg-emerald-100 text-emerald-800 rounded-full flex items-center justify-center">
                      <CheckCircle className="w-6 h-6" />
                    </div>
                    <h3 className="text-2xl font-bold text-stone-900">{generatedPlan.title}</h3>
                    <p className="text-stone-500 text-sm max-w-xl mx-auto">{generatedPlan.overview}</p>
                    
                    {/* Status Badge */}
                    <div className="flex justify-center gap-2 pt-1.5">
                      <span className="bg-emerald-50 text-emerald-800 text-xs font-semibold px-3 py-1 rounded-full border border-emerald-100 flex items-center gap-1">
                        <Leaf className="w-3.5 h-3.5" />
                        Dosha: {generatedPlan.dosha_focus}
                      </span>
                      {generatedPlan.is_doctor_vetted ? (
                        <span className="bg-emerald-100 text-emerald-900 text-xs font-bold px-3 py-1 rounded-full border border-emerald-200 flex items-center gap-1">
                          <CheckCircle className="w-3.5 h-3.5 text-emerald-800" />
                          Vetted by Dr. {generatedPlan.doctor_name}
                        </span>
                      ) : (
                        <span className="bg-amber-50 text-amber-800 text-xs font-semibold px-3 py-1 rounded-full border border-amber-100 flex items-center gap-1 animate-pulse">
                          <Clock className="w-3.5 h-3.5 text-amber-700" />
                          Pending Doctor Vetting
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Personalization notes log */}
                  {generatedPlan.personalization_notes?.length > 0 && (
                    <div className="p-5 bg-amber-50/40 border border-amber-200/60 rounded-xl space-y-2">
                      <h4 className="text-xs font-bold text-amber-850 uppercase tracking-wider flex items-center gap-1.5">
                        <AlertTriangle className="w-4 h-4 text-amber-700" />
                        Personalization Tweaks Applied:
                      </h4>
                      <ul className="list-disc list-inside text-xs text-stone-600 space-y-1.5">
                        {generatedPlan.personalization_notes.map((note, index) => (
                          <li key={index}>{note}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {/* Doctor Notes Display */}
                  {generatedPlan.is_doctor_vetted && generatedPlan.doctor_notes && (
                    <div className="p-5 bg-emerald-50/30 border border-emerald-200/40 rounded-xl space-y-2">
                      <h4 className="text-xs font-bold text-emerald-950 uppercase tracking-wider flex items-center gap-1.5">
                        <CheckCircle className="w-4 h-4 text-emerald-800" />
                        Clinical Vetting Annotations:
                      </h4>
                      <p className="text-xs italic text-stone-600">{generatedPlan.doctor_notes}</p>
                    </div>
                  )}

                  {/* 7 Days Schedule render */}
                  <div className="space-y-6">
                    <h4 className="text-lg font-bold text-stone-900 border-b pb-2">Your 7-Day Routine</h4>
                    <div className="space-y-6">
                      {generatedPlan.days.map((dayPlan) => (
                        <div key={dayPlan.day} className="border border-stone-200 rounded-xl overflow-hidden shadow-sm bg-white">
                          {/* Day Header */}
                          <div className="bg-stone-50 border-b border-stone-200 px-5 py-3 flex items-center gap-3">
                            <span className="bg-emerald-700 text-white text-xs font-bold px-2.5 py-1 rounded-full">Day {dayPlan.day}</span>
                            <h5 className="font-bold text-stone-800 text-sm">{dayPlan.theme}</h5>
                          </div>
                          <div className="p-5 grid grid-cols-1 md:grid-cols-2 gap-5 text-xs">

                            {/* Morning Block */}
                            <div className="space-y-2">
                              <span className="font-bold text-emerald-700 text-sm block">🌅 Morning ({dayPlan.morning.time})</span>
                              <div>
                                <p className="font-semibold text-stone-600 text-[10px] uppercase tracking-wide mb-1">Routine Steps</p>
                                <ul className="list-disc list-inside space-y-0.5 text-stone-700">
                                  {dayPlan.morning.routine.map((r, i) => <li key={i}>{r}</li>)}
                                </ul>
                              </div>
                              {dayPlan.morning.ingredients?.length > 0 && (
                                <div>
                                  <p className="font-semibold text-stone-600 text-[10px] uppercase tracking-wide mb-1">Ingredients</p>
                                  <p className="text-stone-500">{dayPlan.morning.ingredients.join(', ')}</p>
                                </div>
                              )}
                              {dayPlan.morning.procedure?.length > 0 && (
                                <div>
                                  <p className="font-semibold text-stone-600 text-[10px] uppercase tracking-wide mb-1">Step-by-Step Procedure</p>
                                  <ol className="space-y-1 text-stone-700">
                                    {dayPlan.morning.procedure.map((step, i) => (
                                      <li key={i} className="leading-relaxed">{step}</li>
                                    ))}
                                  </ol>
                                </div>
                              )}
                            </div>

                            {/* Evening Block */}
                            <div className="space-y-2">
                              <span className="font-bold text-indigo-700 text-sm block">🌌 Evening ({dayPlan.evening.time})</span>
                              <div>
                                <p className="font-semibold text-stone-600 text-[10px] uppercase tracking-wide mb-1">Routine Steps</p>
                                <ul className="list-disc list-inside space-y-0.5 text-stone-700">
                                  {dayPlan.evening.routine.map((r, i) => <li key={i}>{r}</li>)}
                                </ul>
                              </div>
                              {dayPlan.evening.ingredients?.length > 0 && (
                                <div>
                                  <p className="font-semibold text-stone-600 text-[10px] uppercase tracking-wide mb-1">Ingredients</p>
                                  <p className="text-stone-500">{dayPlan.evening.ingredients.join(', ')}</p>
                                </div>
                              )}
                              {dayPlan.evening.procedure?.length > 0 && (
                                <div>
                                  <p className="font-semibold text-stone-600 text-[10px] uppercase tracking-wide mb-1">Step-by-Step Procedure</p>
                                  <ol className="space-y-1 text-stone-700">
                                    {dayPlan.evening.procedure.map((step, i) => (
                                      <li key={i} className="leading-relaxed">{step}</li>
                                    ))}
                                  </ol>
                                </div>
                              )}
                            </div>

                            {/* Diet Block */}
                            <div className="space-y-2 md:col-span-2 border-t pt-4">
                              <span className="font-bold text-amber-700 text-sm block">🍽️ Diet Recommendations</span>
                              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                                <div><p className="font-semibold text-stone-600 text-[10px] uppercase tracking-wide">Breakfast</p><p className="text-stone-700 mt-0.5">{dayPlan.diet.breakfast}</p></div>
                                <div><p className="font-semibold text-stone-600 text-[10px] uppercase tracking-wide">Lunch</p><p className="text-stone-700 mt-0.5">{dayPlan.diet.lunch}</p></div>
                                <div><p className="font-semibold text-stone-600 text-[10px] uppercase tracking-wide">Dinner</p><p className="text-stone-700 mt-0.5">{dayPlan.diet.dinner}</p></div>
                                {dayPlan.diet.drinks?.length > 0 && (
                                  <div><p className="font-semibold text-stone-600 text-[10px] uppercase tracking-wide">Drinks</p><p className="text-stone-700 mt-0.5">{dayPlan.diet.drinks.join(', ')}</p></div>
                                )}
                              </div>
                              {dayPlan.diet.avoid?.length > 0 && (
                                <div className="mt-2">
                                  <p className="font-semibold text-rose-700 text-[10px] uppercase tracking-wide mb-0.5">❌ Avoid</p>
                                  <p className="text-stone-600">{dayPlan.diet.avoid.join(', ')}</p>
                                </div>
                              )}
                            </div>

                            {/* Yoga + Tip */}
                            <div className="md:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-3 border-t pt-4">
                              <div className="bg-stone-50 rounded-lg p-3">
                                <span className="font-semibold text-stone-800 text-[11px] block mb-1">🧘 Yoga / Pranayama</span>
                                <p className="text-stone-700">{dayPlan.yoga}</p>
                              </div>
                              <div className="bg-emerald-50/40 border border-emerald-100 rounded-lg p-3">
                                <span className="font-semibold text-emerald-900 text-[11px] block mb-1">💡 Day Tip</span>
                                <p className="italic text-stone-600">{dayPlan.tip}</p>
                              </div>
                            </div>

                          </div>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Weekly Summary */}
                  {generatedPlan.weekly_summary && (
                    <div className="border border-stone-200 rounded-xl p-6 bg-stone-50/50 space-y-4">
                      <h4 className="text-base font-bold text-stone-900 border-b pb-2">Weekly Treatment Summary</h4>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
                        <div className="space-y-2">
                          <div>
                            <span className="font-bold text-emerald-800">Key Ingredients to Procure:</span>
                            <p className="text-stone-600 mt-0.5">{generatedPlan.weekly_summary.key_ingredients.join(', ')}</p>
                          </div>
                          <div className="pt-2">
                            <span className="font-bold text-stone-850">Key Diet Adjustments:</span>
                            <p className="text-stone-600 mt-0.5">{Array.isArray(generatedPlan.weekly_summary.key_diet_changes) ? generatedPlan.weekly_summary.key_diet_changes.join(', ') : generatedPlan.weekly_summary.key_diet_changes}</p>
                          </div>
                        </div>
                        <div className="space-y-2">
                          <div>
                            <span className="font-bold text-stone-850">Expected Results:</span>
                            <p className="text-stone-600 mt-0.5">{generatedPlan.weekly_summary.expected_results}</p>
                          </div>
                          <div className="pt-2">
                            <span className="font-bold text-emerald-850">Post-7 Days Continuity:</span>
                            <p className="text-stone-600 mt-0.5">{generatedPlan.weekly_summary.continue_after_7_days}</p>
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  <div className="flex justify-center">
                    <button
                      onClick={handleResetWizard}
                      className="px-6 py-3 rounded-xl text-sm font-semibold text-white bg-emerald-700 hover:bg-emerald-800 active:scale-95 transition shadow-md"
                    >
                      Analyze Another Skin Scan
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ==================== TAB 2: SAVED PLANS HISTORY ==================== */}
        {activeTab === 'plans' && (
          <div className="space-y-6">
            <div className="bg-white border border-stone-200 rounded-2xl shadow-sm p-6">
              <h3 className="text-xl font-bold text-stone-900 mb-2">Saved Ayurvedic Schedules</h3>
              <p className="text-stone-500 text-sm">
                Here are your generated 7-day schedules. Plans with verified ticks have been medically audited.
              </p>
            </div>

            {plansLoading ? (
              <div className="flex justify-center py-12">
                <Loader className="w-8 h-8 animate-spin text-stone-400" />
              </div>
            ) : planHistory.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {planHistory.map((plan, index) => (
                  <div 
                    key={index}
                    className="bg-white border border-stone-200 rounded-2xl shadow-sm p-6 hover:shadow-md transition flex flex-col justify-between"
                  >
                    <div className="space-y-3">
                      <div className="flex items-start justify-between gap-4">
                        <h4 className="font-bold text-stone-900 text-lg leading-snug">{plan.title}</h4>
                        {plan.is_doctor_vetted ? (
                          <span className="shrink-0 bg-emerald-100 text-emerald-950 text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center gap-1 border border-emerald-200">
                            <CheckCircle className="w-3 h-3 text-emerald-800" />
                            Verified
                          </span>
                        ) : (
                          <span className="shrink-0 bg-amber-50 text-amber-800 text-[10px] font-semibold px-2 py-0.5 rounded-full flex items-center gap-1 border border-amber-100">
                            <Clock className="w-3 h-3 text-amber-700" />
                            Pending Review
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-stone-500 line-clamp-2">{plan.overview}</p>
                      
                      <div className="flex flex-wrap gap-1.5 pt-1">
                        <span className="text-[10px] font-semibold bg-stone-100 text-stone-700 px-2 py-0.5 rounded-md">
                          Dosha: {plan.dosha_focus}
                        </span>
                        <span className="text-[10px] font-semibold bg-emerald-50 text-emerald-800 px-2 py-0.5 rounded-md">
                          Target: {plan.required_specialty}
                        </span>
                      </div>
                    </div>

                    <div className="border-t border-stone-100 mt-6 pt-4 flex items-center justify-between text-xs text-stone-400">
                      <span>Created: {new Date(plan.created_at).toLocaleDateString()}</span>
                      <button
                        onClick={() => setSelectedPlanDetail(plan)}
                        className="flex items-center gap-1 font-semibold text-emerald-700 hover:text-emerald-800"
                      >
                        <Eye className="w-4 h-4" />
                        View Full Schedule
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center p-12 bg-white border border-stone-200 rounded-2xl">
                <FileText className="w-12 h-12 text-stone-300 mx-auto mb-3" />
                <h4 className="font-semibold text-stone-800">No schedules saved</h4>
                <p className="text-stone-400 text-xs mt-1">Complete a skin scan and diagnostic quiz to build your first plan.</p>
              </div>
            )}
          </div>
        )}

        {/* ==================== TAB 3: SCAN HISTORY ==================== */}
        {activeTab === 'scans' && (
          <div className="space-y-6">
            <div className="bg-white border border-stone-200 rounded-2xl shadow-sm p-6">
              <h3 className="text-xl font-bold text-stone-900 mb-2">Scan & Prediction Log</h3>
              <p className="text-stone-500 text-sm">
                A ledger of your past skin scan diagnosis checks. Use these IDs to regenerate plans.
              </p>
            </div>

            {scansLoading ? (
              <div className="flex justify-center py-12">
                <Loader className="w-8 h-8 animate-spin text-stone-400" />
              </div>
            ) : scanHistory.length > 0 ? (
              <div className="bg-white border border-stone-200 rounded-2xl shadow-sm overflow-hidden">
                <table className="min-w-full divide-y divide-stone-200 text-left text-sm">
                  <thead className="bg-stone-50 text-stone-500 text-xs uppercase font-bold">
                    <tr>
                      <th className="px-6 py-3">Scan Date</th>
                      <th className="px-6 py-3">Detected Skin Conditions</th>
                      <th className="px-6 py-3">Outcome / Recommendation</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-stone-200 text-stone-700">
                    {scanHistory.map((scan, idx) => (
                      <tr key={idx} className="hover:bg-stone-50/50">
                        <td className="px-6 py-4 whitespace-nowrap text-xs text-stone-400">
                          {new Date(scan.created_at).toLocaleString()}
                        </td>
                        <td className="px-6 py-4 font-semibold text-stone-900">
                          {scan.detected_conditions.join(', ') || 'No conditions / Normal Skin'}
                        </td>
                        <td className="px-6 py-4 text-xs">
                          {scan.consult_doctor ? (
                            <span className="text-amber-800 bg-amber-50 px-2.5 py-1 rounded-full border border-amber-100">
                              Consult Dermatologist
                            </span>
                          ) : (
                            <span className="text-emerald-800 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-100">
                              System Plan Available
                            </span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              <div className="text-center p-12 bg-white border border-stone-200 rounded-2xl">
                <Camera className="w-12 h-12 text-stone-300 mx-auto mb-3" />
                <h4 className="font-semibold text-stone-800">No scans logged</h4>
                <p className="text-stone-400 text-xs mt-1">Uploaded images will build your skin ledger here.</p>
              </div>
            )}
          </div>
        )}

        {/* ==================== TAB 4: NEARBY SHOPS ==================== */}
        {activeTab === 'shops' && (
          <div className="bg-white border border-stone-200 rounded-2xl shadow-sm p-6 sm:p-8 space-y-8">
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4 border-b border-stone-100 pb-6">
              <div className="space-y-1 text-center sm:text-left">
                <h3 className="text-xl font-bold text-stone-900">Ayurvedic Pharmacy Finder</h3>
                <p className="text-stone-500 text-sm">
                  Locate pharmacies nearby using coordinates mapping. The query auto-expands search scope.
                </p>
              </div>
              <div className="flex flex-col sm:flex-row gap-3 w-full sm:w-auto">
                <button
                  onClick={() => setShowManualEntry(!showManualEntry)}
                  className="px-4 py-2.5 rounded-xl text-xs font-bold border border-stone-300 text-stone-600 hover:bg-stone-50 transition"
                >
                  {showManualEntry ? 'Hide Manual' : 'Enter Coordinates Manually'}
                </button>
                <button
                  onClick={() => handleFindShops()}
                  disabled={shopsLoading}
                  className="px-5 py-2.5 rounded-xl text-sm font-semibold text-white bg-emerald-700 hover:bg-emerald-800 disabled:opacity-50 disabled:pointer-events-none active:scale-95 transition shadow-md flex items-center justify-center gap-2"
                >
                  {shopsLoading ? (
                    <>
                      <Loader className="w-4 h-4 animate-spin" />
                      Searching GPS...
                    </>
                  ) : (
                    <>
                      <MapPin className="w-4 h-4" />
                      Find Near Me (GPS)
                    </>
                  )}
                </button>
              </div>
            </div>

            {showManualEntry && (
              <div className="p-5 bg-stone-50/50 border border-stone-200 rounded-2xl animate-in fade-in slide-in-from-top-4 duration-300">
                <h4 className="text-sm font-bold text-stone-800 mb-4">Manual Location Search</h4>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-stone-500 uppercase">Latitude</label>
                    <input 
                      type="number" 
                      step="any"
                      placeholder="e.g. 18.5204"
                      value={manualLat}
                      onChange={(e) => setManualLat(e.target.value)}
                      className="w-full px-3 py-2 border border-stone-300 rounded-xl bg-white text-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600 outline-none transition"
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-[10px] font-bold text-stone-500 uppercase">Longitude</label>
                    <input 
                      type="number" 
                      step="any"
                      placeholder="e.g. 73.8567"
                      value={manualLon}
                      onChange={(e) => setManualLon(e.target.value)}
                      className="w-full px-3 py-2 border border-stone-300 rounded-xl bg-white text-sm focus:ring-2 focus:ring-emerald-500/20 focus:border-emerald-600 outline-none transition"
                    />
                  </div>
                  <div className="flex items-end">
                    <button
                      onClick={() => handleFindShops({ lat: parseFloat(manualLat), lon: parseFloat(manualLon) })}
                      disabled={!manualLat || !manualLon || shopsLoading}
                      className="w-full py-2.5 rounded-xl text-xs font-bold text-emerald-800 bg-emerald-50 border border-emerald-200 hover:bg-emerald-100 transition disabled:opacity-50"
                    >
                      Search coordinates
                    </button>
                  </div>
                </div>
              </div>
            )}

            {shopsError && (
              <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 flex items-start gap-3 text-rose-800 text-sm">
                <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
                <div>{shopsError}</div>
              </div>
            )}

            {shopsMessage && (
              <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-250 flex items-start gap-3 text-emerald-800 text-sm">
                <CheckCircle className="w-5 h-5 shrink-0 mt-0.5" />
                <div>{shopsMessage}</div>
              </div>
            )}

            {shops.length > 0 ? (
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {shops.map((shop, idx) => (
                  <div key={idx} className="bg-white border border-stone-200 rounded-2xl shadow-sm hover:shadow-md transition-all overflow-hidden flex flex-col group">
                    {/* Map Preview Area */}
                    <div className="h-40 w-full bg-stone-100 relative overflow-hidden border-b border-stone-100">
                      <iframe
                        width="100%"
                        height="100%"
                        style={{ border: 0, opacity: 0.85 }}
                        loading="lazy"
                        allowFullScreen
                        referrerPolicy="no-referrer-when-downgrade"
                        src={`https://maps.google.com/maps?q=${shop.latitude},${shop.longitude}&z=15&output=embed`}
                        title={`Map for ${shop.name}`}
                        className="group-hover:opacity-100 transition-opacity"
                      ></iframe>
                    </div>

                    <div className="p-5 flex flex-col flex-1 justify-between gap-4">
                      <div className="space-y-2">
                        <h4 className="font-bold text-stone-900 text-base leading-snug group-hover:text-emerald-800 transition-colors">
                          {shop.name || 'Ayurvedic Pharmacy'}
                        </h4>
                        <p className="text-xs text-stone-500 flex items-start gap-1">
                          <MapPin className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                          <span>{shop.address || 'Address not listed'}</span>
                        </p>
                        <div className="flex items-center justify-between pt-1">
                          <span className="text-[10px] bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded-md font-bold border border-emerald-100">
                            {shop.distance}
                          </span>
                        </div>
                      </div>

                      <div className="flex flex-col gap-2">
                        <a
                          href={shop.maps_link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="w-full flex items-center justify-center gap-1.5 py-2.5 bg-white border border-stone-200 hover:border-emerald-600 rounded-xl text-xs font-semibold text-stone-700 hover:text-emerald-850 hover:bg-emerald-50/10 transition shadow-sm"
                        >
                          <MapPin className="w-4 h-4 text-emerald-700" />
                          Directions
                        </a>
                        
                        {shop.phone && (
                          <a
                            href={`tel:${shop.phone}`}
                            className="w-full flex items-center justify-center gap-1.5 py-2.5 bg-white border border-stone-200 hover:border-emerald-600 rounded-xl text-xs font-semibold text-stone-700 hover:text-emerald-850 hover:bg-emerald-50/10 transition shadow-sm"
                          >
                            <Phone className="w-4 h-4 text-emerald-700" />
                            Call ({shop.phone})
                          </a>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              !shopsLoading && !shopsError && (
                <div className="text-center p-16 bg-stone-50/30 border border-dashed border-stone-200 rounded-2xl">
                  <div className="w-16 h-16 bg-white rounded-full shadow-sm flex items-center justify-center mx-auto mb-4 border border-stone-100">
                    <MapPin className="w-8 h-8 text-stone-300" />
                  </div>
                  <h4 className="font-bold text-stone-800">Locate Pharmacies</h4>
                  <p className="text-stone-500 text-sm mt-1 max-w-xs mx-auto">
                    Use your device GPS or enter coordinates to find the nearest Ayurvedic medical stores.
                  </p>
                </div>
              )
            )}
          </div>
        )}

      </div>

      {/* PLAN DETAIL MODAL */}
      {selectedPlanDetail && (
        <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white border border-stone-200 rounded-2xl shadow-xl w-full max-w-4xl max-h-[85vh] overflow-y-auto p-6 sm:p-8 relative space-y-6">
            <button
              onClick={() => setSelectedPlanDetail(null)}
              className="absolute top-4 right-4 bg-stone-100 hover:bg-stone-200 text-stone-600 rounded-full p-2 transition text-sm font-bold shadow-sm"
            >
              ✕
            </button>

            <div className="text-center space-y-3 pt-2">
              <h3 className="text-2xl font-bold text-stone-900">{selectedPlanDetail.title}</h3>
              <p className="text-stone-500 text-sm max-w-xl mx-auto">{selectedPlanDetail.overview}</p>
              
              <div className="flex justify-center gap-2 pt-1.5">
                <span className="bg-emerald-50 text-emerald-800 text-xs font-semibold px-3 py-1 rounded-full border border-emerald-100 flex items-center gap-1">
                  <Leaf className="w-3.5 h-3.5" />
                  Dosha: {selectedPlanDetail.dosha_focus}
                </span>
                {selectedPlanDetail.is_doctor_vetted ? (
                  <span className="bg-emerald-100 text-emerald-900 text-xs font-bold px-3 py-1 rounded-full border border-emerald-200 flex items-center gap-1">
                    <CheckCircle className="w-3.5 h-3.5 text-emerald-800" />
                    Vetted by Dr. {selectedPlanDetail.doctor_name}
                  </span>
                ) : (
                  <span className="bg-amber-50 text-amber-800 text-xs font-semibold px-3 py-1 rounded-full border border-amber-100 flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5 text-amber-750" />
                    Pending Doctor Review
                  </span>
                )}
              </div>
            </div>

            {/* Personalized notes */}
            {selectedPlanDetail.personalization_notes?.length > 0 && (
              <div className="p-4 bg-amber-50/40 border border-amber-200/50 rounded-xl space-y-1">
                <h4 className="text-xs font-bold text-amber-850 uppercase tracking-wider">Applied Personalizations:</h4>
                <ul className="list-disc list-inside text-xs text-stone-600 space-y-1">
                  {selectedPlanDetail.personalization_notes.map((note, idx) => (
                    <li key={idx}>{note}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Doctor Vetting Notes */}
            {selectedPlanDetail.is_doctor_vetted && selectedPlanDetail.doctor_notes && (
              <div className="p-4 bg-emerald-50/30 border border-emerald-250/30 rounded-xl space-y-1">
                <h4 className="text-xs font-bold text-emerald-950 uppercase tracking-wider">Clinical Vetting Notes:</h4>
                <p className="text-xs italic text-stone-600">{selectedPlanDetail.doctor_notes}</p>
              </div>
            )}

            {/* Days schedules */}
            <div className="space-y-4">
              <h4 className="text-base font-bold text-stone-900 border-b pb-2">Routine Log</h4>
              <div className="space-y-5">
                {selectedPlanDetail.days.map((dayPlan) => (
                  <div key={dayPlan.day} className="border border-stone-200 rounded-xl overflow-hidden bg-white">
                    {/* Day Header */}
                    <div className="bg-stone-50 border-b border-stone-200 px-4 py-2.5 flex items-center gap-3">
                      <span className="bg-emerald-700 text-white text-[10px] font-bold px-2 py-0.5 rounded-full">Day {dayPlan.day}</span>
                      <h5 className="font-bold text-stone-800 text-xs">{dayPlan.theme}</h5>
                    </div>
                    <div className="p-4 grid grid-cols-1 sm:grid-cols-2 gap-4 text-[11px]">

                      {/* Morning Block */}
                      <div className="space-y-2">
                        <span className="font-bold text-emerald-700 block">🌅 Morning ({dayPlan.morning.time})</span>
                        <div>
                          <p className="font-semibold text-stone-500 text-[9px] uppercase tracking-wide mb-0.5">Routine</p>
                          <ul className="list-disc list-inside space-y-0.5 text-stone-700 leading-relaxed">
                            {dayPlan.morning.routine.map((r, i) => <li key={i}>{r}</li>)}
                          </ul>
                        </div>
                        {dayPlan.morning.ingredients?.length > 0 && (
                          <div>
                            <p className="font-semibold text-stone-500 text-[9px] uppercase tracking-wide mb-0.5">Ingredients</p>
                            <p className="text-stone-500">{dayPlan.morning.ingredients.join(', ')}</p>
                          </div>
                        )}
                        {dayPlan.morning.procedure?.length > 0 && (
                          <div>
                            <p className="font-semibold text-stone-500 text-[9px] uppercase tracking-wide mb-0.5">Step-by-Step</p>
                            <ol className="space-y-1 text-stone-700 leading-relaxed">
                              {dayPlan.morning.procedure.map((step, i) => (
                                <li key={i}>{step}</li>
                              ))}
                            </ol>
                          </div>
                        )}
                      </div>

                      {/* Evening Block */}
                      <div className="space-y-2">
                        <span className="font-bold text-indigo-700 block">🌌 Evening ({dayPlan.evening.time})</span>
                        <div>
                          <p className="font-semibold text-stone-500 text-[9px] uppercase tracking-wide mb-0.5">Routine</p>
                          <ul className="list-disc list-inside space-y-0.5 text-stone-700 leading-relaxed">
                            {dayPlan.evening.routine.map((r, i) => <li key={i}>{r}</li>)}
                          </ul>
                        </div>
                        {dayPlan.evening.ingredients?.length > 0 && (
                          <div>
                            <p className="font-semibold text-stone-500 text-[9px] uppercase tracking-wide mb-0.5">Ingredients</p>
                            <p className="text-stone-500">{dayPlan.evening.ingredients.join(', ')}</p>
                          </div>
                        )}
                        {dayPlan.evening.procedure?.length > 0 && (
                          <div>
                            <p className="font-semibold text-stone-500 text-[9px] uppercase tracking-wide mb-0.5">Step-by-Step</p>
                            <ol className="space-y-1 text-stone-700 leading-relaxed">
                              {dayPlan.evening.procedure.map((step, i) => (
                                <li key={i}>{step}</li>
                              ))}
                            </ol>
                          </div>
                        )}
                      </div>

                      {/* Diet Block */}
                      <div className="sm:col-span-2 border-t pt-3 space-y-2">
                        <span className="font-bold text-amber-700 block">🍽️ Diet</span>
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                          <div><p className="text-[9px] font-semibold text-stone-500 uppercase">Breakfast</p><p className="text-stone-700 mt-0.5">{dayPlan.diet.breakfast}</p></div>
                          <div><p className="text-[9px] font-semibold text-stone-500 uppercase">Lunch</p><p className="text-stone-700 mt-0.5">{dayPlan.diet.lunch}</p></div>
                          <div><p className="text-[9px] font-semibold text-stone-500 uppercase">Dinner</p><p className="text-stone-700 mt-0.5">{dayPlan.diet.dinner}</p></div>
                          {dayPlan.diet.drinks?.length > 0 && (
                            <div><p className="text-[9px] font-semibold text-stone-500 uppercase">Drinks</p><p className="text-stone-700 mt-0.5">{dayPlan.diet.drinks.join(', ')}</p></div>
                          )}
                        </div>
                        {dayPlan.diet.avoid?.length > 0 && (
                          <div>
                            <p className="text-[9px] font-semibold text-rose-700 uppercase mb-0.5">❌ Avoid</p>
                            <p className="text-stone-600">{dayPlan.diet.avoid.join(', ')}</p>
                          </div>
                        )}
                      </div>

                      {/* Yoga + Tip */}
                      <div className="sm:col-span-2 grid grid-cols-1 sm:grid-cols-2 gap-3 border-t pt-3">
                        <div className="bg-stone-50 rounded-lg p-3">
                          <span className="font-semibold text-stone-800 text-[10px] block mb-1">🧘 Yoga / Pranayama</span>
                          <p className="text-stone-700">{dayPlan.yoga}</p>
                        </div>
                        <div className="bg-emerald-50/40 border border-emerald-100 rounded-lg p-3">
                          <span className="font-semibold text-emerald-900 text-[10px] block mb-1">💡 Day Tip</span>
                          <p className="italic text-stone-600">{dayPlan.tip}</p>
                        </div>
                      </div>

                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Weekly summary */}
            {selectedPlanDetail.weekly_summary && (
              <div className="border border-stone-200 rounded-xl p-5 bg-stone-50/50 text-xs space-y-3">
                <h4 className="text-sm font-bold text-stone-900 border-b pb-1.5">Weekly Treatment Summary</h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div className="space-y-1">
                    <span className="font-bold text-emerald-800">Key Ingredients:</span>
                    <p className="text-stone-600">{selectedPlanDetail.weekly_summary.key_ingredients.join(', ')}</p>
                  </div>
                  <div className="space-y-1">
                    <span className="font-bold text-stone-850">Expected Results:</span>
                    <p className="text-stone-600">{selectedPlanDetail.weekly_summary.expected_results}</p>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

    </div>
  );
};

export default PatientDashboard;
