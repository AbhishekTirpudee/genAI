import React, { useEffect } from 'react';
import { AlertCircle, CheckCircle, Info, X } from 'lucide-react';

export default function Toast({ toast, onClose }) {
  useEffect(() => {
    if (!toast) return;
    const timer = setTimeout(() => {
      onClose();
    }, 6000);
    return () => clearTimeout(timer);
  }, [toast, onClose]);

  if (!toast) return null;

  const isError = toast.type === 'error';
  const isSuccess = toast.type === 'success';

  return (
    <div className="fixed bottom-6 right-6 z-50 max-w-md w-full animate-in fade-in slide-in-from-bottom-5 duration-200">
      <div className={`p-4 rounded-xl shadow-2xl border flex items-start gap-3 backdrop-blur-xl ${
        isError
          ? 'bg-red-950/90 border-red-500/40 text-red-100 shadow-red-950/50'
          : isSuccess
          ? 'bg-emerald-950/90 border-emerald-500/40 text-emerald-100 shadow-emerald-950/50'
          : 'bg-slate-900/90 border-purple-500/40 text-slate-100 shadow-purple-950/50'
      }`}>
        <div className="mt-0.5 flex-shrink-0">
          {isError && <AlertCircle className="w-5 h-5 text-red-400" />}
          {isSuccess && <CheckCircle className="w-5 h-5 text-emerald-400" />}
          {!isError && !isSuccess && <Info className="w-5 h-5 text-purple-400" />}
        </div>
        
        <div className="flex-1 text-sm leading-relaxed pr-2">
          {toast.title && <div className="font-semibold mb-0.5">{toast.title}</div>}
          <div className="text-slate-300 break-words">{toast.message}</div>
        </div>

        <button
          onClick={onClose}
          className="text-slate-400 hover:text-white transition-colors p-1 -mr-1 rounded-lg hover:bg-white/10"
          aria-label="Close notification"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

