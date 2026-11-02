const mongoose = require('mongoose');

const documentSchema = new mongoose.Schema({
  name: { type: String, required: true, trim: true },
  originalName: { type: String, required: true },
  mimeType: { type: String, required: true },
  size: { type: Number, required: true },
  cloudinaryUrl: { type: String, required: true },
  cloudinaryPublicId: { type: String, required: true },
  cloudinaryResourceType: { type: String, default: 'raw' },
  cloudinaryDeliveryType: { type: String, enum: ['upload', 'private', 'authenticated'] },
  pageCount: { type: Number, default: 0 },
  chunkCount: { type: Number, default: 0 },
  status: { type: String, enum: ['processing', 'ready', 'failed'], default: 'processing', index: true },
  processingError: { type: String, default: null },
}, { timestamps: true });

module.exports = mongoose.model('Document', documentSchema);
