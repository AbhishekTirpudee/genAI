const { GoogleGenAI } = require('@google/genai');

if (!process.env.GEMINI_API_KEY) throw new Error('GEMINI_API_KEY is required.');
module.exports = new GoogleGenAI({ apiKey: process.env.GEMINI_API_KEY });
