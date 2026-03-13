import React, { useState } from 'react';
import { motion } from 'motion/react';
import { Sparkles, Loader2, LogIn, UserPlus } from 'lucide-react';

interface AuthProps {
  onLogin: (user: { id: number; username: string }) => void;
}

export default function Auth({ onLogin }: AuthProps) {
  const [isLogin, setIsLogin] = useState(true);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    const endpoint = isLogin ? '/api/login' : '/api/signup';
    
    try {
      const res = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password })
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.error || 'Authentication failed');
      }

      if (isLogin) {
        onLogin(data.user);
      } else {
        // After signup, automatically login
        const loginRes = await fetch('/api/login', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ username, password })
        });
        const loginData = await loginRes.json();
        onLogin(loginData.user);
      }
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#FAFAFA] flex items-center justify-center p-4">
      <motion.div 
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="w-full max-w-md bg-white border border-[#DBDBDB] rounded-3xl p-8 shadow-sm space-y-8"
      >
        <div className="text-center space-y-2">
          <div className="flex justify-center mb-4">
            <div className="p-3 bg-black rounded-2xl text-white">
              <Sparkles className="w-8 h-8" />
            </div>
          </div>
          <h1 className="text-2xl font-bold italic">VibeSearch</h1>
          <p className="text-gray-500 text-sm">
            {isLogin ? 'Welcome back to your curated world.' : 'Start your aesthetic journey today.'}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-gray-400 uppercase ml-1">Username</label>
            <input
              type="text"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-3 bg-[#FAFAFA] border border-[#DBDBDB] rounded-xl focus:outline-none focus:ring-2 focus:ring-black transition-all text-sm"
              placeholder="Your unique handle"
            />
          </div>
          <div className="space-y-1">
            <label className="text-[10px] font-bold text-gray-400 uppercase ml-1">Password</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-4 py-3 bg-[#FAFAFA] border border-[#DBDBDB] rounded-xl focus:outline-none focus:ring-2 focus:ring-black transition-all text-sm"
              placeholder="Keep it secret, keep it safe"
            />
          </div>

          {error && (
            <p className="text-red-500 text-xs font-medium text-center">{error}</p>
          )}

          <button
            disabled={loading}
            className="w-full py-3 bg-black text-white rounded-xl font-bold hover:bg-gray-800 disabled:opacity-50 transition-all flex items-center justify-center gap-2"
          >
            {loading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              isLogin ? <LogIn className="w-5 h-5" /> : <UserPlus className="w-5 h-5" />
            )}
            {isLogin ? 'Login' : 'Sign Up'}
          </button>
        </form>

        <div className="text-center pt-4 border-t border-[#DBDBDB]">
          <button 
            onClick={() => setIsLogin(!isLogin)}
            className="text-sm font-medium text-gray-500 hover:text-black transition-colors"
          >
            {isLogin ? "Don't have an account? Sign up" : "Already have an account? Login"}
          </button>
        </div>
      </motion.div>
    </div>
  );
}
