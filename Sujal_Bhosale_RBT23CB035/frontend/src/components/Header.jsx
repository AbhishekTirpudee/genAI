import React from 'react';
import { Sparkles, Cpu, ShieldCheck, AlertTriangle, ExternalLink } from 'lucide-react';

export default function Header({ health, isCheckingHealth }) {
  const isHealthy = health?.status === 'healthy';
  const tokenMissing = health && !health.token_configured;

  return (
    <header className="border-b border-slate-800/80 bg-[#0a0d14]/80 backdrop-blur-md sticky top-0 z-40">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between gap-4">
        {/* Brand Logo */}
        <div className="flex items-center gap-3">
          <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-tr from-purple-600 via-indigo-600 to-pink-500 shadow-lg shadow-purple-500/25">
            <Sparkles className="w-5 h-5 text-white animate-pulse" />
            <div className="absolute inset-0 rounded-xl bg-purple-400 blur-sm opacity-30"></div>
          </div>
          <div>
            <div className="flex items-center gap-2">
              <span className="font-bold text-lg tracking-tight bg-gradient-to-r from-white via-slate-200 to-purple-300 bg-clip-text text-transparent">
                DreamCanvas
              </span>
              <span className="text-[10px] font-semibold tracking-wider uppercase px-2 py-0.5 rounded-full bg-purple-500/10 text-purple-400 border border-purple-500/20">
                FLUX.1
              </span>
            </div>
            <p className="text-xs text-slate-400 hidden sm:block">
              AI Text-to-Image Generator
            </p>
          </div>
        </div>

        {/* Center / Model Badge */}
        <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-900/80 border border-slate-800 text-xs text-slate-300">
          <Cpu className="w-3.5 h-3.5 text-purple-400" />
          <span>Model:</span>
          <span className="font-mono text-purple-300 font-medium">black-forest-labs/FLUX.1-schnell</span>
          <span className="text-[10px] bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded font-mono">PNG Output</span>
        </div>

        {/* Right Status Indicators */}
        <div className="flex items-center gap-3">
          {tokenMissing && (
            <div className="hidden lg:flex items-center gap-1.5 px-3 py-1 rounded-lg bg-amber-500/10 text-amber-300 border border-amber-500/30 text-xs">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-400" />
              <span>Configure HF_TOKEN in backend/.env</span>
            </div>
          )}

          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900/90 border border-slate-800 text-xs">
            <div className={`w-2 h-2 rounded-full ${
              isCheckingHealth
                ? 'bg-amber-400 animate-ping'
                : isHealthy
                ? 'bg-emerald-400 shadow-sm shadow-emerald-400/50'
                : 'bg-amber-400'
            }`} />
            <span className="text-slate-300 font-medium">
              {isCheckingHealth ? 'Checking API...' : isHealthy ? 'API Online' : 'Degraded (No Token)'}
            </span>
          </div>

          <a
            href="https://huggingface.co/black-forest-labs/FLUX.1-schnell"
            target="_blank"
            rel="noopener noreferrer"
            className="hidden sm:inline-flex items-center gap-1.5 text-xs text-slate-400 hover:text-slate-200 transition-colors py-1.5 px-2.5 rounded-lg hover:bg-slate-800/60"
            title="View FLUX.1-schnell on Hugging Face"
          >
            <span>Hugging Face</span>
            <ExternalLink className="w-3 h-3" />
          </a>
        </div>
      </div>
    </header>
  );
}

