import React, { useState } from 'react';
import { Palette, Check } from 'lucide-react';
import { STYLES } from '../constants/styles';

export default function StyleSelector({ selectedStyle, onSelectStyle, disabled }) {
  const [activeCategory, setActiveCategory] = useState("All");

  const categories = ["All", "Realism", "Illustration", "Sci-Fi", "Artistic", "3D", "Fine Art", "Retro"];

  const filteredStyles = activeCategory === "All"
    ? STYLES
    : STYLES.filter(s => s.category === activeCategory || (activeCategory === "Realism" && s.id === "none"));

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <label className="text-sm font-semibold text-slate-200 flex items-center gap-2">
          <Palette className="w-4 h-4 text-purple-400" />
          <span>Artistic Style Preset</span>
        </label>
        <span className="text-xs text-purple-400 font-medium">
          {STYLES.find(s => s.id === selectedStyle)?.name || "Select Style"}
        </span>
      </div>

      {/* Category Pills */}
      <div className="flex items-center gap-1.5 overflow-x-auto pb-1 no-scrollbar text-xs">
        {categories.map(cat => (
          <button
            key={cat}
            type="button"
            onClick={() => setActiveCategory(cat)}
            disabled={disabled}
            className={`px-2.5 py-1 rounded-lg font-medium whitespace-nowrap transition-all ${
              activeCategory === cat
                ? 'bg-purple-600 text-white shadow-sm shadow-purple-600/30'
                : 'bg-slate-900/60 text-slate-400 hover:text-slate-200 hover:bg-slate-800 border border-slate-800'
            }`}
          >
            {cat}
          </button>
        ))}
      </div>

      {/* Style Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 gap-2.5 max-h-[290px] overflow-y-auto pr-1">
        {filteredStyles.map((style) => {
          const isSelected = selectedStyle === style.id;
          return (
            <button
              key={style.id}
              type="button"
              disabled={disabled}
              onClick={() => onSelectStyle(style.id)}
              className={`relative flex flex-col items-start p-2.5 rounded-xl text-left border transition-all active:scale-[0.98] ${
                isSelected
                  ? 'bg-purple-950/40 border-purple-500 shadow-md shadow-purple-500/10 ring-1 ring-purple-500'
                  : 'bg-slate-900/70 border-slate-800 hover:border-slate-700 hover:bg-slate-800/80'
              } disabled:opacity-50`}
            >
              <div className="w-full flex items-center justify-between mb-1.5">
                <span className="text-xl">{style.emoji}</span>
                {isSelected ? (
                  <span className="w-4 h-4 rounded-full bg-purple-500 text-white flex items-center justify-center">
                    <Check className="w-2.5 h-2.5 stroke-[3]" />
                  </span>
                ) : (
                  <span className="text-[10px] text-slate-500 font-mono bg-slate-800 px-1.5 py-0.5 rounded">
                    {style.badge}
                  </span>
                )}
              </div>
              <div className="font-semibold text-xs text-slate-200 truncate w-full mb-0.5">
                {style.name}
              </div>
              <div className="text-[11px] text-slate-400 line-clamp-2 leading-snug">
                {style.description}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

