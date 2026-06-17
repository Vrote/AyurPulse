import React, { useState, useRef, useEffect } from 'react';
import api from '../services/api';
import { 
  Send, 
  Bot, 
  User, 
  Leaf, 
  Loader2, 
  MessageSquare, 
  Sparkles, 
  Calendar, 
  ChevronRight, 
  RefreshCw 
} from 'lucide-react';

const ChatPage = () => {
  // Navigation & Mode States
  const [activeTab, setActiveTab] = useState('general'); // 'general' or 'plan'
  
  // Message Histories (Segregated)
  const [messages, setMessages] = useState([]); // Ask Anything (General)
  const [planMessages, setPlanMessages] = useState([]); // My Plan Chat
  
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  
  // My Plan Chat Specific States
  const [userPlans, setUserPlans] = useState([]);
  const [selectedPlanId, setSelectedPlanId] = useState(null);
  const [isPlansLoading, setIsPlansLoading] = useState(false);

  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, planMessages, isLoading]);

  useEffect(() => {
    if (activeTab === 'general' || (activeTab === 'plan' && selectedPlanId)) {
      inputRef.current?.focus();
    }
  }, [activeTab, selectedPlanId]);

  // Fetch plans when switching to the plan tab or when switching plan
  const fetchUserPlans = async () => {
    setIsPlansLoading(true);
    try {
      const response = await api.get('/chat/plans');
      setUserPlans(response.data);
    } catch (err) {
      console.error('Failed to fetch user plans for chat:', err);
    } finally {
      setIsPlansLoading(false);
    }
  };

  const handleTabChange = (tab) => {
    setActiveTab(tab);
    if (tab === 'plan') {
      fetchUserPlans();
    }
  };

  const handleSwitchPlan = () => {
    setSelectedPlanId(null);
    fetchUserPlans();
  };

  const generalSuggestions = [
    'What foods should I avoid for Pitta dosha?',
    'Which herbs help reduce acne?',
    'What is Vata dosha and its characteristics?',
    'How does Ashwagandha help with stress?',
    'What is Prakriti in Ayurveda?',
  ];

  const planSuggestions = [
    'Why was Neem recommended?',
    'Can I skip Aloe Vera Gel?',
    'What foods should I avoid while following this plan?',
    'What is the purpose of the evening routine?',
    'Can I replace this ingredient?',
    'Which part of the plan helps acne the most?',
  ];

  const suggestedQuestions = activeTab === 'general' ? generalSuggestions : planSuggestions;
  const activeMessages = activeTab === 'general' ? messages : planMessages;
  const activePlan = userPlans.find((p) => p.id === selectedPlanId);

  const handleSend = async (messageText) => {
    const text = (messageText || inputValue).trim();
    if (!text || isLoading) return;

    // Build the user message object
    const userMessage = { role: 'user', content: text, id: Date.now() };
    
    // Add immediately to local state based on active tab
    if (activeTab === 'general') {
      setMessages((prev) => [...prev, userMessage]);
    } else {
      setPlanMessages((prev) => [...prev, userMessage]);
    }
    
    setInputValue('');
    setIsLoading(true);

    try {
      const currentHistory = activeTab === 'general' ? messages : planMessages;
      
      const payload = {
        message: text,
        history: currentHistory.map((m) => ({ role: m.role, content: m.content })),
        chat_mode: activeTab,
      };

      if (activeTab === 'plan') {
        payload.plan_id = selectedPlanId;
      }

      const response = await api.post('/chat', payload);
      const { answer, sources } = response.data;

      const botMessage = {
        role: 'bot',
        content: answer,
        sources: sources || [],
        id: Date.now() + 1,
      };

      if (activeTab === 'general') {
        setMessages((prev) => [...prev, botMessage]);
      } else {
        setPlanMessages((prev) => [...prev, botMessage]);
      }
    } catch (err) {
      const errMsg =
        err?.response?.data?.detail ||
        'Something went wrong. Please try again.';
      
      const botErrorMessage = {
        role: 'bot',
        content: `⚠️ ${errMsg}`,
        sources: [],
        id: Date.now() + 1,
      };

      if (activeTab === 'general') {
        setMessages((prev) => [...prev, botErrorMessage]);
      } else {
        setPlanMessages((prev) => [...prev, botErrorMessage]);
      }
    } finally {
      setIsLoading(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-stone-50 via-emerald-50/30 to-teal-50/20 pt-16">
      {/* Header Banner */}
      <div className="flex-none bg-white/80 backdrop-blur-md border-b border-emerald-100 px-4 py-3 shadow-sm">
        <div className="max-w-3xl mx-auto space-y-3">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center shadow-lg shadow-emerald-500/30">
              <Bot className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-base font-bold text-stone-800 leading-tight">
                AyurBot
              </h1>
              <p className="text-xs text-emerald-600 font-medium">
                Your personal Ayurvedic wellness assistant
              </p>
            </div>
            <div className="ml-auto flex items-center gap-1.5 bg-emerald-50 border border-emerald-200 rounded-full px-3 py-1">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span className="text-xs font-semibold text-emerald-700">Online</span>
            </div>
          </div>
          
          {/* Tab Selector */}
          <div className="flex gap-2 p-1 bg-stone-100/80 rounded-xl border border-stone-200/50">
            <button
              onClick={() => handleTabChange('general')}
              className={`flex-1 flex items-center justify-center gap-2 py-2 text-xs font-semibold rounded-lg transition-all duration-300 ${
                activeTab === 'general'
                  ? 'bg-white text-emerald-700 shadow-sm border border-emerald-100'
                  : 'text-stone-500 hover:text-stone-800 hover:bg-stone-200/50'
              }`}
            >
              <MessageSquare className="w-3.5 h-3.5" />
              Ask Anything
            </button>
            <button
              onClick={() => handleTabChange('plan')}
              className={`flex-1 flex items-center justify-center gap-2 py-2 text-xs font-semibold rounded-lg transition-all duration-300 ${
                activeTab === 'plan'
                  ? 'bg-white text-emerald-700 shadow-sm border border-emerald-100'
                  : 'text-stone-500 hover:text-stone-800 hover:bg-stone-200/50'
              }`}
            >
              <Leaf className="w-3.5 h-3.5" />
              My Plan Chat
            </button>
          </div>
        </div>
      </div>

      {/* Plan Selector Interface */}
      {activeTab === 'plan' && !selectedPlanId ? (
        <div className="flex-1 overflow-y-auto px-4 py-8">
          <div className="max-w-2xl mx-auto space-y-6">
            <div className="text-center space-y-2 mb-4 animate-fadeIn">
              <h2 className="text-xl font-bold text-stone-800">
                Select a Plan to Chat About
              </h2>
              <p className="text-stone-500 text-sm">
                Choose one of your generated Ayurvedic plans to ask specific questions about diet, routines, ingredients, and recommendations.
              </p>
            </div>

            {isPlansLoading ? (
              <div className="flex flex-col items-center justify-center py-12 gap-3 animate-pulse">
                <Loader2 className="w-8 h-8 text-emerald-500 animate-spin" />
                <p className="text-sm text-stone-500 font-medium">Loading your plans...</p>
              </div>
            ) : userPlans.length === 0 ? (
              <div className="bg-white rounded-3xl border border-stone-200/60 p-8 text-center space-y-4 shadow-sm animate-fadeIn">
                <div className="w-16 h-16 rounded-2xl bg-stone-50 flex items-center justify-center mx-auto text-stone-400">
                  <Leaf className="w-8 h-8" />
                </div>
                <div className="space-y-1">
                  <p className="text-stone-700 font-semibold text-base">No Plans Found</p>
                  <p className="text-stone-500 text-sm max-w-sm mx-auto">
                    You need to generate an Ayurvedic treatment plan first before chatting about it.
                  </p>
                </div>
                <button
                  onClick={() => window.location.href = '/dashboard'}
                  className="px-5 py-2.5 bg-gradient-to-br from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white text-sm font-semibold rounded-xl shadow-md shadow-emerald-500/20 active:scale-95 transition-all duration-150"
                >
                  Go to Dashboard
                </button>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 animate-fadeIn">
                {userPlans.map((plan) => (
                  <div
                    key={plan.id}
                    onClick={() => {
                      setSelectedPlanId(plan.id);
                      setPlanMessages([]);
                    }}
                    className="bg-white rounded-2xl border border-stone-200/60 hover:border-emerald-500 hover:shadow-lg p-5 cursor-pointer transition-all duration-300 group flex flex-col justify-between shadow-sm relative overflow-hidden active:scale-98"
                  >
                    {/* Subtle Background Accent */}
                    <div className="absolute top-0 right-0 w-24 h-24 bg-gradient-to-br from-emerald-100/20 to-teal-100/10 rounded-bl-full pointer-events-none group-hover:scale-110 transition-transform duration-300" />
                    
                    <div className="space-y-3 relative z-10">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                        plan.dosha === 'pitta' ? 'bg-amber-50 text-amber-700 border border-amber-200/50' :
                        plan.dosha === 'vata' ? 'bg-sky-50 text-sky-700 border border-sky-200/50' :
                        'bg-emerald-50 text-emerald-700 border border-emerald-200/50'
                      }`}>
                        {plan.dosha} dosha
                      </span>
                      
                      <h3 className="font-bold text-stone-800 text-base group-hover:text-emerald-700 transition-colors leading-snug">
                        {plan.title}
                      </h3>
                      
                      <div className="space-y-1 text-xs text-stone-500">
                        <p><span className="font-medium text-stone-600">Condition:</span> {plan.condition.replace('_', ' ').replace(/\b\w/g, c => c.toUpperCase())}</p>
                        <div className="flex items-center gap-1 mt-1">
                          <Calendar className="w-3.5 h-3.5 text-stone-400" />
                          <span>Created: {new Date(plan.created_at).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' })}</span>
                        </div>
                      </div>
                    </div>
                    
                    <div className="mt-4 pt-3 border-t border-stone-100 flex justify-end">
                      <span className="text-xs font-semibold text-emerald-600 group-hover:text-emerald-700 flex items-center gap-1 transition-colors">
                        Start Chatting <ChevronRight className="w-3 h-3 group-hover:translate-x-0.5 transition-transform" />
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      ) : (
        /* Chat Messages Area */
        <div className="flex-1 overflow-y-auto px-4 py-6">
          <div className="max-w-3xl mx-auto space-y-5">
            
            {/* Active Plan Banner Context */}
            {activeTab === 'plan' && selectedPlanId && activePlan && (
              <div className="bg-emerald-50/70 border border-emerald-100 rounded-2xl p-3 flex items-center justify-between shadow-sm animate-fadeIn">
                <div className="flex items-center gap-2.5">
                  <div className="w-8 h-8 rounded-xl bg-emerald-500/10 flex items-center justify-center text-emerald-700">
                    <Leaf className="w-4 h-4" />
                  </div>
                  <div>
                    <p className="text-[10px] uppercase font-bold tracking-wider text-emerald-700 leading-none mb-1">Active Plan Context</p>
                    <p className="text-xs font-semibold text-stone-800">{activePlan.title}</p>
                  </div>
                </div>
                <button 
                  onClick={handleSwitchPlan}
                  className="flex items-center gap-1 text-xs font-semibold text-emerald-600 hover:text-emerald-700 bg-white border border-emerald-200 px-3 py-1.5 rounded-xl transition-all duration-200 shadow-sm hover:shadow-md active:scale-95"
                >
                  <RefreshCw className="w-3 h-3" />
                  Switch Plan
                </button>
              </div>
            )}

            {/* Empty State */}
            {activeMessages.length === 0 && (
              <div className="flex flex-col items-center justify-center py-16 gap-6 animate-fadeIn">
                <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center shadow-2xl shadow-emerald-500/30">
                  <Leaf className="w-10 h-10 text-white" />
                </div>
                <div className="text-center max-w-md">
                  <h2 className="text-2xl font-bold text-stone-800 mb-2">
                    {activeTab === 'general' ? "Hi! I'm AyurBot 🌿" : "Plan Assistant 🌿"}
                  </h2>
                  <p className="text-stone-500 text-sm leading-relaxed">
                    {activeTab === 'general'
                      ? "Ask me anything about Ayurveda — from doshas, herbs, and skin care to general wellness. I'll find the best answer for you."
                      : `Ask questions specifically about your ${activePlan?.title || 'Personalized Treatment Plan'}. Ask why ingredients were chosen or how routines work.`}
                  </p>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-xl">
                  {suggestedQuestions.map((q, i) => (
                    <button
                      key={i}
                      onClick={() => handleSend(q)}
                      className="text-left px-4 py-3 bg-white rounded-2xl border border-emerald-100 text-sm text-stone-700 hover:border-emerald-400 hover:bg-emerald-50 hover:text-emerald-800 transition-all duration-200 shadow-sm hover:shadow-md group"
                    >
                      <MessageSquare className="w-3.5 h-3.5 text-emerald-500 mb-1.5 group-hover:text-emerald-600 transition-colors" />
                      {q}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Chat Messages Bubbles */}
            {activeMessages.map((msg) =>
              msg.role === 'user' ? (
                /* User Bubble — right aligned */
                <div key={msg.id} className="flex items-end justify-end gap-2 animate-slideInRight">
                  <div className="max-w-[75%] lg:max-w-[65%]">
                    <div className="bg-gradient-to-br from-emerald-600 to-teal-600 text-white px-4 py-3 rounded-2xl rounded-br-md shadow-lg shadow-emerald-500/20">
                      <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                    </div>
                  </div>
                  <div className="flex-none w-8 h-8 rounded-full bg-emerald-100 flex items-center justify-center mb-0.5 ring-2 ring-emerald-200">
                    <User className="w-4 h-4 text-emerald-700" />
                  </div>
                </div>
              ) : (
                /* Bot Bubble — left aligned */
                <div key={msg.id} className="flex items-end gap-2 animate-slideInLeft">
                  <div className="flex-none w-8 h-8 rounded-full bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center mb-0.5 shadow-md shadow-emerald-500/30">
                    <Bot className="w-4 h-4 text-white" />
                  </div>
                  <div className="max-w-[75%] lg:max-w-[65%] space-y-2">
                    <div className="bg-white text-stone-800 px-4 py-3 rounded-2xl rounded-bl-md shadow-md border border-stone-100">
                      <p className="text-sm leading-relaxed whitespace-pre-wrap">{msg.content}</p>
                    </div>
                    {/* Source Pills */}
                    {msg.sources && msg.sources.length > 0 && (
                      <div className="space-y-1.5">
                        <div className="flex items-center gap-1.5 px-1">
                          <Sparkles className="w-3 h-3 text-stone-400" />
                          <span className="text-[10px] font-semibold text-stone-400 uppercase tracking-wider">
                            References
                          </span>
                        </div>
                        {msg.sources.map((src, i) => (
                          <div
                            key={i}
                            className="px-3 py-2 bg-emerald-50/70 border border-emerald-100 rounded-xl"
                          >
                            <p className="text-[11px] text-stone-500 leading-relaxed line-clamp-2">
                              {src}
                            </p>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )
            )}

            {/* Loading Thinking Indicator */}
            {isLoading && (
              <div className="flex items-end gap-2 animate-slideInLeft">
                <div className="flex-none w-8 h-8 rounded-full bg-gradient-to-br from-emerald-500 to-teal-600 flex items-center justify-center shadow-md shadow-emerald-500/30">
                  <Bot className="w-4 h-4 text-white" />
                </div>
                <div className="bg-white px-4 py-3.5 rounded-2xl rounded-bl-md shadow-md border border-stone-100">
                  <div className="flex items-center gap-2">
                    <Loader2 className="w-4 h-4 text-emerald-500 animate-spin" />
                    <span className="text-sm text-stone-500 font-medium">
                      Thinking…
                    </span>
                  </div>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>
        </div>
      )}

      {/* Input Area — fixed at bottom, hidden when selecting plans in plan mode */}
      {(activeTab === 'general' || (activeTab === 'plan' && selectedPlanId)) && (
        <div className="flex-none bg-white/90 backdrop-blur-md border-t border-stone-200 px-4 py-4">
          <div className="max-w-3xl mx-auto">
            <div className="flex items-end gap-3 bg-stone-50 border border-stone-200 rounded-2xl px-4 py-3 focus-within:border-emerald-400 focus-within:ring-2 focus-within:ring-emerald-400/20 transition-all duration-200 shadow-sm">
              <textarea
                ref={inputRef}
                id="chat-input"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={activeTab === 'general' ? "Ask about doshas, herbs, or general wellness..." : "Ask questions about this specific treatment plan..."}
                rows={1}
                disabled={isLoading}
                className="flex-1 bg-transparent text-sm text-stone-800 placeholder-stone-400 resize-none outline-none leading-relaxed max-h-32 overflow-y-auto disabled:opacity-50"
                style={{ fieldSizing: 'content', minHeight: '24px' }}
              />
              <button
                id="chat-send-btn"
                onClick={() => handleSend()}
                disabled={!inputValue.trim() || isLoading}
                className="flex-none w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-600 to-teal-600 flex items-center justify-center text-white shadow-md shadow-emerald-500/30 hover:from-emerald-500 hover:to-teal-500 active:scale-95 transition-all duration-150 disabled:opacity-40 disabled:cursor-not-allowed disabled:scale-100"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
            <p className="text-center text-[10px] text-stone-400 mt-2 tracking-wide">
              Always consult a practitioner for medical advice
            </p>
          </div>
        </div>
      )}
    </div>
  );
};

export default ChatPage;
