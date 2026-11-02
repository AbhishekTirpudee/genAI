const axios = require('axios');

/**
 * Prompt Engineering LLM Service
 * Implements Step 2 of the Generative AI Pipeline:
 * Transforms raw user input (Title, Description, Theme, Style, Color Preference)
 * into a highly detailed, professional text-to-image generation prompt.
 */

// Heuristic fallback generator in case network or external LLM API is unavailable
function generateHeuristicEnhancedPrompt(params) {
  const { title, description, theme, style, colorPreference, audience, mood } = params;

  const themeKeywords = {
    Technical: {
      elements: 'floating glowing circuit boards, neural network nodes, holographic code, isometric server racks, data particles',
      lighting: 'volumetric cyan and violet laser beams, ambient blue glow, edge rim highlights',
      background: 'futuristic glass server room or deep space matrix data grid with soft bokeh',
      composition: 'centered focal point with clean upper third negative space reserved for event typography'
    },
    Hackathon: {
      elements: 'cyberpunk workstation, dual ultrawide holographic screens, floating 3D code runes, energy cables, coffee and futuristic gadget motifs',
      lighting: 'vibrant neon pink and electric turquoise backlighting, cinematic high contrast rim lighting',
      background: 'high-tech incubator hub with panoramic glass windows overlooking a neon city skyline at night',
      composition: 'dynamic angled isometric perspective, wide angle lens, dramatic depth of field'
    },
    Cultural: {
      elements: 'expressive swirling silk ribbons, ethnic decorative mandalas, golden traditional motifs, handcrafted origami and dynamic lanterns',
      lighting: 'warm golden hour sunlight, festive fairy lights, soft ambient warmth, glowing embers',
      background: 'grand festival pavilion with decorative heritage arches and floating flower petals',
      composition: 'balanced symmetrical mandala-inspired layout with graceful flow around the central subject'
    },
    Sports: {
      elements: 'high-speed motion streaks, exploding dust particles, dynamic athletic silhouette in motion, shockwaves, geometric stadium lines',
      lighting: 'dramatic stadium floodlights, harsh dynamic rim lighting, high-contrast chiaroscuro',
      background: 'modern Olympic arena with cheering crowd silhouettes and lens flare effects',
      composition: 'aggressive low-angle heroic perspective capturing intense kinetic motion and energy'
    },
    Music: {
      elements: 'floating 3D audio waves, glowing neon vinyl records, holographic acoustic equalizers, musical notes radiating in particle streams',
      lighting: 'pulsating stage strobes, magenta and ultraviolet laser arrays, smoke and fog haze',
      background: 'concert arena stage with concert crowd silhouettes under starry night festival sky',
      composition: 'vertically aligned concert poster aesthetic with expansive header area for headliners'
    },
    Workshop: {
      elements: 'stylized 3D geometric learning modules, interlocking gear mechanisms, floating interactive knowledge graphs, sleek digital stylus and tablets',
      lighting: 'clean daylight studio lighting, soft diffused shadow, crisp highlights on matte surfaces',
      background: 'minimalist Scandinavian modern collaborative workshop studio with acoustic wood paneling',
      composition: 'clean editorial grid arrangement with designated upper and lower margin zones for information'
    },
    Conference: {
      elements: 'sleek crystalline globe sculpture, interconnected global fiber optics, minimalist architectural podium, polished glass sphere',
      lighting: 'sophisticated corporate lighting, diffused cool white spotlights, subtle gold metallic sheen',
      background: 'grand auditorium of a contemporary glass convention center with soft blurred architectural columns',
      composition: 'prestigious executive poster framing with high-end editorial white space'
    }
  };

  const selectedTheme = themeKeywords[theme] || themeKeywords['Technical'];

  const styleSignatures = {
    Modern: 'clean vector-meets-3D aesthetic, crisp edges, premium graphic design, Swiss typography grid influence, contemporary branding look',
    Minimalist: 'hyper-minimal flat design with subtle gradients, negative space dominance, elegant simple geometric silhouettes, high-end museum poster',
    Futuristic: 'cyber-futurism, glowing neon accents, 3D holographic HUD elements, Octane Render 8K, unreal engine 5 cinematic lighting',
    '3D': 'isometric 3D digital illustration, smooth clay and frosted glass shaders, ray-traced ambient occlusion, subsurface scattering, tactile textures',
    Cyberpunk: 'gritty neo-Tokyo cyberpunk, drenched in rain reflections, neon kanji signs, chrome metal plating, dark moody high contrast',
    Vintage: 'retro 70s screenprint poster, distressed textured grain, halftone dots, warm muted earth tones, groovy vintage typography spacing',
    Watercolor: 'fluid watercolor washes, expressive ink splatters, wet-on-wet pigment blooms, handmade artisanal paper texture, poetic atmosphere'
  };

  const selectedStyle = styleSignatures[style] || styleSignatures['Modern'];

  const colorPalettes = {
    'Neon Cyber': 'Electric Cyan (#00F0FF), Neon Magenta (#FF007F), Deep Violet (#120338), Dark Obsidian (#060814)',
    'Warm Sunset': 'Solar Tangerine (#FF6B35), Deep Coral (#F72585), Goldenrod (#FFC107), Twilight Indigo (#3A0CA3)',
    'Pastel Dream': 'Soft Lavender (#D8B4E2), Mint Jade (#A7F3D0), Blush Rose (#FBCFE8), Off-White (#F8FAFC)',
    'Monochromatic': 'Midnight Onyx (#0F172A), Slate Graphite (#334155), Titanium Silver (#94A3B8), Pure Crisp White (#FFFFFF)',
    'Electric Blue & Purple': 'Hyper Royal Blue (#1D4ED8), Electric Violet (#7C3AED), Radiant Cyan (#06B6D4), Deep Space (#090D16)',
    'Forest Earth': 'Deep Emerald (#064E3B), Sage Moss (#059669), Terracotta (#D97706), Sand Dune (#F5F5DC)',
    'Gold & Luxury': 'Metallic Champagne Gold (#D4AF37), Regal Navy (#0F172A), Brushed Bronze (#B45309), Jet Black (#000000)'
  };

  const selectedColors = colorPalettes[colorPreference] || (colorPreference ? colorPreference : 'Dynamic complementary accent palette tailored to the theme');

  const visual_composition = `Heroic vertical poster composition centered on ${title}. ${selectedTheme.composition}. Balanced focal hierarchy with generous negative space at the top and bottom intentionally preserved for clean event typography overlay.`;
  const background = `${selectedTheme.background}, seamless gradient transition from deep shadows to luminous highlights.`;
  const color_palette = selectedColors;
  const lighting = `${selectedTheme.lighting}, cinematic volumetric atmosphere with subtle particulate luminescence.`;
  const illustrations = `${selectedTheme.elements}, meticulously crafted 3D objects with depth and tactile material realism.`;
  const artistic_style = `${selectedStyle}. High resolution 8K, Octane render quality, trending on Behance and Dribbble, professional event promotional artwork.`;

  const full_enhanced_prompt = `Professional event promotional poster for "${title}". Event context: ${description}. Theme: ${theme}. Visual Style: ${selectedStyle}. Central Motif: ${illustrations}. Background: ${background}. Color Scheme: ${color_palette}. Lighting & Atmosphere: ${lighting}. Layout: ${visual_composition}. Artistic Execution: 8k digital artwork, high detail, masterpiece composition, award-winning poster design, clean negative space for headline text, no illegible clutter, photorealistic textures.`;

  const negative_prompt = `blurry, low quality, distorted, deformed, cluttered composition, illegible garbled gibberish text in image, muddy colors, bad anatomy, pixelated, watermark, amateur drawing.`;

  const prompt_engineering_insights = [
    { technique: "Role Prompting", description: "Instructed AI as an award-winning creative art director and poster designer." },
    { technique: "Domain-Specific Visual Vocabulary", description: `Injected specialized visual descriptors for '${theme}' (${selectedTheme.elements.split(',').slice(0, 3).join(', ')}).` },
    { technique: "Composition & Negative Space Control", description: "Explicitly constrained spatial layout so the upper and lower bounds allow clean text placement." },
    { technique: "Lighting & Shader Specification", description: `Applied '${lighting}' for dramatic atmospheric depth.` },
    { technique: "Negative Prompt Filtering", description: "Screened out common diffusion artifacts, garbled pseudo-text, and low-res noise." }
  ];

  return {
    visual_composition,
    background,
    color_palette,
    lighting,
    illustrations,
    artistic_style,
    full_enhanced_prompt,
    negative_prompt,
    prompt_engineering_insights,
    engine_used: "Heuristic Prompt Engineering Synthesizer"
  };
}

/**
 * Call Gemini API for prompt engineering if key is valid
 */
async function callGeminiPromptEngineering(apiKey, params) {
  const { title, description, theme, style, colorPreference, audience, mood } = params;

  const systemInstruction = `You are an expert Generative AI Prompt Engineer and Creative Director for top-tier event posters.
Your job is to transform raw event information into a masterful, vivid text-to-image prompt suitable for models like Imagen 3, FLUX.1, or Stable Diffusion XL.

The user will provide:
- Event Title: ${title}
- Event Description: ${description}
- Theme: ${theme}
- Poster Style: ${style}
- Color Preferences: ${colorPreference || 'None specified'}
- Mood/Audience: ${mood || 'Energetic and inspiring'}

Output ONLY a valid JSON object (no markdown code blocks, just raw JSON) with the following exact keys:
{
  "visual_composition": "Detailed description of layout, focal subject, rule of thirds, negative space for titles",
  "background": "Detailed description of environment, horizon, depth of field, atmosphere",
  "color_palette": "Specific color names, hex codes, and emotional harmony",
  "lighting": "Detailed lighting sources, rim light, volumetric glow, shadows, highlights",
  "illustrations": "Key graphic elements, 3D motifs, vector or digital assets, textures",
  "artistic_style": "Exact rendering medium, artistic influences, camera/render engine settings (e.g., Octane 8k, Cinema4D, Risograph)",
  "full_enhanced_prompt": "A cohesive, rich, single master prompt ready to be sent to a text-to-image generator. Must leave negative space for event typography.",
  "negative_prompt": "Tokens to avoid (garbled text, blur, pixelation, distortion, artifacts)",
  "prompt_engineering_insights": [
    {"technique": "Name of technique used", "description": "Why and how it was applied to enhance this prompt"}
  ]
}`;

  const response = await axios.post(
    `https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key=${apiKey}`,
    {
      contents: [{ parts: [{ text: systemInstruction }] }],
      generationConfig: {
        temperature: 0.7,
        topP: 0.95,
        responseMimeType: "application/json"
      }
    },
    { timeout: 15000 }
  );

  const text = response.data?.candidates?.[0]?.content?.parts?.[0]?.text;
  if (!text) throw new Error("Empty response from Gemini LLM");
  
  const parsed = JSON.parse(text);
  parsed.engine_used = "Google Gemini 1.5 Flash (Direct API)";
  return parsed;
}

/**
 * Call Open LLM endpoint for prompt engineering (Pollinations text API)
 */
async function callOpenLLMEndpoint(params) {
  const { title, description, theme, style, colorPreference, mood } = params;

  const prompt = `Act as an expert GenAI prompt engineer. Given:
Title: "${title}"
Description: "${description}"
Theme: "${theme}"
Style: "${style}"
Colors: "${colorPreference || 'Adaptive'}"
Mood: "${mood || 'Inspiring'}"

Transform this into a comprehensive text-to-image prompt.
Respond ONLY with a JSON object containing:
visual_composition, background, color_palette, lighting, illustrations, artistic_style, full_enhanced_prompt, negative_prompt, prompt_engineering_insights (array of objects with technique and description).`;

  const response = await axios.get(
    `https://text.pollinations.ai/${encodeURIComponent(prompt)}?json=true&model=openai`,
    { timeout: 18000 }
  );

  let data = response.data;
  if (typeof data === 'string') {
    // Try to extract JSON if wrapped in markdown code fence
    const jsonMatch = data.match(/\{[\s\S]*\}/);
    if (jsonMatch) {
      data = JSON.parse(jsonMatch[0]);
    } else {
      throw new Error("Invalid JSON from LLM");
    }
  }

  if (!data.full_enhanced_prompt) {
    throw new Error("Missing full_enhanced_prompt in response");
  }

  data.engine_used = "OpenAI GPT-4o-mini (via GenAI Hub)";
  return data;
}

/**
 * Main Enhance Prompt Function with Cascading Fallback
 */
async function enhancePrompt(params, userApiKey = null) {
  const apiKey = userApiKey || process.env.GEMINI_API_KEY;

  // 1. Try Gemini if an API key is provided and not a placeholder
  if (apiKey && apiKey.length > 20 && !apiKey.includes('placeholder')) {
    try {
      console.log("[LLM Service] Attempting Gemini API for prompt engineering...");
      const result = await callGeminiPromptEngineering(apiKey, params);
      return result;
    } catch (err) {
      console.warn("[LLM Service] Gemini call failed or key invalid, falling back to open LLM pipeline:", err.message);
    }
  }

  // 2. Try Open LLM endpoint
  try {
    console.log("[LLM Service] Attempting Open LLM API for prompt engineering...");
    const result = await callOpenLLMEndpoint(params);
    return result;
  } catch (err) {
    console.warn("[LLM Service] Open LLM call failed or timed out, falling back to heuristic engine:", err.message);
  }

  // 3. Guaranteed reliable Heuristic Synthesizer
  console.log("[LLM Service] Using Heuristic Prompt Synthesizer...");
  return generateHeuristicEnhancedPrompt(params);
}

module.exports = {
  enhancePrompt,
  generateHeuristicEnhancedPrompt
};
