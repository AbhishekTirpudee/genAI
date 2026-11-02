import React, { useState, useEffect } from 'react';
import {
  Download,
  Maximize2,
  Copy,
  Check,
  Sparkles,
  Clock,
  Layers,
  FileImage,
  RefreshCw,
  X,
  ExternalLink
} from 'lucide-react';
import { downloadPngFromBase64 } from '../services/api';
import { GENERATION_TIPS } from '../constants/styles';

export default function ImageDisplay({
  currentImage,
  isGenerating,
  onRegenerate,
  error
}) {
  const [copied, setCopied] = useState(false);
  const [isZoomOpen, setIsZoomOpen] = useState(false);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [tipIndex, setTipIndex] = useState(0);

  // Timer for loading state
  useEffect(() => {
    let timer;
    if (isGenerating) {
      setElapsedTime(0);
      timer = setInterval(() => {
        setElapsedTime((prev) => +(prev + 0.1).toFixed(1));
      }, 100);
    }
    return () => clearInterval(timer);
  }, [isGenerating]);

  // Rotate tips while generating
  useEffect(() => {
    let tipInterval;
    if (isGenerating) {
      tipInterval = setInterval(() => {
        setTipIndex((prev) => (prev + 1) % GENERATION_TIPS.length);
      }, 3500);
    }
    return () => clearInterval(tipInterval);
  }, [isGenerating]);

  const handleDownload = () => {
    if (!currentImage?.image_base64) return;
    const sanitizedPrompt = (currentImage.prompt || "artwork")
      .toLowerCase()
      .replace(/[^a-z0-9]/g, "-")
      .slice(0, 32);
    const filename = `dreamcanvas-${sanitizedPrompt}-${Date.now()}.png`;
    downloadPngFromBase64(currentImage.image_base64, filename);
  };

  const handleCopyPrompt = () => {
    if (!currentImage?.prompt) return;
    navigator.clipboard.writeText(currentImage.prompt);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Canvas Header */}
      <div className="flex items-center justify-between pb-3 border-b border-slate-800 mb-3">
        <div className="flex items-center gap-2">
          <FileImage className="w-4 h-4 text-purple-400" />
          <h2 className="text-sm font-semibold text-slate-200">Generated Canvas</h2>
          {currentImage && (
            <span className="text-[11px] font-mono text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full">
              Lossless PNG
            </span>
          )}
        </div>

        {currentImage && !isGenerating && (
          <div className="flex items-center gap-2">
            <button
              onClick={handleCopyPrompt}
              className="inline-flex items-center gap-1.5 text-xs text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 px-2.5 py-1.5 rounded-lg border border-slate-700 transition-colors"
              title="Copy original prompt"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? "Copied" : "Copy Prompt"}</span>
            </button>

            <button
              onClick={() => setIsZoomOpen(true)}
              className="p-1.5 text-slate-300 hover:text-white bg-slate-800 hover:bg-slate-700 rounded-lg border border-slate-700 transition-colors"
              title="Full screen preview"
            >
              <Maximize2 className="w-4 h-4" />
            </button>

            <button
              onClick={handleDownload}
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-white bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-500 hover:to-indigo-500 px-3 py-1.5 rounded-lg shadow-md shadow-purple-600/30 transition-all active:scale-95"
              title="Download image as PNG"
            >
              <Download className="w-3.5 h-3.5" />
              <span>Download PNG</span>
            </button>
          </div>
        )}
      </div>

      {/* Main Display Area */}
      <div className="relative flex-1 min-h-[420px] rounded-2xl border border-slate-800 bg-[#06080d] overflow-hidden flex items-center justify-center p-3">
        {/* Loading State */}
        {isGenerating && (
          <div className="flex flex-col items-center justify-center text-center p-6 max-w-md w-full space-y-6 animate-in fade-in duration-300">
            {/* Shimmer glowing canvas preview */}
            <div className="relative w-48 h-48 sm:w-56 sm:h-56 rounded-2xl overflow-hidden border border-purple-500/30 shadow-2xl shadow-purple-900/40 bg-slate-900/90 flex items-center justify-center">
              <div className="absolute inset-0 bg-gradient-to-tr from-purple-900/40 via-indigo-900/40 to-pink-900/20 animate-pulse" />
              <div className="absolute -inset-1 bg-gradient-to-r from-purple-600 to-pink-600 rounded-2xl blur-lg opacity-30 animate-pulse-glow" />
              
              <div className="relative z-10 flex flex-col items-center gap-3">
                <div className="w-12 h-12 rounded-xl bg-purple-600/20 border border-purple-500/40 flex items-center justify-center">
                  <Sparkles className="w-6 h-6 text-purple-400 animate-spin-slow" />
                </div>
                <div className="flex items-center gap-1.5 text-xs font-mono text-purple-300 bg-purple-950/60 px-2.5 py-1 rounded-full border border-purple-500/30">
                  <Clock className="w-3 h-3 animate-spin" />
                  <span>{elapsedTime.toFixed(1)}s elapsed</span>
                </div>
              </div>
            </div>

            {/* Status Text */}
            <div className="space-y-2">
              <h3 className="font-semibold text-slate-100 text-base">
                Synthesizing with FLUX.1-schnell
              </h3>
              <p className="text-xs text-slate-400">
                Executing Hugging Face inference pipeline & encoding PNG with Pillow
              </p>
            </div>

            {/* Rotating Pro Tip */}
            <div className="w-full bg-slate-900/80 border border-slate-800/80 rounded-xl p-3 text-left">
              <div className="flex items-center gap-1.5 text-[10px] font-semibold tracking-wider text-purple-400 uppercase mb-1">
                <Sparkles className="w-3 h-3" />
                <span>FLUX Tip</span>
              </div>
              <p className="text-xs text-slate-300 italic">
                "{GENERATION_TIPS[tipIndex]}"
              </p>
            </div>
          </div>
        )}

        {/* Display Generated Image */}
        {!isGenerating && currentImage && (
          <div className="relative w-full h-full flex flex-col items-center justify-center group">
            <div className="relative max-h-[500px] w-auto max-w-full rounded-xl overflow-hidden shadow-2xl border border-slate-700/50 bg-black">
              <img
                src={`data:image/png;base64,${currentImage.image_base64}`}
                alt={currentImage.prompt}
                className="max-h-[500px] w-auto object-contain cursor-pointer transition-transform duration-300 group-hover:scale-[1.01]"
                onClick={() => setIsZoomOpen(true)}
              />
              
              {/* Overlay on hover */}
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity flex items-end p-4 pointer-events-none">
                <p className="text-xs text-white line-clamp-2 drop-shadow-md">
                  {currentImage.prompt}
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Empty State */}
        {!isGenerating && !currentImage && (
          <div className="flex flex-col items-center justify-center text-center p-8 max-w-md space-y-4">
            <div className="w-16 h-16 rounded-2xl bg-slate-900 border border-slate-800 flex items-center justify-center shadow-inner">
              <Sparkles className="w-8 h-8 text-purple-400/60" />
            </div>
            <div className="space-y-1">
              <h3 className="font-semibold text-slate-200 text-base">Your canvas is waiting</h3>
              <p className="text-xs text-slate-400 max-w-xs leading-relaxed">
                Enter your text prompt, pick a style preset, and hit Generate to create images with FLUX.1-schnell.
              </p>
            </div>
            <div className="grid grid-cols-2 gap-2 w-full pt-2 text-left">
              <div className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800/80">
                <div className="text-[11px] font-semibold text-purple-300">⚡ Fast Latency</div>
                <div className="text-[10px] text-slate-400">4-step FLUX Schnell architecture</div>
              </div>
              <div className="p-2.5 rounded-lg bg-slate-900/60 border border-slate-800/80">
                <div className="text-[11px] font-semibold text-purple-300">🖼️ Lossless PNG</div>
                <div className="text-[10px] text-slate-400">Pillow RGBA rendering & export</div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Image Metadata Bar */}
      {currentImage && !isGenerating && (
        <div className="mt-3 grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
          <div className="bg-slate-900/70 border border-slate-800 px-3 py-2 rounded-lg">
            <span className="text-slate-500 block text-[10px] uppercase tracking-wider">Resolution</span>
            <span className="font-mono text-slate-200 font-semibold">{currentImage.width} × {currentImage.height} px</span>
          </div>
          <div className="bg-slate-900/70 border border-slate-800 px-3 py-2 rounded-lg">
            <span className="text-slate-500 block text-[10px] uppercase tracking-wider">Speed</span>
            <span className="font-mono text-emerald-400 font-semibold">{currentImage.generation_time_seconds}s</span>
          </div>
          <div className="bg-slate-900/70 border border-slate-800 px-3 py-2 rounded-lg">
            <span className="text-slate-500 block text-[10px] uppercase tracking-wider">Style</span>
            <span className="text-purple-300 font-semibold capitalize">{currentImage.style}</span>
          </div>
          <div className="bg-slate-900/70 border border-slate-800 px-3 py-2 rounded-lg">
            <span className="text-slate-500 block text-[10px] uppercase tracking-wider">Seed</span>
            <span className="font-mono text-slate-300">{currentImage.seed ?? "Random"}</span>
          </div>
        </div>
      )}

      {/* Lightbox / Zoom Modal */}
      {isZoomOpen && currentImage && (
        <div className="fixed inset-0 z-50 bg-black/90 backdrop-blur-md flex items-center justify-center p-4">
          <div className="relative max-w-5xl max-h-[90vh] w-full flex flex-col items-center">
            {/* Modal Controls */}
            <div className="w-full flex items-center justify-between pb-3 text-white">
              <div className="text-xs truncate max-w-lg text-slate-300">
                {currentImage.prompt}
              </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={handleDownload}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-xs font-medium text-white transition-colors"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download</span>
                </button>
                <button
                  onClick={() => setIsZoomOpen(false)}
                  className="p-1.5 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white transition-colors"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
            </div>

            {/* Modal Image */}
            <div className="overflow-auto rounded-xl border border-slate-800 bg-black/60 max-h-[80vh] flex items-center justify-center">
              <img
                src={`data:image/png;base64,${currentImage.image_base64}`}
                alt={currentImage.prompt}
                className="max-h-[80vh] max-w-full object-contain"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

