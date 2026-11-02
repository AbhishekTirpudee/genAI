const ai = require('../config/gemini');
const embeddings = require('./embedding.service');
const qdrant = require('./qdrant.service');

exports.answerQuestion = async (documentId, question) => {
  const vector = await embeddings.embed(question);
  const matches = await qdrant.search(documentId, vector, 5);
  const context = matches.map((match, index) => `[Source ${index + 1}] ${match.payload.text}`).join('\n\n');
  if (!context) return { answer: 'I could not find relevant information in this document to answer that question.', sources: [] };
  const response = await ai.models.generateContent({
    model: process.env.GEMINI_CHAT_MODEL || 'gemini-3.5-flash-lite',
    contents: `Answer the question using only the supplied document excerpts. If they do not contain the answer, say so. Do not invent details.\n\nDocument excerpts:\n${context}\n\nQuestion: ${question}`,
  });
  return {
    answer: response.text || 'I could not generate an answer from the available excerpts.',
    sources: matches.map((match) => ({ chunkIndex: match.payload.chunkIndex, score: match.score, preview: String(match.payload.text).slice(0, 240) })),
  };
};
