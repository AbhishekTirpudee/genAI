import React from 'react';
import { Sparkles, Dices, X, Wand2 } from 'lucide-react';
import { SAMPLE_PROMPTS } from '../constants/styles';

export default function PromptInput({
  prompt,
  setPrompt,
  onGenerate,
  isGenerating,
  maxLength = 1000
}) {
  const handleRandomize = () => {
    const randomIndex = Math.floor(Math.random() * SAMPLE_PROMPTS.length);
    setPrompt(SAMPLE_PROMPTS[randomIndex]);
  };

  const handleKeyDown = (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
      e.preventDefault();
      if (prompt.trim() && !isGenerating) {
        onGenerate();
      }
    }
  };

  const handleClear = () => {
    setPrompt('');
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <label className="text-sm font-semibold text-slate-200 flex items-center gap-2">
          <Wand2 className="w-4 h-4 text-purple-400" />
          <span>Describe your vision</span>
        </label>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleRandomize}
            disabled={isGenerating}
            className="inline-flex items-center gap-1.5 text-xs font-medium text-purple-400 hover:text-purple-300 bg-purple-500/10 hover:bg-purple-500/20 border border-purple-500/20 px-2.5 py-1 rounded-lg transition-all active:scale-95 disabled:opacity-50"
            title="Insert a randomized creative prompt"
          >
            <Dices className="w-3.5 h-3.5" />
            <span>Surprise Me</span>
          </button>
          {prompt.length > 0 && (
            <button
              type="button"
              onClick={handleClear}
              disabled={isGenerating}
              className="text-xs text-slate-400 hover:text-slate-200 p-1 rounded hover:bg-slate-800 transition-colors"
              title="Clear prompt"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      <div className="relative group">
        <textarea
          value={prompt}
          onChange={(e) => setPrompt(e.target.value.slice(0, maxLength))}
          onKeyDown={handleKeyDown}
          disabled={isGenerating}
          rows={3}
          placeholder="e.g. A solitary cyberpunk astronaut walking through glowing lavender crystals on Saturn's moon..."
          className="w-full bg-slate-900/90 text-slate-100 placeholder-slate-500 border border-slate-750 focus:border-purple-500 rounded-xl p-3.5 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-purple-500/30 transition-all shadow-inner disabled:opacity-60"
        />
        <div className="absolute right-3 bottom-3 flex items-center gap-2 pointer-events-none text-[11px] text-slate-500 font-mono">
          <span className="hidden sm:inline">Ctrl + Enter to generate</span>
          <span>•</span>
          <span className={prompt.length > maxLength * 0.9 ? 'text-amber-400 font-semibold' : ''}>
            {prompt.length}/{maxLength}
          </span>
        </div>
      </div>

      {/* Suggested Inspiration Pills */}
      <div className="space-y-1.5">
        <span className="text-[11px] text-slate-400 uppercase tracking-wider font-semibold">Quick Ideas</span>
        <div className="flex flex-wrap gap-1.5">
          {SAMPLE_PROMPTS.slice(0, 4).map((p, idx) => (
            <button
              key={idx}
              type="button"
              disabled={isGenerating}
              onClick={() => setPrompt(p)}
              className="text-xs text-left bg-slate-900/80 hover:bg-slate-800/90 text-slate-300 hover:text-white border border-slate-800 hover:border-slate-700 px-2.5 py-1 rounded-lg transition-colors truncate max-w-full active:scale-98 disabled:opacity-50"
            >
              {p}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}

