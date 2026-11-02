const mongoose = require('mongoose');
const Document = require('../models/document.model');
const service = require('../services/document.service');
const ApiError = require('../utils/ApiError');

exports.list = async (_req, res) => res.json({ success: true, data: await Document.find().sort({ createdAt: -1 }).select('-cloudinaryPublicId -__v') });
exports.get = async (req, res) => {
  if (!mongoose.isValidObjectId(req.params.id)) throw new ApiError(400, 'Invalid document ID.');
  const document = await Document.findById(req.params.id).select('-cloudinaryPublicId -__v');
  if (!document) throw new ApiError(404, 'Document not found.');
  res.json({ success: true, data: document });
};
exports.create = async (req, res) => {
  if (!req.file) throw new ApiError(400, 'Select a PDF to upload.');
  const document = await service.create(req.file);
  res.status(202).json({ success: true, data: document });
};
exports.remove = async (req, res) => {
  if (!mongoose.isValidObjectId(req.params.id)) throw new ApiError(400, 'Invalid document ID.');
  const document = await Document.findById(req.params.id);
  if (!document) throw new ApiError(404, 'Document not found.');
  await service.remove(document);
  res.json({ success: true, message: 'Document and associated data deleted.' });
};
