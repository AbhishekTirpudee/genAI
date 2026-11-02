import React, { useState } from 'react';
import { Sliders, ChevronDown, ChevronUp, Shuffle, Monitor, Smartphone, Square, Tv } from 'lucide-react';
import { ASPECT_RATIOS } from '../constants/styles';

export default function AdvancedOptions({
  aspectRatio,
  setAspectRatio,
  steps,
  setSteps,
  seed,
  setSeed,
  disabled
}) {
  const [isOpen, setIsOpen] = useState(false);

  const getAspectIcon = (iconName) => {
    switch (iconName) {
      case 'Monitor': return <Monitor className="w-3.5 h-3.5" />;
      case 'Smartphone': return <Smartphone className="w-3.5 h-3.5" />;
      case 'Tv': return <Tv className="w-3.5 h-3.5" />;
      default: return <Square className="w-3.5 h-3.5" />;
    }
  };

  const handleRandomSeed = () => {
    setSeed(Math.floor(Math.random() * 1000000000));
  };

  return (
    <div className="border border-slate-800 rounded-xl bg-slate-900/40 overflow-hidden">
      <button
        type="button"
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-4 py-3 text-sm font-medium text-slate-300 hover:text-white transition-colors"
      >
        <span className="flex items-center gap-2">
          <Sliders className="w-4 h-4 text-purple-400" />
          <span>Advanced Parameters</span>
          <span className="text-[11px] text-slate-500 font-mono">
            ({aspectRatio.label}, {steps} steps)
          </span>
        </span>
        {isOpen ? <ChevronUp className="w-4 h-4 text-slate-400" /> : <ChevronDown className="w-4 h-4 text-slate-400" />}
      </button>

      {isOpen && (
        <div className="px-4 pb-4 pt-1 space-y-4 border-t border-slate-800/80">
          {/* Aspect Ratio */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-300 font-medium">Aspect Ratio & Resolution</span>
              <span className="font-mono text-purple-400">{aspectRatio.width} × {aspectRatio.height}px</span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
              {ASPECT_RATIOS.map((ratio) => {
                const isSelected = aspectRatio.id === ratio.id;
                return (
                  <button
                    key={ratio.id}
                    type="button"
                    disabled={disabled}
                    onClick={() => setAspectRatio(ratio)}
                    className={`flex flex-col items-center justify-center p-2 rounded-lg border text-xs transition-all ${
                      isSelected
                        ? 'bg-purple-950/50 border-purple-500 text-purple-200'
                        : 'bg-slate-900 border-slate-800 text-slate-400 hover:text-slate-200 hover:border-slate-700'
                    } disabled:opacity-50`}
                  >
                    <div className="mb-1">{getAspectIcon(ratio.icon)}</div>
                    <span className="font-semibold">{ratio.id}</span>
                    <span className="text-[10px] text-slate-500">{ratio.width}x{ratio.height}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* Inference Steps */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-300 font-medium">Inference Steps</span>
              <span className="font-mono text-purple-400">{steps} steps</span>
            </div>
            <div className="flex items-center gap-3">
              <input
                type="range"
                min="1"
                max="8"
                step="1"
                value={steps}
                disabled={disabled}
                onChange={(e) => setSteps(Number(e.target.value))}
                className="w-full accent-purple-500 bg-slate-800 h-1.5 rounded-lg cursor-pointer"
              />
              <span className="text-xs font-mono text-slate-400 w-6 text-right">{steps}</span>
            </div>
            <p className="text-[11px] text-slate-500">
              FLUX.1-schnell is distilled for 4 steps. 4 steps gives top results in ~2-4s.
            </p>
          </div>

          {/* Seed Input */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-300 font-medium">Seed (Reproducibility)</span>
              {seed !== null && seed !== "" && (
                <button
                  type="button"
                  onClick={() => setSeed(null)}
                  className="text-[11px] text-purple-400 hover:underline"
                >
                  Reset to Random
                </button>
              )}
            </div>
            <div className="flex items-center gap-2">
              <input
                type="number"
                placeholder="Random seed (empty for random)"
                value={seed !== null ? seed : ""}
                disabled={disabled}
                onChange={(e) => setSeed(e.target.value === "" ? null : Number(e.target.value))}
                className="flex-1 bg-slate-900 text-slate-200 placeholder-slate-600 border border-slate-800 focus:border-purple-500 rounded-lg px-3 py-1.5 text-xs font-mono focus:outline-none focus:ring-1 focus:ring-purple-500"
              />
              <button
                type="button"
                onClick={handleRandomSeed}
                disabled={disabled}
                className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg border border-slate-700 transition-colors"
                title="Generate random seed"
              >
                <Shuffle className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

