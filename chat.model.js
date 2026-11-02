const mongoose = require('mongoose');

const chatSchema = new mongoose.Schema({
  documentId: { type: mongoose.Schema.Types.ObjectId, ref: 'Document', required: true, index: true },
  question: { type: String, required: true, trim: true },
  answer: { type: String, required: true },
  sources: [{ chunkIndex: Number, score: Number, preview: String }],
}, { timestamps: true });

chatSchema.index({ documentId: 1, createdAt: 1 });
module.exports = mongoose.model('Chat', chatSchema);
