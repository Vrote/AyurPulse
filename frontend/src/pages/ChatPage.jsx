import React, { useState, useRef, useEffect } from 'react';
import api from '../services/api';
import { Send, Bot, User, Leaf, Loader2, MessageSquare, Sparkles } from 'lucide-react';

const ChatPage = () => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const suggestedQuestions = [
    'What foods should I avoid for Pitta dosha?',
    'Which herbs help reduce acne?',
    'What is my Day 1 morning routine?',
    'How does Ashwagandha help with stress?',
    'What should I eat based on my plan?',
    'What is Vata dosha and its characteristics?',
  ];

  const handleSend = async (messageText) => {
    const text = (messageText || inputValue).trim();
    if (!text || isLoading) return;

    const userMessage = { role: 'user', content: text, id: Date.now() };
    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await api.post('/chat', {
        message: text,
        history: messages.map((m) => ({ role: m.role, content: m.content })),
      });
      const { answer, sources } = response.data;

      const botMessage = {
        role: 'bot',
        content: answer,
        sources: sources || [],
        id: Date.now() + 1,
      };
      setMessages((prev) => [...prev, botMessage]);
    } catch (err) {
      const errMsg =
        err?.response?.data?.detail ||
        'Something went wrong. Please try again.';
      setMessages((prev) => [
        ...prev,
        {
          role: 'bot',
          content: `⚠️ ${errMsg}`,
          sources: [],
          id: Date.now() + 1,
        },
      ]);
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
        <div className="max-w-3xl mx-auto flex items-center gap-3">
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
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-3xl mx-auto space-y-5">

          {/* Empty State */}
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center py-16 gap-6 animate-fadeIn">
              <div className="w-20 h-20 rounded-3xl bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center shadow-2xl shadow-emerald-500/30">
                <Leaf className="w-10 h-10 text-white" />
              </div>
              <div className="text-center max-w-md">
                <h2 className="text-2xl font-bold text-stone-800 mb-2">
                  Hi! I'm AyurBot 🌿
                </h2>
                <p className="text-stone-500 text-sm leading-relaxed">
                  Ask me anything about Ayurveda — from doshas, herbs, and skin care to your personalized wellness plan. I'll find the best answer for you.
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

          {/* Chat Messages */}
          {messages.map((msg) =>
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

          {/* Loading Indicator */}
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

      {/* Input Area — fixed at bottom */}
      <div className="flex-none bg-white/90 backdrop-blur-md border-t border-stone-200 px-4 py-4">
        <div className="max-w-3xl mx-auto">
          <div className="flex items-end gap-3 bg-stone-50 border border-stone-200 rounded-2xl px-4 py-3 focus-within:border-emerald-400 focus-within:ring-2 focus-within:ring-emerald-400/20 transition-all duration-200 shadow-sm">
            <textarea
              ref={inputRef}
              id="chat-input"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about doshas, herbs, skin care, or your wellness plan…"
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
    </div>
  );
};

export default ChatPage;
