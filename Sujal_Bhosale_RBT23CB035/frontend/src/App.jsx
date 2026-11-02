import React, { useState, useEffect } from 'react';
import { Sparkles, Wand2, AlertTriangle, ArrowRight, RefreshCw, Zap } from 'lucide-react';

import Header from './components/Header';
import PromptInput from './components/PromptInput';
import StyleSelector from './components/StyleSelector';
import AdvancedOptions from './components/AdvancedOptions';
import ImageDisplay from './components/ImageDisplay';
import HistoryGallery from './components/HistoryGallery';
import Toast from './components/Toast';

import { checkHealth, generateImage } from './services/api';
import { ASPECT_RATIOS } from './constants/styles';

export default function App() {
  // App state
  const [prompt, setPrompt] = useState('');
  const [selectedStyle, setSelectedStyle] = useState('photorealistic');
  const [aspectRatio, setAspectRatio] = useState(ASPECT_RATIOS[0]);
  const [steps, setSteps] = useState(4);
  const [seed, setSeed] = useState(null);

  // Generation & Status state
  const [isGenerating, setIsGenerating] = useState(false);
  const [currentImage, setCurrentImage] = useState(null);
  const [history, setHistory] = useState([]);
  const [health, setHealth] = useState(null);
  const [isCheckingHealth, setIsCheckingHealth] = useState(true);
  const [toast, setToast] = useState(null);

  const showToast = (message, type = 'info', title = null) => {
    setToast({ message, type, title });
  };

  // Check backend health on mount
  useEffect(() => {
    async function loadHealth() {
      try {
        setIsCheckingHealth(true);
        const data = await checkHealth();
        setHealth(data);
        if (!data.token_configured) {
          showToast(
            'Backend is running, but HF_TOKEN is not configured in backend/.env.',
            'info',
            'Hugging Face Token Required'
          );
        }
      } catch (err) {
        setHealth({ status: 'offline', token_configured: false });
        showToast(
          'Could not connect to FastAPI backend at http://localhost:8000. Ensure the backend server is running.',
          'error',
          'Backend Offline'
        );
      } finally {
        setIsCheckingHealth(false);
      }
    }
    loadHealth();
  }, []);

  const handleGenerate = async () => {
    const trimmed = prompt.trim();
    if (!trimmed) {
      showToast('Please enter a prompt describing what you want to generate.', 'error', 'Missing Prompt');
      return;
    }

    setIsGenerating(true);

    try {
      const payload = {
        prompt: trimmed,
        style: selectedStyle,
        width: aspectRatio.width,
        height: aspectRatio.height,
        num_inference_steps: steps,
        seed: seed !== null ? Number(seed) : null,
      };

      const result = await generateImage(payload);

      if (result.success && result.image_base64) {
        setCurrentImage(result);
        setHistory((prev) => [result, ...prev]);
        showToast(
          `Image generated in ${result.generation_time_seconds}s (${result.width}x${result.height} PNG)`,
          'success',
          'Artwork Ready!'
        );
      } else {
        throw new Error('Image generation completed without valid image data.');
      }
    } catch (err) {
      console.error('Generation error:', err);
      showToast(
        err.message || 'Failed to generate image. Please verify your HF_TOKEN and try again.',
        'error',
        'Generation Error'
      );
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#07090e] text-slate-100 flex flex-col font-sans">
      <Header health={health} isCheckingHealth={isCheckingHealth} />

      {/* Main Workspace */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 flex flex-col gap-6">
        {/* Token Alert Banner if not configured */}
        {health && !health.token_configured && (
          <div className="bg-purple-950/40 border border-purple-500/30 rounded-xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-sm text-purple-200">
            <div className="flex items-center gap-2.5">
              <AlertTriangle className="w-5 h-5 text-purple-400 flex-shrink-0" />
              <span>
                <strong>Hugging Face Token Setup:</strong> Add your token to{' '}
                <code className="bg-purple-900/50 px-1.5 py-0.5 rounded text-xs text-white">backend/.env</code>{' '}
                as <code className="bg-purple-900/50 px-1.5 py-0.5 rounded text-xs text-white">HF_TOKEN=hf_...</code> to enable live image generation.
              </span>
            </div>
            <a
              href="https://huggingface.co/settings/tokens"
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs bg-purple-600 hover:bg-purple-500 text-white font-medium px-3 py-1.5 rounded-lg transition-colors whitespace-nowrap self-end sm:self-auto"
            >
              Get Free HF Token →
            </a>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Generation Controls */}
          <section className="lg:col-span-5 flex flex-col gap-5 bg-[#0d111a]/80 backdrop-blur-xl border border-slate-800/80 rounded-2xl p-5 shadow-xl">
            {/* 1. Prompt Input */}
            <PromptInput
              prompt={prompt}
              setPrompt={setPrompt}
              onGenerate={handleGenerate}
              isGenerating={isGenerating}
            />

            {/* 2. Style Selector */}
            <StyleSelector
              selectedStyle={selectedStyle}
              onSelectStyle={setSelectedStyle}
              disabled={isGenerating}
            />

            {/* 3. Advanced Parameters (Aspect ratio, Steps, Seed) */}
            <AdvancedOptions
              aspectRatio={aspectRatio}
              setAspectRatio={setAspectRatio}
              steps={steps}
              setSteps={setSteps}
              seed={seed}
              setSeed={setSeed}
              disabled={isGenerating}
            />

            {/* 4. Generate Button */}
            <div className="pt-2">
              <button
                type="button"
                onClick={handleGenerate}
                disabled={isGenerating || !prompt.trim()}
                className={`w-full relative group overflow-hidden rounded-xl font-bold text-sm sm:text-base py-3.5 px-6 transition-all duration-300 shadow-xl flex items-center justify-center gap-2.5 ${
                  isGenerating
                    ? 'bg-purple-900/60 text-purple-300 border border-purple-500/30 cursor-wait'
                    : !prompt.trim()
                    ? 'bg-slate-800 text-slate-500 border border-slate-700/50 cursor-not-allowed'
                    : 'bg-gradient-to-r from-purple-600 via-indigo-600 to-pink-600 hover:from-purple-500 hover:via-indigo-500 hover:to-pink-500 text-white shadow-purple-600/30 active:scale-[0.99] border border-purple-400/30'
                }`}
              >
                {isGenerating ? (
                  <>
                    <RefreshCw className="w-5 h-5 animate-spin text-purple-300" />
                    <span>Generating Artwork with FLUX...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-5 h-5 text-pink-300 group-hover:rotate-12 transition-transform duration-300" />
                    <span>Generate Artwork</span>
                    <ArrowRight className="w-4 h-4 ml-1 opacity-70 group-hover:translate-x-1 transition-transform" />
                  </>
                )}
              </button>
            </div>
          </section>

          {/* Right Column: Canvas Display */}
          <section className="lg:col-span-7 flex flex-col gap-4 bg-[#0d111a]/80 backdrop-blur-xl border border-slate-800/80 rounded-2xl p-5 shadow-xl">
            <ImageDisplay
              currentImage={currentImage}
              isGenerating={isGenerating}
              onRegenerate={handleGenerate}
            />
          </section>
        </div>

        {/* Bottom Section: Session Gallery */}
        <HistoryGallery
          history={history}
          selectedImage={currentImage}
          onSelectImage={setCurrentImage}
          onClearHistory={() => setHistory([])}
        />
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800/80 bg-[#0a0d14] py-6 mt-12 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-slate-400">
            <span className="font-semibold text-slate-300">DreamCanvas</span>
            <span>—</span>
            <span>Powered by <strong className="text-purple-300">black-forest-labs/FLUX.1-schnell</strong> &amp; Hugging Face</span>
          </div>
          <div className="flex items-center gap-4 text-slate-500">
            <span>FastAPI + Pillow PNG</span>
            <span>•</span>
            <span>React + Vite + Tailwind CSS</span>
          </div>
        </div>
      </footer>

      {/* Global Toast */}
      <Toast toast={toast} onClose={() => setToast(null)} />
    </div>
  );
}
