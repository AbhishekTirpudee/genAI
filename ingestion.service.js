const Document = require('../models/document.model');
const pdf = require('./pdf.service');
const cloudinary = require('./cloudinary.service');
const embedding = require('./embedding.service');
const vectors = require('./qdrant.service');

exports.ingestDocument = async (documentId) => {
  const document = await Document.findById(documentId);
  if (!document) return;

  await Document.updateOne({ _id: documentId }, { $set: { status: 'processing', processingError: null } });
  // Retries start clean so partial batches from a previous attempt cannot survive.
  await vectors.deleteDocument(documentId);
  const buffer = await cloudinary.downloadPdf(document);
  const { pageCount, chunks } = await pdf.extractAndChunk(buffer);
  const embeddings = [];
  for (const chunk of chunks) embeddings.push(await embedding.embed(chunk));
  await vectors.storeChunks(documentId, chunks, embeddings);

  const updated = await Document.updateOne({ _id: documentId, status: 'processing' }, {
    $set: { pageCount, chunkCount: chunks.length, status: 'ready', processingError: null },
  });
  if (!updated.matchedCount) await vectors.deleteDocument(documentId);
};
