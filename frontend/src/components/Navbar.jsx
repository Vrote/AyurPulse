import React, { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Leaf, LogOut, Menu, X, User } from 'lucide-react';

const Navbar = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [isOpen, setIsOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/');
    setIsOpen(false);
  };

  const isActive = (path) => location.pathname === path;

  const navLinks = [
    { name: 'Home', path: '/' },
    { name: 'About', path: '/about' },
  ];

  if (user) {
    if (user.role === 'user') {
      navLinks.push({ name: 'My Dashboard', path: '/dashboard' });
    } else if (user.role === 'doctor') {
      navLinks.push({ name: 'Doctor Dashboard', path: '/dashboard' });
    }
  }

  return (
    <nav className="fixed top-0 left-0 w-full z-50 bg-white/80 backdrop-blur-md border-b border-stone-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Logo */}
          <div className="flex items-center">
            <Link to="/" className="flex items-center gap-2 group">
              <div className="w-10 h-10 rounded-xl bg-emerald-100 flex items-center justify-center text-emerald-700 group-hover:bg-emerald-200 transition-colors">
                <Leaf className="w-6 h-6 animate-pulse" />
              </div>
              <span className="text-xl font-bold tracking-tight text-stone-900 group-hover:text-emerald-800 transition-colors">
                Ayur<span className="text-emerald-600">Pulse</span>
              </span>
            </Link>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-6">
            {navLinks.map((link) => (
              <Link
                key={link.path}
                to={link.path}
                className={`text-sm font-medium transition-colors ${
                  isActive(link.path)
                    ? 'text-emerald-700 font-semibold border-b-2 border-emerald-600 pb-1'
                    : 'text-stone-600 hover:text-emerald-700'
                }`}
              >
                {link.name}
              </Link>
            ))}

            {user ? (
              <div className="flex items-center gap-4 pl-4 border-l border-stone-200">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-800">
                    <User className="w-4 h-4" />
                  </div>
                  <span className="text-sm font-semibold text-stone-700 max-w-[120px] truncate" title={user.full_name}>
                    {user.full_name}
                  </span>
                  {user.role === 'doctor' && (
                    <span className="text-[10px] bg-emerald-600 text-white font-bold px-1.5 py-0.5 rounded-full uppercase tracking-wider">
                      Dr
                    </span>
                  )}
                </div>
                <button
                  onClick={handleLogout}
                  className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl text-sm font-medium text-stone-600 hover:text-rose-600 hover:bg-rose-50 active:scale-95 transition-all"
                >
                  <LogOut className="w-4 h-4" />
                  Logout
                </button>
              </div>
            ) : (
              <div className="flex items-center gap-3 pl-4 border-l border-stone-200">
                <Link
                  to="/login"
                  className="px-4 py-2 text-sm font-medium text-stone-700 hover:text-emerald-700 transition-colors"
                >
                  Sign In
                </Link>
                <Link
                  to="/register"
                  className="px-4 py-2 rounded-xl text-sm font-medium text-white bg-emerald-700 hover:bg-emerald-800 active:scale-95 transition-all shadow-md shadow-emerald-700/10"
                >
                  Get Started
                </Link>
              </div>
            )}
          </div>

          {/* Mobile Menu Button */}
          <div className="flex items-center md:hidden">
            <button
              onClick={() => setIsOpen(!isOpen)}
              className="p-2 rounded-lg text-stone-600 hover:text-emerald-700 hover:bg-emerald-50 transition-colors"
            >
              {isOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Navigation Panel */}
      {isOpen && (
        <div className="md:hidden bg-white border-b border-stone-200 px-4 py-4 space-y-3">
          {navLinks.map((link) => (
            <Link
              key={link.path}
              to={link.path}
              onClick={() => setIsOpen(false)}
              className={`block px-3 py-2 rounded-xl text-base font-medium transition-colors ${
                isActive(link.path)
                  ? 'text-emerald-800 bg-emerald-50/70 font-semibold'
                  : 'text-stone-600 hover:text-emerald-700 hover:bg-stone-50'
              }`}
            >
              {link.name}
            </Link>
          ))}

          {user ? (
            <div className="pt-4 border-t border-stone-100 space-y-3">
              <div className="flex items-center gap-2 px-3 py-1">
                <div className="w-8 h-8 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-800">
                  <User className="w-4 h-4" />
                </div>
                <span className="text-sm font-semibold text-stone-700 truncate">
                  {user.full_name}
                </span>
                {user.role === 'doctor' && (
                  <span className="text-[10px] bg-emerald-600 text-white font-bold px-1.5 py-0.5 rounded-full uppercase">
                    Dr
                  </span>
                )}
              </div>
              <button
                onClick={handleLogout}
                className="w-full flex items-center justify-center gap-1.5 px-3 py-2 rounded-xl text-base font-medium text-rose-600 hover:bg-rose-50 transition-all"
              >
                <LogOut className="w-4 h-4" />
                Logout
              </button>
            </div>
          ) : (
            <div className="pt-4 border-t border-stone-100 flex flex-col gap-2">
              <Link
                to="/login"
                onClick={() => setIsOpen(false)}
                className="w-full text-center px-4 py-2 rounded-xl text-base font-medium text-stone-700 hover:bg-stone-50 transition-colors"
              >
                Sign In
              </Link>
              <Link
                to="/register"
                onClick={() => setIsOpen(false)}
                className="w-full text-center px-4 py-2 rounded-xl text-base font-medium text-white bg-emerald-700 hover:bg-emerald-800 transition-colors"
              >
                Get Started
              </Link>
            </div>
          )}
        </div>
      )}
    </nav>
  );
};

export default Navbar;
