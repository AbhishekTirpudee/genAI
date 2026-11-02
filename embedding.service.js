const ai = require('../config/gemini');

exports.embed = async (text) => {
  const response = await ai.models.embedContent({ model: process.env.GEMINI_EMBEDDING_MODEL || 'gemini-embedding-2', contents: text });
  const vector = response.embeddings?.[0]?.values;
  if (!vector?.length) throw new Error('Gemini returned an empty embedding.');
  return vector;
};
