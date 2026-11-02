const express = require('express');
const router = express.Router();
const { enhancePrompt } = require('../services/llmService');
const { generateImage, generateVariations } = require('../services/imageService');

/**
 * POST /api/generate-poster
 * Full End-to-End Generative AI Pipeline
 */
router.post('/generate-poster', async (req, res) => {
  const overallStart = Date.now();
  try {
    const {
      title,
      description,
      theme,
      style,
      colorPreference,
      aspectRatio = '3:4',
      date,
      venue,
      host,
      audience,
      mood,
      customApiKey,
      customPromptOverride // If user edited the prompt manually
    } = req.body;

    // Validation
    if (!title || !description || !theme) {
      return res.status(400).json({
        success: false,
        error: 'Missing required fields: title, description, and theme are required.'
      });
    }

    // Step 2: Prompt Engineering using LLM
    let enhancedPromptData;
    let llmStart = Date.now();
    let llmLatencyMs = 0;

    if (customPromptOverride && customPromptOverride.trim().length > 10) {
      enhancedPromptData = {
        full_enhanced_prompt: customPromptOverride.trim(),
        visual_composition: "Custom user-directed composition override",
        background: "Custom visual background",
        color_palette: colorPreference || "Custom palette",
        lighting: "Custom lighting",
        illustrations: "Custom elements",
        artistic_style: style || "Modern",
        negative_prompt: "blurry, low quality, distorted, watermark",
        prompt_engineering_insights: [{ technique: "User Custom Edit", description: "Prompt directly edited by user in Prompt Studio." }],
        engine_used: "User-Directed Prompt Override"
      };
      llmLatencyMs = 0;
    } else {
      enhancedPromptData = await enhancePrompt({
        title,
        description,
        theme,
        style: style || 'Modern',
        colorPreference,
        audience,
        mood
      }, customApiKey);
      llmLatencyMs = Date.now() - llmStart;
    }

    // Step 3: Text-to-Image Generation
    const imgStart = Date.now();
    const imageData = await generateImage(
      enhancedPromptData.full_enhanced_prompt,
      { aspectRatio },
      customApiKey
    );
    const imageLatencyMs = Date.now() - imgStart;

    const totalLatencyMs = Date.now() - overallStart;

    return res.status(200).json({
      success: true,
      rawInput: {
        title,
        description,
        theme,
        style: style || 'Modern',
        colorPreference: colorPreference || 'Adaptive',
        date: date || '',
        venue: venue || '',
        host: host || '',
        aspectRatio
      },
      enhancedPrompt: enhancedPromptData,
      image: imageData,
      metrics: {
        llmLatencyMs,
        imageLatencyMs,
        totalLatencyMs,
        timestamp: new Date().toISOString()
      }
    });

  } catch (err) {
    console.error("[Generate Route Error]:", err);
    return res.status(500).json({
      success: false,
      error: err.message || 'Failed to generate poster via GenAI pipeline'
    });
  }
});

/**
 * POST /api/enhance-prompt-only
 * Step 2 demonstration: inspect LLM prompt engineering without rendering image
 */
router.post('/enhance-prompt-only', async (req, res) => {
  try {
    const { title, description, theme, style, colorPreference, audience, mood, customApiKey } = req.body;

    if (!title || !description || !theme) {
      return res.status(400).json({
        success: false,
        error: 'title, description, and theme are required'
      });
    }

    const start = Date.now();
    const result = await enhancePrompt({
      title,
      description,
      theme,
      style: style || 'Modern',
      colorPreference,
      audience,
      mood
    }, customApiKey);

    return res.json({
      success: true,
      data: result,
      latencyMs: Date.now() - start
    });
  } catch (err) {
    console.error("[Enhance Prompt Error]:", err);
    return res.status(500).json({ success: false, error: err.message });
  }
});

/**
 * POST /api/generate-variations
 * Generate alternative variations for an existing poster
 */
router.post('/generate-variations', async (req, res) => {
  try {
    const { prompt, aspectRatio = '3:4', count = 3, customApiKey } = req.body;

    if (!prompt) {
      return res.status(400).json({ success: false, error: 'prompt is required' });
    }

    const variations = await generateVariations(prompt, count, { aspectRatio }, customApiKey);
    return res.json({
      success: true,
      variations
    });
  } catch (err) {
    console.error("[Variations Error]:", err);
    return res.status(500).json({ success: false, error: err.message });
  }
});

module.exports = router;
