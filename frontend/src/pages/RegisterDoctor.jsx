import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Leaf, User, Mail, Lock, Building, GraduationCap, AlertCircle, CheckCircle } from 'lucide-react';

const RegisterDoctor = () => {
  const { registerDoctor } = useAuth();
  const navigate = useNavigate();

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [specialization, setSpecialization] = useState('Ayurvedic Dermatology');
  const [clinicAddress, setClinicAddress] = useState('');
  const [experienceYears, setExperienceYears] = useState('');

  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const specializations = [
    'Ayurvedic Dermatology',
    'Skin Rejuvenation',
    'Anti-Aging (Rasayana)',
    'General Ayurveda',
  ];

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccess('');

    if (!fullName || !email || !password || !specialization || !clinicAddress || !experienceYears) {
      setError('Please fill in all fields.');
      return;
    }

    // Password validation check
    const hasUpper = /[A-Z]/.test(password);
    const hasDigit = /[0-9]/.test(password);
    const hasSpecial = /[^A-Za-z0-9]/.test(password);
    if (!hasUpper || !hasDigit || !hasSpecial || password.length < 8) {
      setError(
        'Password must be at least 8 characters long and contain at least one uppercase letter, one number, and one special character.'
      );
      return;
    }

    const expVal = parseInt(experienceYears);
    if (isNaN(expVal) || expVal < 0) {
      setError('Experience years must be a valid positive number.');
      return;
    }

    setSubmitting(true);
    try {
      await registerDoctor({
        full_name: fullName,
        email,
        password,
        specialization,
        clinic_address: clinicAddress,
        experience_years: expVal,
      });
      setSuccess('Doctor registration complete! Vetting details sent. Redirecting to login...');
      setTimeout(() => {
        navigate('/login');
      }, 2000);
    } catch (err) {
      console.error(err);
      setError(
        err.response?.data?.detail || err.response?.data?.message || 'Doctor registration failed. Please try again.'
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="min-h-screen bg-stone-50 pt-16 flex items-center justify-center px-4 sm:px-6 lg:px-8 relative overflow-hidden">
      <div className="absolute top-0 right-0 w-96 h-96 bg-emerald-100/30 rounded-full blur-3xl -z-10"></div>
      <div className="absolute bottom-0 left-0 w-96 h-96 bg-amber-100/30 rounded-full blur-3xl -z-10"></div>

      <div className="max-w-lg w-full space-y-8 bg-white p-8 rounded-2xl border border-stone-200 shadow-xl shadow-stone-200/50">
        <div className="text-center">
          <div className="mx-auto w-12 h-12 rounded-xl bg-emerald-100 flex items-center justify-center text-emerald-800">
            <Leaf className="w-6 h-6" />
          </div>
          <h2 className="mt-6 text-3xl font-extrabold text-stone-900 tracking-tight">
            Doctor Registration
          </h2>
          <p className="mt-2 text-sm text-stone-500">
            Join the AyurPulse clinical validation network
          </p>
        </div>

        {error && (
          <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-rose-800 shrink-0 mt-0.5" />
            <div className="text-sm text-rose-800">{error}</div>
          </div>
        )}

        {success && (
          <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 flex items-start gap-3">
            <CheckCircle className="w-5 h-5 text-emerald-800 shrink-0 mt-0.5" />
            <div className="text-sm text-emerald-800">{success}</div>
          </div>
        )}

        <form className="mt-8 space-y-5" onSubmit={handleSubmit}>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label htmlFor="fullName" className="block text-sm font-semibold text-stone-700 mb-1">
                Full Name
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-stone-400">
                  <User className="w-5 h-5" />
                </div>
                <input
                  id="fullName"
                  name="fullName"
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="block w-full pl-10 pr-3 py-3 border border-stone-300 rounded-xl bg-stone-50/50 text-stone-950 placeholder-stone-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent text-sm"
                  placeholder="Dr. Shreya Patel"
                />
              </div>
            </div>

            <div>
              <label htmlFor="email" className="block text-sm font-semibold text-stone-700 mb-1">
                Email Address
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-stone-400">
                  <Mail className="w-5 h-5" />
                </div>
                <input
                  id="email"
                  name="email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="block w-full pl-10 pr-3 py-3 border border-stone-300 rounded-xl bg-stone-50/50 text-stone-950 placeholder-stone-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent text-sm"
                  placeholder="shreya@ayurpulse.com"
                />
              </div>
            </div>

            <div className="sm:col-span-2">
              <label htmlFor="password" className="block text-sm font-semibold text-stone-700 mb-1">
                Password
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-stone-400">
                  <Lock className="w-5 h-5" />
                </div>
                <input
                  id="password"
                  name="password"
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="block w-full pl-10 pr-3 py-3 border border-stone-300 rounded-xl bg-stone-50/50 text-stone-950 placeholder-stone-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent text-sm"
                  placeholder="••••••••"
                />
              </div>
              <p className="mt-1 text-stone-400 text-[10px]">
                Must contain at least 8 chars, 1 uppercase, 1 digit, and 1 special symbol.
              </p>
            </div>

            <div>
              <label htmlFor="specialization" className="block text-sm font-semibold text-stone-700 mb-1">
                Specialization Area
              </label>
              <select
                id="specialization"
                name="specialization"
                value={specialization}
                onChange={(e) => setSpecialization(e.target.value)}
                className="block w-full px-3 py-3 border border-stone-300 rounded-xl bg-stone-50/50 text-stone-950 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent text-sm"
              >
                {specializations.map((spec) => (
                  <option key={spec} value={spec}>
                    {spec}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label htmlFor="experienceYears" className="block text-sm font-semibold text-stone-700 mb-1">
                Years of Experience
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-stone-400">
                  <GraduationCap className="w-5 h-5" />
                </div>
                <input
                  id="experienceYears"
                  name="experienceYears"
                  type="number"
                  required
                  min="0"
                  value={experienceYears}
                  onChange={(e) => setExperienceYears(e.target.value)}
                  className="block w-full pl-10 pr-3 py-3 border border-stone-300 rounded-xl bg-stone-50/50 text-stone-950 placeholder-stone-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent text-sm"
                  placeholder="e.g. 8"
                />
              </div>
            </div>

            <div className="sm:col-span-2">
              <label htmlFor="clinicAddress" className="block text-sm font-semibold text-stone-700 mb-1">
                Clinic Address
              </label>
              <div className="relative">
                <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-stone-400">
                  <Building className="w-5 h-5" />
                </div>
                <input
                  id="clinicAddress"
                  name="clinicAddress"
                  type="text"
                  required
                  value={clinicAddress}
                  onChange={(e) => setClinicAddress(e.target.value)}
                  className="block w-full pl-10 pr-3 py-3 border border-stone-300 rounded-xl bg-stone-50/50 text-stone-950 placeholder-stone-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent text-sm"
                  placeholder="123 Wellness Ave, Pune"
                />
              </div>
            </div>
          </div>

          <div className="pt-2">
            <button
              type="submit"
              disabled={submitting}
              className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-semibold rounded-xl text-white bg-emerald-700 hover:bg-emerald-800 active:scale-98 transition-all disabled:opacity-50 disabled:pointer-events-none shadow-md shadow-emerald-700/10"
            >
              {submitting ? (
                <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
              ) : (
                'Register Practitioner'
              )}
            </button>
          </div>
        </form>

        <div className="pt-6 border-t border-stone-200 text-center">
          <p className="text-sm text-stone-500">
            Already registered?{' '}
            <Link to="/login" className="font-semibold text-emerald-700 hover:text-emerald-800">
              Sign In
            </Link>
          </p>
        </div>
      </div>
    </main>
  );
};

export default RegisterDoctor;
