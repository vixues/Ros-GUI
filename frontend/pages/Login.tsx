import React, { useState } from 'react';
import { api } from '../services/api';
import { useStore } from '../store/useStore';
import { Cpu, ShieldCheck } from 'lucide-react';
import { cn } from '../lib/utils';

export const Login: React.FC = () => {
  const login = useStore((state) => state.login);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const response = await api.login(username, password);
      login(response.user, response.access_token);
    } catch (err) {
      setError('Access Denied. Invalid credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-black flex items-center justify-center relative overflow-hidden">
      {/* Background Grid */}
      <div className="absolute inset-0 opacity-20 pointer-events-none" 
           style={{ backgroundImage: 'radial-gradient(#333 1px, transparent 1px)', backgroundSize: '20px 20px' }}>
      </div>

      <div className="w-full max-w-sm z-10 p-8 bg-black border border-neutral-800 shadow-2xl">
        <div className="flex flex-col items-center mb-10">
          <div className="w-12 h-12 bg-white flex items-center justify-center mb-4">
            <Cpu className="w-6 h-6 text-black" />
          </div>
          <h1 className="text-2xl font-bold text-white tracking-widest font-mono">SKYNET<span className="text-neutral-600">.OS</span></h1>
          <p className="text-neutral-500 text-[10px] tracking-[0.3em] mt-2 uppercase">Authorized Access Only</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="space-y-1">
            <label className="text-[10px] font-mono text-neutral-500 uppercase tracking-wider">Identity</label>
            <input
              type="text"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className={cn(
                "w-full bg-black border-b border-neutral-700 py-2 text-white transition-colors font-mono text-sm",
                "focus:border-white focus:outline-none placeholder:text-neutral-800"
              )}
              placeholder="ENTER USERNAME"
            />
          </div>

          <div className="space-y-1">
            <label className="text-[10px] font-mono text-neutral-500 uppercase tracking-wider">Keycode</label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={cn(
                "w-full bg-black border-b border-neutral-700 py-2 text-white transition-colors font-mono text-sm",
                "focus:border-white focus:outline-none placeholder:text-neutral-800"
              )}
              placeholder="ENTER PASSWORD"
            />
          </div>

          {error && (
            <div className="p-3 bg-red-950/30 border border-red-900 text-red-500 text-xs flex items-center gap-2 font-mono">
              <ShieldCheck className="w-3 h-3" />
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className={cn(
              "w-full bg-white text-black font-bold py-3 mt-4 hover:bg-neutral-200 transition-colors font-mono text-xs tracking-widest uppercase",
              "disabled:opacity-50 disabled:cursor-not-allowed"
            )}
          >
            {loading ? 'VERIFYING...' : 'INITIATE SESSION'}
          </button>
        </form>
      </div>
    </div>
  );
};