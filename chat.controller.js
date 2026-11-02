const mongoose = require('mongoose');
const Document = require('../models/document.model');
const Chat = require('../models/chat.model');
const ai = require('../services/ai.service');
const ApiError = require('../utils/ApiError');

async function requireReadyDocument(id) {
  if (!mongoose.isValidObjectId(id)) throw new ApiError(400, 'Invalid document ID.');
  const document = await Document.findById(id);
  if (!document) throw new ApiError(404, 'Document not found.');
  if (document.status !== 'ready') throw new ApiError(409, 'This document is not ready for chat.');
  return document;
}

exports.ask = async (req, res) => {
  await requireReadyDocument(req.params.documentId);
  const question = typeof req.body.question === 'string' ? req.body.question.trim() : '';
  if (!question || question.length > 2000) throw new ApiError(400, 'Question must be between 1 and 2000 characters.');
  const result = await ai.answerQuestion(req.params.documentId, question);
  const chat = await Chat.create({ documentId: req.params.documentId, question, answer: result.answer, sources: result.sources });
  res.status(201).json({ success: true, data: chat });
};
exports.history = async (req, res) => {
  await requireReadyDocument(req.params.documentId);
  res.json({ success: true, data: await Chat.find({ documentId: req.params.documentId }).sort({ createdAt: 1 }).select('-__v') });
};
exports.clear = async (req, res) => {
  await requireReadyDocument(req.params.documentId);
  await Chat.deleteMany({ documentId: req.params.documentId });
  res.json({ success: true, message: 'Chat history cleared.' });
};
