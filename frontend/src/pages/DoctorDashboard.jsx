import React, { useState, useEffect } from 'react';
import api from '../services/api';
import { useAuth } from '../context/AuthContext';
import { 
  FileText, CheckCircle, Clock, Loader, AlertCircle, Edit, Save, 
  ArrowLeft, ListFilter, ClipboardList, Info 
} from 'lucide-react';

const DoctorDashboard = () => {
  const { user } = useAuth();
  
  // Dashboard tabs
  const [activeTab, setActiveTab] = useState('unchecked'); // 'unchecked' | 'reviewed'

  // Data state
  const [uncheckedPlans, setUncheckedPlans] = useState([]);
  const [reviewedPlans, setReviewedPlans] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Selected plan editing workspace state
  const [editingPlan, setEditingPlan] = useState(null);
  const [doctorNotes, setDoctorNotes] = useState('');
  const [saveLoading, setSaveLoading] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState('');
  const [saveError, setSaveError] = useState('');

  useEffect(() => {
    fetchPlans();
  }, [activeTab]);

  const fetchPlans = async () => {
    setLoading(true);
    setError('');
    try {
      if (activeTab === 'unchecked') {
        const response = await api.get('/plan/unchecked-plans');
        setUncheckedPlans(response.data);
      } else {
        const response = await api.get('/plan/reviewed-plans');
        setReviewedPlans(response.data);
      }
    } catch (err) {
      console.error(err);
      setError(
        err.response?.data?.detail || 'Failed to fetch patient plans. Access might be restricted.'
      );
    } finally {
      setLoading(false);
    }
  };

  // Open plan in doctor editor
  const handleStartReview = (plan) => {
    // Create a deep copy of the plan to prevent mutation side-effects in states
    setEditingPlan(JSON.parse(JSON.stringify(plan)));
    setDoctorNotes(plan.doctor_notes || '');
    setSaveSuccess('');
    setSaveError('');
  };

  // Bind day-level input changes
  const handleDayFieldChange = (dayIndex, section, field, value) => {
    setEditingPlan(prev => {
      const updated = JSON.parse(JSON.stringify(prev));
      if (section === 'diet') {
        updated.days[dayIndex].diet[field] = value;
      } else if (section === 'morning' || section === 'evening') {
        if (field === 'time') {
          // Time is a plain string, not a list
          updated.days[dayIndex][section].time = value;
        } else {
          // Splitting comma strings back to lists
          const listVal = value.split(',').map(s => s.trim()).filter(Boolean);
          updated.days[dayIndex][section][field] = listVal;
        }
      } else if (section === 'yoga') {
        // yoga is a string in the backend schema
        updated.days[dayIndex].yoga = value;
      } else {
        updated.days[dayIndex][field] = value;
      }
      return updated;
    });
  };

  // Bind weekly summary fields
  const handleSummaryFieldChange = (field, value) => {
    setEditingPlan(prev => {
      const updated = JSON.parse(JSON.stringify(prev));
      if (field === 'key_ingredients') {
        const listVal = value.split(',').map(s => s.trim()).filter(Boolean);
        updated.weekly_summary.key_ingredients = listVal;
      } else {
        updated.weekly_summary[field] = value;
      }
      return updated;
    });
  };

  // Submit reviewed / modified plan
  const handleSubmitReview = async () => {
    if (!editingPlan) return;

    setSaveLoading(true);
    setSaveSuccess('');
    setSaveError('');

    try {
      // ── SENSITIVE DATA CLEANUP FOR MODIFIED PLAN ──
      const cleanedModifiedPlan = JSON.parse(JSON.stringify(editingPlan));
      
      // Clean up properties that doctor shouldn't modify directly in nested fields
      delete cleanedModifiedPlan.id;
      delete cleanedModifiedPlan.user_id;
      delete cleanedModifiedPlan.prediction_id;
      delete cleanedModifiedPlan.created_at;

      const payload = {
        is_doctor_vetted: true,
        doctor_notes: doctorNotes,
        modified_plan: cleanedModifiedPlan
      };

      const response = await api.patch(`/plan/${editingPlan.id}/review`, payload);
      
      setSaveSuccess('Patient treatment plan vetted and updated successfully!');
      
      // Refresh backend list
      fetchPlans();
      
      // Exit editor after a short delay
      setTimeout(() => {
        setEditingPlan(null);
      }, 1500);

    } catch (err) {
      console.error(err);
      setSaveError(
        err.response?.data?.detail || 'Vetting submission failed. Verify Plan ID and inputs.'
      );
    } finally {
      setSaveLoading(false);
    }
  };

  // Render main plans queue list
  const renderPlansList = (plans) => {
    if (plans.length === 0) {
      return (
        <div className="text-center p-12 bg-white border border-stone-200 rounded-2xl">
          <ClipboardList className="w-12 h-12 text-stone-300 mx-auto mb-3" />
          <h4 className="font-semibold text-stone-850">Queue Empty</h4>
          <p className="text-stone-400 text-xs mt-1">No patient files are currently pending review in this group.</p>
        </div>
      );
    }

    return (
      <div className="bg-white border border-stone-200 rounded-2xl shadow-sm overflow-hidden">
        <table className="min-w-full divide-y divide-stone-200 text-left text-sm">
          <thead className="bg-stone-50 text-stone-500 text-xs uppercase font-bold">
            <tr>
              <th className="px-6 py-3">Created Date</th>
              <th className="px-6 py-3">Patient ID / Reference</th>
              <th className="px-6 py-3">Treatment Plan Title</th>
              <th className="px-6 py-3">Dosha Focus</th>
              <th className="px-6 py-3 text-right">Action</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-stone-200 text-stone-700">
            {plans.map((plan) => (
              <tr key={plan.id} className="hover:bg-stone-50/50">
                <td className="px-6 py-4 whitespace-nowrap text-xs text-stone-400">
                  {new Date(plan.created_at).toLocaleString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap font-medium text-stone-850">
                  Patient Profile File
                </td>
                <td className="px-6 py-4 font-semibold text-stone-900">
                  {plan.title}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-xs">
                  <span className="bg-emerald-50 text-emerald-800 border border-emerald-100 font-semibold px-2 py-0.5 rounded-full">
                    {plan.dosha_focus}
                  </span>
                </td>
                <td className="px-6 py-4 text-right whitespace-nowrap">
                  <button
                    onClick={() => handleStartReview(plan)}
                    className="inline-flex items-center gap-1 text-xs font-semibold bg-emerald-700 text-white px-3.5 py-2 rounded-lg hover:bg-emerald-800 transition active:scale-95 shadow-sm"
                  >
                    <Edit className="w-3.5 h-3.5" />
                    Review & Edit
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-stone-50 pt-16 pb-12">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        
        {/* If in edit panel */}
        {editingPlan ? (
          <div className="space-y-6 mt-6">
            {/* Header / Back */}
            <div className="flex items-center justify-between">
              <button
                onClick={() => setEditingPlan(null)}
                className="flex items-center gap-1 text-sm font-semibold text-stone-600 hover:text-emerald-800 transition"
              >
                <ArrowLeft className="w-4 h-4" />
                Back to Patient Queue
              </button>
              <span className="text-xs bg-amber-50 border border-amber-200 text-amber-800 px-3 py-1 rounded-full font-semibold animate-pulse">
                Medically Editing: {editingPlan.title}
              </span>
            </div>

            {/* Editing workspace */}
            <div className="bg-white border border-stone-200 rounded-2xl shadow-sm p-6 sm:p-8 space-y-8">
              
              {/* Doctor Review Header Info */}
              <div className="border-b pb-4 space-y-2">
                <h2 className="text-2xl font-bold text-stone-900">Treatment Plan Customizer</h2>
                <p className="text-stone-500 text-sm">
                  You are reviewing this system generated plan. Feel free to refine diet regimens, physical postures, or routines to fit patient history.
                </p>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-2 text-xs">
                  <div>
                    <span className="text-stone-400 block font-semibold">Dosha Focus</span>
                    <span className="font-bold text-stone-700">{editingPlan.dosha_focus}</span>
                  </div>
                  <div>
                    <span className="text-stone-400 block font-semibold">Specialty Target</span>
                    <span className="font-bold text-stone-700">{editingPlan.required_specialty}</span>
                  </div>
                  <div>
                    <span className="text-stone-400 block font-semibold">Skin Personalization Notes</span>
                    <span className="font-bold text-stone-750 block truncate max-w-[200px]" title={editingPlan.personalization_notes?.join(', ')}>
                      {editingPlan.personalization_notes?.join(', ') || 'None'}
                    </span>
                  </div>
                </div>
              </div>
              
              {/* Patient Profile Disclosure Section (New) */}
              {editingPlan.patient_metadata && (
                <div className="bg-stone-50 border border-stone-200 rounded-2xl p-6 space-y-4 shadow-sm">
                  <div className="flex items-center gap-2 border-b border-stone-200 pb-3">
                    <div className="bg-emerald-100 p-1.5 rounded-lg">
                      <Info className="w-5 h-5 text-emerald-800" />
                    </div>
                    <div>
                      <h4 className="font-bold text-stone-900 text-base">Patient Medical Profile</h4>
                      <p className="text-[10px] text-stone-400 font-semibold uppercase tracking-wider">Assessment Data from Generation</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 md:grid-cols-5 gap-6">
                    <div>
                      <span className="text-[10px] uppercase font-bold text-stone-400 block mb-1">Patient Name</span>
                      <p className="text-sm font-bold text-emerald-900 px-3 py-2 bg-white border border-stone-200 rounded-xl truncate" title={editingPlan.patient_metadata.full_name}>
                        {editingPlan.patient_metadata.full_name}
                      </p>
                    </div>
                    <div>
                      <span className="text-[10px] uppercase font-bold text-stone-400 block mb-1">Age Bracket</span>
                      <p className="text-sm font-bold text-stone-850 px-3 py-2 bg-white border border-stone-200 rounded-xl">{editingPlan.patient_metadata.age_group}</p>
                    </div>
                    <div>
                      <span className="text-[10px] uppercase font-bold text-stone-400 block mb-1">Dermal Type</span>
                      <p className="text-sm font-bold text-stone-850 px-3 py-2 bg-white border border-stone-200 rounded-xl capitalize">{editingPlan.patient_metadata.skin_type}</p>
                    </div>
                    <div className="col-span-1 md:col-span-2">
                      <span className="text-[10px] uppercase font-bold text-stone-400 block mb-1">Lifestyle Factors</span>
                      <div className="flex flex-wrap gap-1.5 p-1.5 bg-white border border-stone-200 rounded-xl min-h-[42px]">
                        {editingPlan.patient_metadata.lifestyle?.length > 0 ? (
                          editingPlan.patient_metadata.lifestyle.map((l, i) => (
                            <span key={i} className="text-[10px] bg-stone-100 text-stone-700 px-2 py-1 rounded-lg font-bold capitalize">
                              {l.replace('_', ' ')}
                            </span>
                          ))
                        ) : (
                          <span className="text-[10px] text-stone-300 italic p-1">No factors listed</span>
                        )}
                      </div>
                    </div>
                  </div>
                  
                  <div className="pt-4 border-t border-stone-200">
                    <span className="text-[10px] uppercase font-bold text-stone-400 block mb-3">Assessment Answer Key (Dosha Analysis)</span>
                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
                      {Object.entries(editingPlan.patient_metadata.dosha_answers).map(([key, val]) => (
                        <div key={key} className="bg-white border border-stone-100 p-2.5 rounded-xl shadow-[0_2px_4px_rgba(0,0,0,0.02)]">
                          <span className="text-[9px] text-stone-400 block font-bold uppercase mb-1">{key.replace('_', ' ')}</span>
                          <span className="text-xs font-bold text-emerald-900 capitalize">{val.replace('_', ' ')}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* Editable Days loop */}
              <div className="space-y-6">
                <h3 className="text-lg font-bold text-stone-900">1. Modify Daily Schedules (7 Days)</h3>
                
                <div className="space-y-6">
                  {(editingPlan.days || []).map((dayPlan, dIdx) => (
                    <div key={dayPlan.day} className="border border-stone-200 rounded-2xl p-6 bg-stone-50/20 space-y-4">
                      <div className="flex flex-col sm:flex-row justify-between border-b pb-2 gap-2">
                        <span className="font-bold text-emerald-800 text-sm uppercase">Day {dayPlan.day} Customizer</span>
                        <div className="flex items-center gap-2">
                          <label className="text-xs font-semibold text-stone-500">Theme/Focus:</label>
                          <input
                            type="text"
                            value={dayPlan.theme}
                            onChange={(e) => handleDayFieldChange(dIdx, 'day', 'theme', e.target.value)}
                            className="px-2 py-1 border border-stone-300 rounded bg-white text-xs font-semibold text-stone-800 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                          />
                        </div>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                        {/* Morning Routine Column */}
                        <div className="space-y-3">
                          <h5 className="font-bold text-xs text-stone-400 uppercase tracking-wider">🌅 Morning Routine</h5>
                          <div>
                            <label className="block text-[10px] font-semibold text-stone-500 mb-0.5">Time Slot</label>
                            <input
                              type="text"
                              value={dayPlan.morning.time}
                              onChange={(e) => handleDayFieldChange(dIdx, 'morning', 'time', e.target.value)}
                              className="w-full px-2.5 py-1.5 border border-stone-300 rounded bg-white text-xs focus:outline-none focus:ring-1 focus:ring-emerald-500"
                            />
                          </div>
                          <div>
                            <label className="block text-[10px] font-semibold text-stone-500 mb-0.5">Routines (Comma-separated)</label>
                            <textarea
                              rows="2"
                              value={dayPlan.morning.routine.join(', ')}
                              onChange={(e) => handleDayFieldChange(dIdx, 'morning', 'routine', e.target.value)}
                              className="w-full px-2.5 py-1.5 border border-stone-300 rounded bg-white text-xs focus:outline-none focus:ring-1 focus:ring-emerald-500"
                            />
                          </div>
                          <div>
                            <label className="block text-[10px] font-semibold text-stone-500 mb-0.5">Ingredients (Comma-separated)</label>
                            <input
                              type="text"
                              value={dayPlan.morning.ingredients.join(', ')}
                              onChange={(e) => handleDayFieldChange(dIdx, 'morning', 'ingredients', e.target.value)}
                              className="w-full px-2.5 py-1.5 border border-stone-300 rounded bg-white text-xs focus:outline-none focus:ring-1 focus:ring-emerald-500"
                            />
                          </div>
                        </div>

                        {/* Diet Column */}
                        <div className="space-y-3">
                          <h5 className="font-bold text-xs text-stone-400 uppercase tracking-wider">🍽️ Diet Directives</h5>
                          <div>
                            <label className="block text-[10px] font-semibold text-stone-500 mb-0.5">Breakfast</label>
                            <input
                              type="text"
                              value={dayPlan.diet.breakfast}
                              onChange={(e) => handleDayFieldChange(dIdx, 'diet', 'breakfast', e.target.value)}
                              className="w-full px-2.5 py-1.5 border border-stone-300 rounded bg-white text-xs focus:outline-none focus:ring-1 focus:ring-emerald-500"
                            />
                          </div>
                          <div>
                            <label className="block text-[10px] font-semibold text-stone-500 mb-0.5">Lunch</label>
                            <input
                              type="text"
                              value={dayPlan.diet.lunch}
                              onChange={(e) => handleDayFieldChange(dIdx, 'diet', 'lunch', e.target.value)}
                              className="w-full px-2.5 py-1.5 border border-stone-300 rounded bg-white text-xs focus:outline-none focus:ring-1 focus:ring-emerald-500"
                            />
                          </div>
                          <div>
                            <label className="block text-[10px] font-semibold text-stone-500 mb-0.5">Dinner</label>
                            <input
                              type="text"
                              value={dayPlan.diet.dinner}
                              onChange={(e) => handleDayFieldChange(dIdx, 'diet', 'dinner', e.target.value)}
                              className="w-full px-2.5 py-1.5 border border-stone-300 rounded bg-white text-xs focus:outline-none focus:ring-1 focus:ring-emerald-500"
                            />
                          </div>
                        </div>

                        {/* Evening, Yoga & Tips Column */}
                        <div className="space-y-3">
                          <h5 className="font-bold text-xs text-stone-400 uppercase tracking-wider">🌌 Evening & Physical</h5>
                          <div>
                            <label className="block text-[10px] font-semibold text-stone-500 mb-0.5">Evening Routines (Comma-separated)</label>
                            <textarea
                              rows="1"
                              value={dayPlan.evening.routine.join(', ')}
                              onChange={(e) => handleDayFieldChange(dIdx, 'evening', 'routine', e.target.value)}
                              className="w-full px-2.5 py-1.5 border border-stone-300 rounded bg-white text-xs focus:outline-none focus:ring-1 focus:ring-emerald-500"
                            />
                          </div>
                          <div>
                            <label className="block text-[10px] font-semibold text-stone-500 mb-0.5">Yoga Asanas (Comma-separated)</label>
                            <input
                              type="text"
                              value={dayPlan.yoga || ''}
                              onChange={(e) => handleDayFieldChange(dIdx, 'yoga', null, e.target.value)}
                              className="w-full px-2.5 py-1.5 border border-stone-300 rounded bg-white text-xs focus:outline-none focus:ring-1 focus:ring-emerald-500"
                            />
                          </div>
                          <div>
                            <label className="block text-[10px] font-semibold text-stone-500 mb-0.5">Daily Tip</label>
                            <input
                              type="text"
                              value={dayPlan.tip}
                              onChange={(e) => handleDayFieldChange(dIdx, 'day', 'tip', e.target.value)}
                              className="w-full px-2.5 py-1.5 border border-stone-300 rounded bg-white text-xs focus:outline-none focus:ring-1 focus:ring-emerald-500"
                            />
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Weekly Summary edit */}
              <div className="space-y-4 border-t pt-6">
                <h3 className="text-lg font-bold text-stone-900">2. Modify Weekly Summary</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs font-semibold text-stone-750 mb-1">Key Ingredients (Comma-separated)</label>
                    <textarea
                      rows="2"
                      value={(editingPlan.weekly_summary?.key_ingredients || []).join(', ')}
                      onChange={(e) => handleSummaryFieldChange('key_ingredients', e.target.value)}
                      className="w-full px-3 py-2 border border-stone-300 rounded-xl bg-white text-sm focus:outline-none focus:ring-1 focus:ring-emerald-500"
                    />
                  </div>
                  <div>
                    <label className="block text-xs font-semibold text-stone-750 mb-1">Expected Results</label>
                    <textarea
                      rows="2"
                      value={editingPlan.weekly_summary?.expected_results || ''}
                      onChange={(e) => handleSummaryFieldChange('expected_results', e.target.value)}
                      className="w-full px-3 py-2 border border-stone-300 rounded-xl bg-white text-sm focus:outline-none focus:ring-1 focus:ring-emerald-500"
                    />
                  </div>
                </div>
              </div>

              {/* Doctor Annotation Textarea */}
              <div className="space-y-3 border-t pt-6">
                <h3 className="text-lg font-bold text-stone-900">3. Vetting Signature & Annotations</h3>
                <div>
                  <label htmlFor="doctorNotes" className="block text-sm font-semibold text-stone-700 mb-1">
                    Clinical Vetting Notes (Visible to Patient)
                  </label>
                  <textarea
                    id="doctorNotes"
                    rows="4"
                    value={doctorNotes}
                    onChange={(e) => setDoctorNotes(e.target.value)}
                    placeholder="Enter patient dietary restrictions, custom usage advisories, or warnings..."
                    className="w-full px-3 py-3 border border-stone-300 rounded-xl bg-stone-50/50 text-stone-950 placeholder-stone-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent text-sm"
                  />
                </div>
              </div>

              {/* Status and submit */}
              {saveSuccess && (
                <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 flex items-start gap-3 text-emerald-800 text-sm">
                  <CheckCircle className="w-5 h-5 shrink-0 mt-0.5" />
                  <div>{saveSuccess}</div>
                </div>
              )}

              {saveError && (
                <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 flex items-start gap-3 text-rose-800 text-sm">
                  <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
                  <div>{saveError}</div>
                </div>
              )}

              <div className="flex gap-4 border-t pt-6 justify-end">
                <button
                  onClick={() => setEditingPlan(null)}
                  className="px-6 py-3 border border-stone-300 rounded-xl text-sm font-semibold text-stone-755 hover:bg-stone-50 transition active:scale-95"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSubmitReview}
                  disabled={saveLoading}
                  className="px-8 py-3 rounded-xl text-sm font-semibold text-white bg-emerald-700 hover:bg-emerald-800 active:scale-95 transition shadow-md flex items-center gap-2 disabled:opacity-50"
                >
                  {saveLoading ? (
                    <>
                      <Loader className="w-4 h-4 animate-spin" />
                      Saving Medical Review...
                    </>
                  ) : (
                    <>
                      <Save className="w-4 h-4" />
                      Approve & Save Vetted Plan
                    </>
                  )}
                </button>
              </div>

            </div>
          </div>
        ) : (
          <div className="space-y-6 mt-6">
            
            {/* Welcome banner doctor */}
            <div className="bg-white border border-stone-200 p-6 sm:p-8 rounded-2xl shadow-sm flex flex-col md:flex-row md:items-center md:justify-between gap-4">
              <div className="space-y-1">
                <h1 className="text-3xl font-bold tracking-tight text-stone-900">
                  Welcome, <span className="text-emerald-755">{user?.full_name}</span>
                </h1>
                <p className="text-stone-500 text-sm">
                  Vetting area. You are currently viewing plans filtered by your specialization:{' '}
                  <span className="font-bold underline text-emerald-800">{user?.specialization}</span>.
                </p>
              </div>
              <div className="bg-emerald-65 bg-emerald-50 border border-emerald-100 px-4 py-3 rounded-xl flex items-center gap-3 self-start md:self-center">
                <ClipboardList className="w-6 h-6 text-emerald-850 shrink-0" />
                <div className="text-xs text-stone-700">
                  <span className="font-semibold block text-emerald-900">Specialty Domain</span>
                  {user?.specialization} practitioner
                </div>
              </div>
            </div>

            {/* Doctor Tabs */}
            <div className="flex border-b border-stone-200 gap-6">
              <button
                onClick={() => setActiveTab('unchecked')}
                className={`pb-4 text-sm font-semibold border-b-2 transition-colors flex items-center gap-1.5 ${
                  activeTab === 'unchecked'
                    ? 'border-emerald-600 text-emerald-800 font-bold'
                    : 'border-transparent text-stone-500 hover:text-stone-700'
                }`}
              >
                <Clock className="w-4 h-4" />
                Unchecked Plans Waiting Vetting ({uncheckedPlans.length})
              </button>
              <button
                onClick={() => setActiveTab('reviewed')}
                className={`pb-4 text-sm font-semibold border-b-2 transition-colors flex items-center gap-1.5 ${
                  activeTab === 'reviewed'
                    ? 'border-emerald-600 text-emerald-800 font-bold'
                    : 'border-transparent text-stone-500 hover:text-stone-700'
                }`}
              >
                <CheckCircle className="w-4 h-4" />
                Reviewed Plans Log ({reviewedPlans.length})
              </button>
            </div>

            {/* Error notifications */}
            {error && (
              <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 flex items-start gap-3 text-rose-800 text-sm">
                <AlertCircle className="w-5 h-5 shrink-0 mt-0.5" />
                <div>{error}</div>
              </div>
            )}

            {/* Render items based on status */}
            {loading ? (
              <div className="flex justify-center py-12">
                <Loader className="w-8 h-8 animate-spin text-stone-400" />
              </div>
            ) : activeTab === 'unchecked' ? (
              renderPlansList(uncheckedPlans)
            ) : (
              renderPlansList(reviewedPlans)
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default DoctorDashboard;
