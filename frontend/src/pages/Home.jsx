import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { ArrowRight, Brain, Target, ShieldCheck, MapPin } from 'lucide-react';

const Home = () => {
  const { user } = useAuth();

  return (
    <main className="min-h-screen bg-stone-50 pt-16 flex flex-col justify-between">
      {/* Hero Section */}
      <section className="relative px-6 py-20 lg:py-32 overflow-hidden flex-grow flex items-center">
        <div className="absolute inset-0 -z-10">
          <div className="absolute top-20 right-10 w-96 h-96 bg-emerald-100/50 rounded-full blur-3xl"></div>
          <div className="absolute bottom-20 left-10 w-96 h-96 bg-amber-100/40 rounded-full blur-3xl"></div>
        </div>

        <div className="mx-auto max-w-5xl text-center space-y-8">
          <div className="inline-flex items-center gap-1.5 px-4 py-2 rounded-full bg-emerald-50 text-emerald-800 text-sm font-semibold border border-emerald-150">
            <span className="w-2 h-2 rounded-full bg-emerald-600 animate-ping"></span>
            AI-Powered Ayurvedic Wellness Platform
          </div>

          <h1 className="text-5xl sm:text-6xl lg:text-7xl font-extrabold text-stone-900 tracking-tight leading-tight text-balance">
            Analyze Your Skin. <br />
            Discover Your <span className="text-emerald-700">Prakriti</span>.
          </h1>

          <p className="text-xl max-w-2xl text-stone-600 mx-auto leading-relaxed">
            Combine PyTorch-driven skin diagnostics with ancient Ayurvedic wisdom to construct highly personalized 7-day treatment plans vetted by certified doctors.
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center pt-4">
            {user ? (
              <Link
                to="/dashboard"
                className="flex items-center justify-center gap-2 px-8 py-4 bg-emerald-700 text-white rounded-xl text-lg font-semibold hover:bg-emerald-800 transition shadow-lg shadow-emerald-700/10 active:scale-95"
              >
                Go to Dashboard <ArrowRight className="w-5 h-5" />
              </Link>
            ) : (
              <>
                <Link
                  to="/register"
                  className="flex items-center justify-center gap-2 px-8 py-4 bg-emerald-700 text-white rounded-xl text-lg font-semibold hover:bg-emerald-800 transition shadow-lg shadow-emerald-700/10 active:scale-95"
                >
                  Start Skin Analysis <ArrowRight className="w-5 h-5" />
                </Link>
                <Link
                  to="/login"
                  className="flex items-center justify-center px-8 py-4 bg-white border border-stone-300 text-stone-700 rounded-xl text-lg font-semibold hover:bg-stone-50 transition active:scale-95"
                >
                  Sign In
                </Link>
              </>
            )}
          </div>
        </div>
      </section>

      {/* Grid Highlights Section */}
      <section className="px-6 py-16 bg-white border-t border-stone-200">
        <div className="mx-auto max-w-6xl">
          <div className="grid md:grid-cols-4 gap-8">
            <div className="flex flex-col items-center text-center p-6 space-y-3 bg-stone-50 rounded-2xl border border-stone-200/60 shadow-sm">
              <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center text-emerald-800 shrink-0">
                <Brain className="w-6 h-6" />
              </div>
              <h3 className="font-bold text-stone-900 text-lg">AI Diagnostics</h3>
              <p className="text-sm text-stone-600 leading-relaxed">
                Scan your face to detect acne, blackheads, wrinkles, or dark spots using deep learning.
              </p>
            </div>

            <div className="flex flex-col items-center text-center p-6 space-y-3 bg-stone-50 rounded-2xl border border-stone-200/60 shadow-sm">
              <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center text-emerald-800 shrink-0">
                <Target className="w-6 h-6" />
              </div>
              <h3 className="font-bold text-stone-900 text-lg">Dosha Profiling</h3>
              <p className="text-sm text-stone-600 leading-relaxed">
                Calculate your dominant Vata, Pitta, or Kapha constitution to set recommendations.
              </p>
            </div>

            <div className="flex flex-col items-center text-center p-6 space-y-3 bg-stone-50 rounded-2xl border border-stone-200/60 shadow-sm">
              <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center text-emerald-800 shrink-0">
                <ShieldCheck className="w-6 h-6" />
              </div>
              <h3 className="font-bold text-stone-900 text-lg">Doctor Vetted</h3>
              <p className="text-sm text-stone-600 leading-relaxed">
                Qualified Ayurvedic practitioners review and refine your generated schedule.
              </p>
            </div>

            <div className="flex flex-col items-center text-center p-6 space-y-3 bg-stone-50 rounded-2xl border border-stone-200/60 shadow-sm">
              <div className="w-12 h-12 bg-emerald-100 rounded-xl flex items-center justify-center text-emerald-800 shrink-0">
                <MapPin className="w-6 h-6" />
              </div>
              <h3 className="font-bold text-stone-900 text-lg">Shops Locator</h3>
              <p className="text-sm text-stone-600 leading-relaxed">
                Geolocate nearby physical Ayurvedic stores to source clean ingredients.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 bg-stone-50 border-t border-stone-250 text-center text-stone-500 text-sm">
        <div className="max-w-7xl mx-auto px-4">
          <p>© {new Date().getFullYear()} AyurPulse Platform. All rights reserved.</p>
        </div>
      </footer>
    </main>
  );
};

export default Home;
