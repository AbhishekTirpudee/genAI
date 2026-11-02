const axios = require('axios');
const fs = require('fs');
const path = require('path');

const OUTPUT_DIR = path.join(__dirname, '../../public/generated');

// Ensure output directory exists
if (!fs.existsSync(OUTPUT_DIR)) {
  fs.mkdirSync(OUTPUT_DIR, { recursive: true });
}

/**
 * Aspect Ratio Dimensions mapping
 */
function getDimensions(aspectRatio) {
  switch (aspectRatio) {
    case '1:1':
      return { width: 1024, height: 1024 };
    case '16:9':
      return { width: 1024, height: 576 };
    case '9:16':
      return { width: 576, height: 1024 };
    case '4:5':
      return { width: 800, height: 1000 };
    case '3:4':
    default:
      return { width: 768, height: 1024 }; // Standard poster vertical ratio
  }
}

/**
 * Generate image using Google Imagen 3 if API key available
 */
async function generateWithGoogleImagen(apiKey, prompt, options = {}) {
  const { aspectRatio = '3:4' } = options;
  const imagenAspectRatio = aspectRatio === '1:1' ? '1:1' : aspectRatio === '16:9' ? '16:9' : '3:4';

  const response = await axios.post(
    `https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict?key=${apiKey}`,
    {
      instances: [{ prompt }],
      parameters: {
        sampleCount: 1,
        aspectRatio: imagenAspectRatio,
        personGeneration: "ALLOW_ADULT",
        safetySetting: "BLOCK_MEDIUM_AND_ABOVE"
      }
    },
    { timeout: 35000 }
  );

  const b64Data = response.data?.predictions?.[0]?.bytesBase64Encoded;
  if (!b64Data) throw new Error("No image data returned from Imagen 3");

  const buffer = Buffer.from(b64Data, 'base64');
  const filename = `poster_imagen_${Date.now()}_${Math.floor(Math.random() * 10000)}.png`;
  const filePath = path.join(OUTPUT_DIR, filename);
  fs.writeFileSync(filePath, buffer);

  return {
    filename,
    localUrl: `/generated/${filename}`,
    base64: `data:image/png;base64,${b64Data}`,
    model: 'Google Imagen 3 (DeepMind)',
    seed: Math.floor(Math.random() * 1000000),
  };
}

/**
 * Generate image using Pollinations AI (FLUX.1 / Turbo)
 */
async function generateWithPollinations(prompt, options = {}) {
  const { aspectRatio = '3:4', seed = Math.floor(Math.random() * 10000000), model = 'flux' } = options;
  const { width, height } = getDimensions(aspectRatio);

  // Clean prompt for URL encoding
  const cleanPrompt = prompt.replace(/[\r\n]+/g, ' ').trim();
  const encodedPrompt = encodeURIComponent(cleanPrompt.slice(0, 800));

  const imageUrl = `https://image.pollinations.ai/prompt/${encodedPrompt}?width=${width}&height=${height}&seed=${seed}&nologo=true&model=${model}`;

  console.log(`[Image Service] Fetching AI image from model: ${model}, seed: ${seed}...`);
  const response = await axios.get(imageUrl, {
    responseType: 'arraybuffer',
    timeout: 30000
  });

  const buffer = Buffer.from(response.data);
  const base64 = `data:image/jpeg;base64,${buffer.toString('base64')}`;
  
  const filename = `poster_${model}_${Date.now()}_${seed}.jpg`;
  const filePath = path.join(OUTPUT_DIR, filename);
  fs.writeFileSync(filePath, buffer);

  return {
    filename,
    localUrl: `/generated/${filename}`,
    directUrl: imageUrl,
    base64,
    model: model === 'flux' ? 'FLUX.1-schnell (Black Forest Labs)' : 'Stable Diffusion XL Turbo',
    seed,
    width,
    height
  };
}

/**
 * Main generateImage function with multi-engine fallback
 */
async function generateImage(prompt, options = {}, userApiKey = null) {
  const startTime = Date.now();
  const apiKey = userApiKey || process.env.GEMINI_API_KEY;

  let result;
  let engineUsed = '';

  // 1. Try Google Imagen 3 if Gemini API key provided
  if (apiKey && apiKey.length > 20 && !apiKey.includes('placeholder')) {
    try {
      console.log("[Image Service] Attempting Google Imagen 3 API...");
      result = await generateWithGoogleImagen(apiKey, prompt, options);
      engineUsed = 'Google Imagen 3';
    } catch (err) {
      console.warn("[Image Service] Imagen 3 failed or not enabled on key, falling back to FLUX.1:", err.message);
    }
  }

  // 2. Primary / Fallback: Pollinations AI FLUX.1
  if (!result) {
    try {
      result = await generateWithPollinations(prompt, { ...options, model: 'flux' });
      engineUsed = 'FLUX.1-schnell';
    } catch (err) {
      console.warn("[Image Service] FLUX.1 model timed out, trying SDXL Turbo fallback:", err.message);
      result = await generateWithPollinations(prompt, { ...options, model: 'turbo' });
      engineUsed = 'SDXL Turbo';
    }
  }

  const durationMs = Date.now() - startTime;

  return {
    ...result,
    aspectRatio: options.aspectRatio || '3:4',
    generationTimeMs: durationMs,
    promptUsed: prompt
  };
}

/**
 * Generate Variations (generates 3 different seeds/styles)
 */
async function generateVariations(prompt, count = 3, options = {}, userApiKey = null) {
  const variations = [];
  const baseSeed = options.seed || Math.floor(Math.random() * 1000000);

  for (let i = 0; i < count; i++) {
    const variationSeed = baseSeed + (i * 997);
    try {
      const variationResult = await generateImage(prompt, { ...options, seed: variationSeed }, userApiKey);
      variations.push({
        id: `var-${i + 1}`,
        title: `Variation ${i + 1}`,
        seed: variationSeed,
        ...variationResult
      });
    } catch (err) {
      console.error(`[Image Service] Failed generating variation ${i + 1}:`, err.message);
    }
  }

  return variations;
}

module.exports = {
  generateImage,
  generateVariations,
  getDimensions
};
