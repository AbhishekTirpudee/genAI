import React, { useState, useEffect } from 'react';
import {
  Sparkles,
  Image as ImageIcon,
  Download,
  RefreshCw,
  Layers,
  Settings,
  Eye,
  Sliders,
  CheckCircle2,
  Cpu,
  Wand2,
  Calendar,
  MapPin,
  Palette,
  Tag,
  ArrowRight,
  BookOpen,
  Info,
  History,
  Copy,
  Check
} from 'lucide-react';
import confetti from 'canvas-confetti';
import { createCompositePoster, downloadDataUrl } from './utils/canvasExport';

// Presets for quick lab testing
const SAMPLE_EVENTS = [
  {
    title: "HackNova 2026: AI & Web3",
    description: "Annual 24-hour national hackathon for developers building next-gen autonomous AI agents and decentralized protocols.",
    theme: "Hackathon",
    style: "Futuristic",
    colorPreference: "Neon Cyber",
    date: "October 14-15, 2026",
    venue: "Innovation Tech Hub, Silicon Bay"
  },
  {
    title: "Sonic Horizon Music Fest",
    description: "Open-air indie electronic music festival featuring live synthesizers, laser visualizers, and acoustic stages.",
    theme: "Music",
    style: "Modern",
    colorPreference: "Electric Blue & Purple",
    date: "December 05, 2026",
    venue: "Sunset Amphitheatre, Coast Arena"
  },
  {
    title: "Virasat: National Cultural Gala",
    description: "A celebration of traditional heritage, classical dance performances, artisanal exhibitions, and culinary arts.",
    theme: "Cultural",
    style: "Vintage",
    colorPreference: "Warm Sunset",
    date: "November 20, 2026",
    venue: "Grand Heritage Convention Hall"
  },
  {
    title: "RoboVanguard: Autonomous Robotics Expo",
    description: "Showcase of combat robotics, humanoid AI navigation, and drone obstacle agility races.",
    theme: "Technical",
    style: "3D",
    colorPreference: "Monochromatic",
    date: "January 18, 2027",
    venue: "National Exhibition Pavilion"
  }
];

export default function App() {
  // Form Inputs
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [theme, setTheme] = useState('Technical');
  const [style, setStyle] = useState('Modern');
  const [colorPreference, setColorPreference] = useState('Neon Cyber');
  const [aspectRatio, setAspectRatio] = useState('3:4');
  const [date, setDate] = useState('');
  const [venue, setVenue] = useState('');

  // Generation state
  const [isLoading, setIsLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(1);
  const [generationResult, setGenerationResult] = useState(null);
  const [variations, setVariations] = useState([]);
  const [isLoadingVariations, setIsLoadingVariations] = useState(false);
  const [error, setError] = useState(null);

  // UI state
  const [showOverlay, setShowOverlay] = useState(true);
  const [copiedPrompt, setCopiedPrompt] = useState(false);
  const [showSettings, setShowSettings] = useState(false);
  const [customApiKey, setCustomApiKey] = useState('');
  const [history, setHistory] = useState([]);
  const [activeTab, setActiveTab] = useState('poster'); // 'poster' | 'prompt' | 'variations'

  // Load history from localStorage on mount
  useEffect(() => {
    try {
      const savedHistory = localStorage.getItem('posterai_history');
      if (savedHistory) setHistory(JSON.parse(savedHistory));
      const savedKey = localStorage.getItem('posterai_gemini_key');
      if (savedKey) setCustomApiKey(savedKey);
    } catch (e) {
      console.warn("Storage access failed:", e);
    }
  }, []);

  // Save history helper
  const saveToHistory = (item) => {
    const updated = [item, ...history.filter(h => h.image?.filename !== item.image?.filename)].slice(0, 8);
    setHistory(updated);
    try {
      localStorage.setItem('posterai_history', JSON.stringify(updated));
    } catch (e) {
      console.warn("Failed saving history:", e);
    }
  };

  // Quick load sample preset
  const loadPreset = (preset) => {
    setTitle(preset.title);
    setDescription(preset.description);
    setTheme(preset.theme);
    setStyle(preset.style);
    setColorPreference(preset.colorPreference);
    setDate(preset.date);
    setVenue(preset.venue);
  };

  // Step 2 & 3: Run Full GenAI Pipeline
  const handleGenerate = async (e) => {
    if (e) e.preventDefault();
    if (!title.trim() || !description.trim()) {
      setError("Please provide at least an Event Title and Description.");
      return;
    }

    setError(null);
    setIsLoading(true);
    setLoadingStep(1);
    setVariations([]);
    setActiveTab('poster');

    // Simulate animated step progression for UI responsiveness
    const stepTimer1 = setTimeout(() => setLoadingStep(2), 1200);
    const stepTimer2 = setTimeout(() => setLoadingStep(3), 3200);

    try {
      const response = await fetch('/api/generate-poster', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: title.trim(),
          description: description.trim(),
          theme,
          style,
          colorPreference,
          aspectRatio,
          date: date.trim(),
          venue: venue.trim(),
          customApiKey: customApiKey.trim() || undefined
        })
      });

      const data = await response.json();
      if (!data.success) {
        throw new Error(data.error || 'Failed to generate poster');
      }

      setGenerationResult(data);
      saveToHistory(data);
      confetti({
        particleCount: 75,
        spread: 60,
        origin: { y: 0.6 }
      });
    } catch (err) {
      console.error(err);
      setError(err.message || 'Error occurred while contacting GenAI service.');
    } finally {
      clearTimeout(stepTimer1);
      clearTimeout(stepTimer2);
      setIsLoading(false);
    }
  };

  // Step 5: Regenerate with fresh seed
  const handleRegenerate = () => {
    handleGenerate();
  };

  // Step 5: Generate Variations
  const handleGenerateVariations = async () => {
    if (!generationResult?.enhancedPrompt?.full_enhanced_prompt) return;
    setIsLoadingVariations(true);
    try {
      const response = await fetch('/api/generate-variations', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          prompt: generationResult.enhancedPrompt.full_enhanced_prompt,
          aspectRatio: generationResult.rawInput.aspectRatio || '3:4',
          count: 3,
          customApiKey: customApiKey.trim() || undefined
        })
      });
      const data = await response.json();
      if (data.success && data.variations) {
        setVariations(data.variations);
        setActiveTab('variations');
      }
    } catch (err) {
      console.error(err);
      alert("Failed generating variations: " + err.message);
    } finally {
      setIsLoadingVariations(false);
    }
  };

  // Step 5: Download Poster with composite text-overlay layer
  const handleDownload = async () => {
    if (!generationResult) return;
    try {
      const imgSource = generationResult.image.base64 || generationResult.image.localUrl;
      const compositeDataUrl = await createCompositePoster({
        imageUrl: imgSource,
        title: generationResult.rawInput.title,
        theme: generationResult.rawInput.theme,
        style: generationResult.rawInput.style,
        date: generationResult.rawInput.date,
        venue: generationResult.rawInput.venue,
        includeOverlay: showOverlay
      });

      const safeTitle = generationResult.rawInput.title.replace(/[^a-zA-Z0-9]/g, '_').toLowerCase();
      downloadDataUrl(compositeDataUrl, `poster_${safeTitle}.png`);
    } catch (err) {
      console.error(err);
      alert("Download failed: " + err.message);
    }
  };

  // Copy enhanced prompt
  const handleCopyPrompt = () => {
    if (!generationResult?.enhancedPrompt?.full_enhanced_prompt) return;
    navigator.clipboard.writeText(generationResult.enhancedPrompt.full_enhanced_prompt);
    setCopiedPrompt(true);
    setTimeout(() => setCopiedPrompt(false), 2000);
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col selection:bg-indigo-600 selection:text-white">
      {/* 1. Header / Navbar */}
      <header className="sticky top-0 z-40 bg-slate-900/80 backdrop-blur-md border-b border-slate-800 px-4 lg:px-8 py-3.5">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 via-violet-600 to-pink-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold tracking-tight bg-gradient-to-r from-white via-slate-200 to-slate-400 bg-clip-text text-transparent">
                PosterAI
              </h1>
              <span className="text-xs text-indigo-400 font-medium tracking-wide uppercase">Generative Poster Studio</span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-2 bg-slate-800/80 px-3 py-1.5 rounded-lg border border-slate-700/60 text-xs text-slate-300">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span>AI Engine: <strong>FLUX.1 / Imagen 3</strong></span>
            </div>
            
            <button
              onClick={() => setShowSettings(!showSettings)}
              className="p-2 rounded-lg bg-slate-800 hover:bg-slate-700 border border-slate-700 text-slate-300 transition-colors flex items-center gap-1.5 text-xs font-medium"
              title="API Configuration"
            >
              <Settings className="w-4 h-4" />
              <span className="hidden md:inline">API Key</span>
            </button>
          </div>
        </div>
      </header>

      {/* Optional Settings Modal */}
      {showSettings && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-slate-900 border border-slate-800 rounded-2xl max-w-md w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-semibold text-lg flex items-center gap-2 text-white">
                <Settings className="w-5 h-5 text-indigo-400" />
                AI API Configuration
              </h3>
              <button onClick={() => setShowSettings(false)} className="text-slate-400 hover:text-white">✕</button>
            </div>
            <p className="text-xs text-slate-400">
              By default, PosterAI utilizes the built-in <strong>FLUX.1 Neural Engine & LLM Prompt Synthesizer</strong> with zero configuration required. You may optionally provide a Google Gemini API Key below to use Google Imagen 3 and Gemini directly.
            </p>
            <div className="space-y-1.5">
              <label className="text-xs font-medium text-slate-300">Google Gemini API Key (Optional)</label>
              <input
                type="password"
                value={customApiKey}
                onChange={(e) => {
                  setCustomApiKey(e.target.value);
                  localStorage.setItem('posterai_gemini_key', e.target.value);
                }}
                placeholder="AIzaSy..."
                className="w-full bg-slate-950 border border-slate-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500"
              />
            </div>
            <div className="flex justify-end pt-2">
              <button
                onClick={() => setShowSettings(false)}
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-500 text-white rounded-lg text-sm font-medium transition-colors"
              >
                Save & Close
              </button>
            </div>
          </div>
        </div>
      )}

      {/* 2. Hero Section */}
      <section className="border-b border-slate-800/80 bg-gradient-to-b from-slate-900/50 to-transparent py-8 px-4 lg:px-8">
        <div className="max-w-7xl mx-auto space-y-4">
          <div className="max-w-3xl space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 text-xs font-semibold">
              <Cpu className="w-3.5 h-3.5" />
              Generative AI Laboratory Practical
            </div>
            <h2 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold tracking-tight text-white">
              AI Event Poster Generator
            </h2>
            <p className="text-sm sm:text-base text-slate-400 leading-relaxed">
              Accepts event details and theme, enhances them using an <strong>LLM Prompt Engineering Pipeline</strong>, and generates a promotional poster image via <strong>Text-to-Image AI</strong>.
            </p>
          </div>

          {/* Quick-fill sample presets */}
          <div className="pt-2">
            <span className="text-xs font-medium text-slate-400 block mb-2">Try a Sample Event:</span>
            <div className="flex flex-wrap gap-2">
              {SAMPLE_EVENTS.map((preset, idx) => (
                <button
                  key={idx}
                  onClick={() => loadPreset(preset)}
                  className="px-3 py-1.5 rounded-lg bg-slate-800/80 hover:bg-indigo-950/60 hover:border-indigo-600/50 border border-slate-700/60 text-xs text-slate-300 hover:text-white transition-all flex items-center gap-1.5"
                >
                  <Sparkles className="w-3 h-3 text-indigo-400" />
                  {preset.title.split(':')[0]}
                </button>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Main Workspace: 2-Column Layout */}
      <main className="max-w-7xl mx-auto w-full px-4 lg:px-8 py-8 flex-1 grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">
        
        {/* Left Column: User Input Form (Step 1) */}
        <div className="lg:col-span-5 space-y-6">
          <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-5">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <h3 className="font-semibold text-base text-white flex items-center gap-2">
                <Sliders className="w-4 h-4 text-indigo-400" />
                Event Information
              </h3>
              <span className="text-xs text-indigo-400 font-medium">Step 1: Input</span>
            </div>

            {error && (
              <div className="p-3 rounded-lg bg-rose-500/10 border border-rose-500/30 text-rose-300 text-xs">
                {error}
              </div>
            )}

            <form onSubmit={handleGenerate} className="space-y-4">
              {/* Event Title */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300 flex items-center justify-between">
                  <span>Event Title *</span>
                  <span className="text-[10px] text-slate-500">{title.length}/60</span>
                </label>
                <input
                  type="text"
                  required
                  maxLength={60}
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. HackNova 2026: AI & Web3"
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2.5 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors"
                />
              </div>

              {/* Event Description */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300">
                  Event Description *
                </label>
                <textarea
                  required
                  rows={3}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Explain what the event is about, activities, target audience..."
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3.5 py-2 text-sm text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 transition-colors resize-none"
                />
              </div>

              {/* Theme & Poster Style */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                    <Tag className="w-3.5 h-3.5 text-indigo-400" />
                    Event Theme *
                  </label>
                  <select
                    value={theme}
                    onChange={(e) => setTheme(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="Technical">Technical</option>
                    <option value="Hackathon">Hackathon</option>
                    <option value="Cultural">Cultural</option>
                    <option value="Sports">Sports</option>
                    <option value="Music">Music</option>
                    <option value="Workshop">Workshop</option>
                    <option value="Conference">Conference</option>
                    <option value="Gaming">Gaming</option>
                    <option value="Art & Design">Art & Design</option>
                  </select>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                    <Palette className="w-3.5 h-3.5 text-violet-400" />
                    Poster Style *
                  </label>
                  <select
                    value={style}
                    onChange={(e) => setStyle(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                  >
                    <option value="Modern">Modern</option>
                    <option value="Minimalist">Minimalist</option>
                    <option value="Futuristic">Futuristic</option>
                    <option value="3D">3D Render</option>
                    <option value="Cyberpunk">Cyberpunk</option>
                    <option value="Vintage">Vintage / Retro</option>
                    <option value="Watercolor">Watercolor</option>
                  </select>
                </div>
              </div>

              {/* Color Preferences */}
              <div className="space-y-1.5">
                <label className="text-xs font-semibold text-slate-300">
                  Color Preferences (Optional)
                </label>
                <select
                  value={colorPreference}
                  onChange={(e) => setColorPreference(e.target.value)}
                  className="w-full bg-slate-950 border border-slate-700 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                >
                  <option value="Neon Cyber">Neon Cyber (Cyan, Magenta, Violet)</option>
                  <option value="Electric Blue & Purple">Electric Blue & Purple</option>
                  <option value="Warm Sunset">Warm Sunset (Tangerine, Coral, Indigo)</option>
                  <option value="Pastel Dream">Pastel Dream (Lavender, Mint, Rose)</option>
                  <option value="Monochromatic">Monochromatic (Slate, Onyx, White)</option>
                  <option value="Forest Earth">Forest Earth (Emerald, Moss, Terracotta)</option>
                  <option value="Gold & Luxury">Gold & Luxury (Champagne, Regal Navy)</option>
                </select>
              </div>

              {/* Date & Venue (for Poster Text-Overlay layer) */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-slate-400 flex items-center gap-1">
                    <Calendar className="w-3 h-3 text-slate-400" />
                    Date / Time (Optional)
                  </label>
                  <input
                    type="text"
                    value={date}
                    onChange={(e) => setDate(e.target.value)}
                    placeholder="e.g. Oct 14-15, 2026"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-xs font-medium text-slate-400 flex items-center gap-1">
                    <MapPin className="w-3 h-3 text-slate-400" />
                    Venue (Optional)
                  </label>
                  <input
                    type="text"
                    value={venue}
                    onChange={(e) => setVenue(e.target.value)}
                    placeholder="e.g. Tech Arena Hall B"
                    className="w-full bg-slate-950 border border-slate-800 rounded-xl px-3 py-2 text-xs text-white focus:outline-none focus:border-indigo-500"
                  />
                </div>
              </div>

              {/* Aspect Ratio */}
              <div className="space-y-1.5 pt-1">
                <label className="text-xs font-semibold text-slate-300">Poster Aspect Ratio</label>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { id: '3:4', label: 'Portrait (3:4)', sub: 'Standard Poster' },
                    { id: '1:1', label: 'Square (1:1)', sub: 'Social Media' },
                    { id: '16:9', label: 'Banner (16:9)', sub: 'Wide Screen' },
                  ].map((ratio) => (
                    <button
                      key={ratio.id}
                      type="button"
                      onClick={() => setAspectRatio(ratio.id)}
                      className={`p-2 rounded-xl border text-left transition-all ${
                        aspectRatio === ratio.id
                          ? 'border-indigo-500 bg-indigo-500/15 text-white'
                          : 'border-slate-800 bg-slate-950 text-slate-400 hover:border-slate-700'
                      }`}
                    >
                      <div className="text-xs font-semibold">{ratio.label}</div>
                      <div className="text-[10px] text-slate-500">{ratio.sub}</div>
                    </button>
                  ))}
                </div>
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={isLoading}
                className="w-full py-3.5 px-4 rounded-xl bg-gradient-to-r from-indigo-600 via-violet-600 to-pink-600 hover:from-indigo-500 hover:via-violet-500 hover:to-pink-500 text-white font-semibold text-sm shadow-lg shadow-indigo-600/25 transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 mt-4 cursor-pointer"
              >
                {isLoading ? (
                  <>
                    <RefreshCw className="w-4 h-4 animate-spin" />
                    <span>Generating Poster via GenAI...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    <span>Generate AI Event Poster</span>
                  </>
                )}
              </button>
            </form>
          </div>
        </div>

        {/* Right Column: Generation Preview & Inspector (Steps 2, 3, 4, 5) */}
        <div className="lg:col-span-7 space-y-6">
          
          {/* State 1: Loading Animation */}
          {isLoading && (
            <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-8 shadow-xl text-center space-y-6 min-h-[460px] flex flex-col justify-center items-center">
              <div className="relative">
                <div className="w-20 h-20 rounded-full border-4 border-indigo-500/20 border-t-indigo-500 animate-spin"></div>
                <div className="absolute inset-0 flex items-center justify-center">
                  <Wand2 className="w-8 h-8 text-indigo-400 animate-pulse" />
                </div>
              </div>

              <div className="space-y-2 max-w-md">
                <h3 className="text-lg font-bold text-white">Generative AI Pipeline in Progress</h3>
                <p className="text-xs text-slate-400">
                  Executing multi-stage GenAI synthesis for "{title}"
                </p>
              </div>

              {/* Progress Steps Indicator */}
              <div className="w-full max-w-sm space-y-3 text-left">
                <div className={`flex items-center gap-3 p-2.5 rounded-xl border text-xs transition-colors ${
                  loadingStep >= 1 ? 'border-indigo-500/40 bg-indigo-500/10 text-white' : 'border-slate-800 text-slate-500'
                }`}>
                  <CheckCircle2 className={`w-4 h-4 ${loadingStep >= 1 ? 'text-indigo-400' : 'text-slate-600'}`} />
                  <div>
                    <div className="font-semibold">Step 1: Input Processing</div>
                    <div className="text-[10px] text-slate-400">Parsing title, description, and thematic constraints</div>
                  </div>
                </div>

                <div className={`flex items-center gap-3 p-2.5 rounded-xl border text-xs transition-colors ${
                  loadingStep >= 2 ? 'border-indigo-500/40 bg-indigo-500/10 text-white' : 'border-slate-800 text-slate-500'
                }`}>
                  <CheckCircle2 className={`w-4 h-4 ${loadingStep >= 2 ? 'text-indigo-400' : 'text-slate-600'}`} />
                  <div>
                    <div className="font-semibold">Step 2: LLM Prompt Engineering</div>
                    <div className="text-[10px] text-slate-400">Synthesizing composition, lighting, style & elements</div>
                  </div>
                </div>

                <div className={`flex items-center gap-3 p-2.5 rounded-xl border text-xs transition-colors ${
                  loadingStep >= 3 ? 'border-indigo-500/40 bg-indigo-500/10 text-white' : 'border-slate-800 text-slate-500'
                }`}>
                  <CheckCircle2 className={`w-4 h-4 ${loadingStep >= 3 ? 'text-indigo-400' : 'text-slate-600'}`} />
                  <div>
                    <div className="font-semibold">Step 3: Text-to-Image Generation</div>
                    <div className="text-[10px] text-slate-400">Generating poster pixels with FLUX.1 / Imagen model</div>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* State 2: Empty Initial State */}
          {!isLoading && !generationResult && (
            <div className="bg-slate-900/60 border border-dashed border-slate-800 rounded-2xl p-12 text-center space-y-4 min-h-[460px] flex flex-col justify-center items-center">
              <div className="w-16 h-16 rounded-2xl bg-slate-800/80 border border-slate-700/60 flex items-center justify-center text-slate-400">
                <ImageIcon className="w-8 h-8" />
              </div>
              <div className="space-y-1.5 max-w-sm">
                <h3 className="text-base font-semibold text-white">Your Poster Will Appear Here</h3>
                <p className="text-xs text-slate-400">
                  Fill in your event details on the left, or select one of the sample presets above to generate an AI poster.
                </p>
              </div>
            </div>
          )}

          {/* State 3: Generated Result Display */}
          {!isLoading && generationResult && (
            <div className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-6">
              
              {/* Top View Tabs & Actions */}
              <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-4">
                <div className="flex items-center gap-1.5 bg-slate-950 p-1 rounded-xl border border-slate-800 text-xs font-medium">
                  <button
                    onClick={() => setActiveTab('poster')}
                    className={`px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 ${
                      activeTab === 'poster' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    <Eye className="w-3.5 h-3.5" />
                    Poster Preview
                  </button>
                  <button
                    onClick={() => setActiveTab('prompt')}
                    className={`px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 ${
                      activeTab === 'prompt' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
                    }`}
                  >
                    <Layers className="w-3.5 h-3.5" />
                    Prompt Inspector
                  </button>
                  {variations.length > 0 && (
                    <button
                      onClick={() => setActiveTab('variations')}
                      className={`px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5 ${
                        activeTab === 'variations' ? 'bg-indigo-600 text-white' : 'text-slate-400 hover:text-white'
                      }`}
                    >
                      <Sparkles className="w-3.5 h-3.5" />
                      Variations ({variations.length})
                    </button>
                  )}
                </div>

                {/* Primary Action Buttons */}
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleDownload}
                    className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white rounded-lg text-xs font-semibold shadow-md transition-colors flex items-center gap-1.5 cursor-pointer"
                  >
                    <Download className="w-3.5 h-3.5" />
                    Download
                  </button>
                  <button
                    onClick={handleRegenerate}
                    title="Regenerate with fresh AI seed"
                    className="p-1.5 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg text-xs font-medium border border-slate-700 transition-colors flex items-center gap-1"
                  >
                    <RefreshCw className="w-3.5 h-3.5" />
                    <span className="hidden sm:inline">Regenerate</span>
                  </button>
                  <button
                    onClick={handleGenerateVariations}
                    disabled={isLoadingVariations}
                    className="px-2.5 py-1.5 bg-slate-800 hover:bg-slate-700 text-indigo-400 rounded-lg text-xs font-medium border border-indigo-900/50 transition-colors flex items-center gap-1 disabled:opacity-50"
                  >
                    {isLoadingVariations ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
                    <span>Variations</span>
                  </button>
                </div>
              </div>

              {/* Tab 1: Poster View */}
              {activeTab === 'poster' && (
                <div className="space-y-4">
                  {/* Overlay Switcher (Step 4 Requirement) */}
                  <div className="flex items-center justify-between bg-slate-950 px-4 py-2 rounded-xl border border-slate-800 text-xs">
                    <span className="text-slate-300 font-medium flex items-center gap-1.5">
                      <Layers className="w-3.5 h-3.5 text-indigo-400" />
                      Step 4: Poster Text-Overlay Layer
                    </span>
                    <button
                      onClick={() => setShowOverlay(!showOverlay)}
                      className={`px-2.5 py-1 rounded-md text-[11px] font-semibold transition-colors ${
                        showOverlay ? 'bg-indigo-600 text-white' : 'bg-slate-800 text-slate-400'
                      }`}
                    >
                      {showOverlay ? 'Overlay: ENABLED' : 'Overlay: OFF (Pure Art)'}
                    </button>
                  </div>

                  {/* Poster Display Container */}
                  <div className="relative mx-auto rounded-2xl overflow-hidden shadow-2xl border border-slate-800 bg-black flex justify-center items-center group max-w-md">
                    <img
                      src={generationResult.image.base64 || generationResult.image.localUrl}
                      alt={generationResult.rawInput.title}
                      className="w-full h-auto object-cover max-h-[580px] rounded-xl"
                    />

                    {/* Step 4: Separate Text Overlay Layer (HTML/CSS simulated preview matching the canvas composite) */}
                    {showOverlay && (
                      <div className="absolute inset-0 pointer-events-none flex flex-col justify-between p-6">
                        {/* Top Gradient & Title Info */}
                        <div className="space-y-2 bg-gradient-to-b from-black/80 via-black/40 to-transparent -m-6 p-6">
                          <span className="inline-block px-3 py-1 rounded-full bg-indigo-600/90 text-white text-[11px] font-bold tracking-wider uppercase backdrop-blur-sm">
                            {generationResult.rawInput.theme} • {generationResult.rawInput.style}
                          </span>
                          <h2 className="text-2xl sm:text-3xl font-extrabold text-white tracking-tight drop-shadow-md leading-tight">
                            {generationResult.rawInput.title}
                          </h2>
                        </div>

                        {/* Bottom Gradient & Date / Venue Info */}
                        <div className="space-y-1 bg-gradient-to-t from-black/90 via-black/50 to-transparent -m-6 p-6">
                          {generationResult.rawInput.date && (
                            <div className="flex items-center gap-1.5 text-xs font-semibold text-slate-100 drop-shadow">
                              <Calendar className="w-3.5 h-3.5 text-indigo-400" />
                              <span>{generationResult.rawInput.date}</span>
                            </div>
                          )}
                          {generationResult.rawInput.venue && (
                            <div className="flex items-center gap-1.5 text-xs text-slate-200 drop-shadow">
                              <MapPin className="w-3.5 h-3.5 text-pink-400" />
                              <span>{generationResult.rawInput.venue}</span>
                            </div>
                          )}
                          <div className="text-[10px] text-slate-400 pt-1">
                            PosterAI Generative Studio
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Metadata Chips */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-[11px] pt-1">
                    <div className="bg-slate-950 p-2 rounded-lg border border-slate-800">
                      <span className="text-slate-500 block">AI Image Model:</span>
                      <span className="font-semibold text-slate-200 truncate block">{generationResult.image.model}</span>
                    </div>
                    <div className="bg-slate-950 p-2 rounded-lg border border-slate-800">
                      <span className="text-slate-500 block">Seed:</span>
                      <span className="font-semibold text-slate-200 font-mono">{generationResult.image.seed}</span>
                    </div>
                    <div className="bg-slate-950 p-2 rounded-lg border border-slate-800">
                      <span className="text-slate-500 block">Aspect Ratio:</span>
                      <span className="font-semibold text-slate-200">{generationResult.image.aspectRatio}</span>
                    </div>
                    <div className="bg-slate-950 p-2 rounded-lg border border-slate-800">
                      <span className="text-slate-500 block">Latency:</span>
                      <span className="font-semibold text-slate-200">{generationResult.metrics.totalLatencyMs} ms</span>
                    </div>
                  </div>
                </div>
              )}

              {/* Tab 2: Prompt Inspector & Engineering Breakdown (Requirement 3 & 6) */}
              {activeTab === 'prompt' && (
                <div className="space-y-4">
                  {/* Side-by-side prompt comparison */}
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-slate-300">
                        Original Raw User Input vs AI-Enhanced Prompt
                      </span>
                      <button
                        onClick={handleCopyPrompt}
                        className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-[11px] text-slate-300 flex items-center gap-1 transition-colors"
                      >
                        {copiedPrompt ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                        <span>{copiedPrompt ? 'Copied' : 'Copy Enhanced Prompt'}</span>
                      </button>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
                      {/* Original Input */}
                      <div className="bg-slate-950 p-3.5 rounded-xl border border-slate-800 space-y-1.5">
                        <span className="text-[10px] uppercase font-bold tracking-wider text-slate-500">
                          Raw Input (Before LLM)
                        </span>
                        <div className="font-semibold text-white">{generationResult.rawInput.title}</div>
                        <p className="text-slate-400">{generationResult.rawInput.description}</p>
                        <div className="text-slate-500 text-[10px] pt-1">
                          Theme: {generationResult.rawInput.theme} | Style: {generationResult.rawInput.style}
                        </div>
                      </div>

                      {/* AI Enhanced Prompt */}
                      <div className="bg-indigo-950/20 p-3.5 rounded-xl border border-indigo-500/30 space-y-1.5">
                        <span className="text-[10px] uppercase font-bold tracking-wider text-indigo-400 flex items-center gap-1">
                          <Sparkles className="w-3 h-3" />
                          Enhanced Image Generation Prompt (After LLM)
                        </span>
                        <p className="text-indigo-100 font-mono text-[11px] leading-relaxed">
                          {generationResult.enhancedPrompt.full_enhanced_prompt}
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* 7 Required Prompt Dimensions Breakdown */}
                  <div className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-3">
                    <h4 className="text-xs font-bold uppercase tracking-wider text-slate-400">
                      Step 2 Breakdown: Prompt Engineering Dimensions
                    </h4>

                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                      <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800/80">
                        <span className="text-indigo-400 font-semibold block mb-1">1. Visual Composition:</span>
                        <span className="text-slate-300">{generationResult.enhancedPrompt.visual_composition}</span>
                      </div>
                      <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800/80">
                        <span className="text-indigo-400 font-semibold block mb-1">2. Background & Environment:</span>
                        <span className="text-slate-300">{generationResult.enhancedPrompt.background}</span>
                      </div>
                      <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800/80">
                        <span className="text-indigo-400 font-semibold block mb-1">3. Color Palette:</span>
                        <span className="text-slate-300">{generationResult.enhancedPrompt.color_palette}</span>
                      </div>
                      <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800/80">
                        <span className="text-indigo-400 font-semibold block mb-1">4. Lighting & Effects:</span>
                        <span className="text-slate-300">{generationResult.enhancedPrompt.lighting}</span>
                      </div>
                      <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800/80">
                        <span className="text-indigo-400 font-semibold block mb-1">5. Illustrations & Elements:</span>
                        <span className="text-slate-300">{generationResult.enhancedPrompt.illustrations}</span>
                      </div>
                      <div className="p-2.5 rounded-lg bg-slate-900 border border-slate-800/80">
                        <span className="text-indigo-400 font-semibold block mb-1">6. Overall Artistic Style:</span>
                        <span className="text-slate-300">{generationResult.enhancedPrompt.artistic_style}</span>
                      </div>
                    </div>

                    {generationResult.enhancedPrompt.prompt_engineering_insights && (
                      <div className="mt-3 pt-3 border-t border-slate-800 space-y-2">
                        <span className="text-xs font-semibold text-slate-300 block">Applied Prompt Engineering Techniques:</span>
                        <div className="flex flex-wrap gap-2">
                          {generationResult.enhancedPrompt.prompt_engineering_insights.map((item, i) => (
                            <span key={i} className="px-2.5 py-1 rounded-md bg-indigo-500/10 border border-indigo-500/20 text-indigo-300 text-[11px]" title={item.description}>
                              ✦ {item.technique}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Tab 3: Variations Gallery (Step 5 Requirement) */}
              {activeTab === 'variations' && (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <span className="text-xs font-semibold text-slate-300">
                      Alternative Visual Variations
                    </span>
                    <span className="text-xs text-slate-500">Different seeds applied to enhanced prompt</span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                    {variations.map((v, i) => (
                      <div key={i} className="group relative rounded-xl overflow-hidden border border-slate-800 bg-slate-950 space-y-2 p-2">
                        <img
                          src={v.base64 || v.localUrl}
                          alt={v.title}
                          className="w-full h-48 object-cover rounded-lg"
                        />
                        <div className="flex items-center justify-between text-xs px-1">
                          <span className="font-semibold text-white">{v.title}</span>
                          <span className="text-[10px] text-slate-500 font-mono">Seed: {v.seed}</span>
                        </div>
                        <button
                          onClick={() => {
                            setGenerationResult({ ...generationResult, image: v });
                            setActiveTab('poster');
                          }}
                          className="w-full py-1.5 rounded-lg bg-indigo-600/80 hover:bg-indigo-600 text-white text-xs font-medium transition-colors"
                        >
                          Use This Variation
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

            </div>
          )}

        </div>
      </main>

      {/* 6. GenAI Practical Demonstration Section: "How Generative AI Works" */}
      <section className="border-t border-slate-800/80 bg-slate-900/40 py-12 px-4 lg:px-8 mt-12">
        <div className="max-w-7xl mx-auto space-y-8">
          <div className="max-w-2xl space-y-2">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-violet-500/10 border border-violet-500/20 text-violet-400 text-xs font-semibold">
              <BookOpen className="w-3.5 h-3.5" />
              Laboratory Practical Theory & Pipeline
            </div>
            <h3 className="text-2xl font-bold text-white tracking-tight">
              How Generative AI Works in PosterAI
            </h3>
            <p className="text-xs sm:text-sm text-slate-400">
              Understanding the end-to-end generative pipeline from natural language input to high-resolution diffusion artwork.
            </p>
          </div>

          {/* 5-Step Pipeline Cards */}
          <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
            
            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-2">
              <div className="w-8 h-8 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400 font-bold text-sm">
                1
              </div>
              <h4 className="text-sm font-semibold text-white">Input Processing</h4>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                Extracts raw event parameters (Title, Description, Theme, Style, Color palette) and structures them into a standardized context payload.
              </p>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-2">
              <div className="w-8 h-8 rounded-lg bg-violet-600/20 border border-violet-500/30 flex items-center justify-center text-violet-400 font-bold text-sm">
                2
              </div>
              <h4 className="text-sm font-semibold text-white">LLM Prompt Enhancement</h4>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                A Large Language Model (Gemini / GPT) acts as an Art Director, analyzing thematic nuances to generate a multidimensional visual concept.
              </p>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-2">
              <div className="w-8 h-8 rounded-lg bg-pink-600/20 border border-pink-500/30 flex items-center justify-center text-pink-400 font-bold text-sm">
                3
              </div>
              <h4 className="text-sm font-semibold text-white">Prompt Engineering</h4>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                Applies composition rules (rule-of-thirds, negative space for titles), volumetric lighting descriptors, and negative prompt filtering.
              </p>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-2">
              <div className="w-8 h-8 rounded-lg bg-emerald-600/20 border border-emerald-500/30 flex items-center justify-center text-emerald-400 font-bold text-sm">
                4
              </div>
              <h4 className="text-sm font-semibold text-white">Text-to-Image Generation</h4>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                A Latent Diffusion Model (FLUX.1 / Imagen 3) converts text token embeddings into high-resolution pixels via multi-step iterative denoising.
              </p>
            </div>

            <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 space-y-2">
              <div className="w-8 h-8 rounded-lg bg-amber-600/20 border border-amber-500/30 flex items-center justify-center text-amber-400 font-bold text-sm">
                5
              </div>
              <h4 className="text-sm font-semibold text-white">Poster Output & Layering</h4>
              <p className="text-[11px] text-slate-400 leading-relaxed">
                The synthesized visual background is paired with a clean typography overlay layer, ready for high-resolution PNG export.
              </p>
            </div>

          </div>
        </div>
      </section>

      {/* Generation History (Step 4 Requirement) */}
      {history.length > 0 && (
        <section className="border-t border-slate-800/80 bg-slate-950 py-8 px-4 lg:px-8">
          <div className="max-w-7xl mx-auto space-y-4">
            <h3 className="text-sm font-bold uppercase tracking-wider text-slate-400 flex items-center gap-2">
              <History className="w-4 h-4 text-indigo-400" />
              Recent Generation History ({history.length})
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 md:grid-cols-6 gap-3">
              {history.map((item, idx) => (
                <div
                  key={idx}
                  onClick={() => {
                    setGenerationResult(item);
                    setTitle(item.rawInput.title);
                    setDescription(item.rawInput.description);
                    setTheme(item.rawInput.theme);
                    setStyle(item.rawInput.style);
                    window.scrollTo({ top: 180, behavior: 'smooth' });
                  }}
                  className="group cursor-pointer rounded-xl overflow-hidden border border-slate-800 hover:border-indigo-500/60 transition-all bg-slate-900 p-1.5 space-y-1.5"
                >
                  <img
                    src={item.image.base64 || item.image.localUrl}
                    alt={item.rawInput.title}
                    className="w-full h-24 object-cover rounded-lg group-hover:scale-105 transition-transform"
                  />
                  <div className="text-[11px] font-semibold text-white truncate px-1">
                    {item.rawInput.title}
                  </div>
                  <div className="text-[10px] text-slate-400 px-1 truncate">
                    {item.rawInput.theme} • {item.rawInput.style}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Footer */}
      <footer className="border-t border-slate-800/80 py-6 px-4 text-center text-xs text-slate-500">
        <p>PosterAI – Generative Poster Studio | Generative AI Laboratory Practical Application</p>
      </footer>
    </div>
  );
}
