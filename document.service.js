const Document = require('../models/document.model');
const Chat = require('../models/chat.model');
const cloudinary = require('./cloudinary.service');
const vectors = require('./qdrant.service');
const ingestionQueue = require('../queues/document-ingestion.queue');

exports.create = async (file) => {
  if (!file.buffer.subarray(0, 5).equals(Buffer.from('%PDF-'))) {
    const error = new Error('The uploaded file is not a valid PDF.');
    error.statusCode = 400;
    throw error;
  }
  const remote = await cloudinary.uploadPdf(file.buffer, file.originalname);
  let document;
  try {
    document = await Document.create({
      name: file.originalname, originalName: file.originalname, mimeType: file.mimetype,
      size: file.size, cloudinaryUrl: remote.secure_url, cloudinaryPublicId: remote.public_id,
      cloudinaryResourceType: remote.resource_type || 'raw',
      cloudinaryDeliveryType: remote.type || 'upload', status: 'processing',
    });
    await ingestionQueue.add('ingest-document', { documentId: document.id }, {
      jobId: document.id,
      attempts: 3,
      backoff: { type: 'exponential', delay: 1000 },
    });
    return document;
  } catch (error) {
    if (document) {
      await Document.updateOne({ _id: document.id }, {
        $set: { status: 'failed', processingError: 'The document could not be queued for processing. Please retry the upload.' },
      }).catch(() => {});
    }
    try {
      await cloudinary.deletePdf(remote.public_id, remote.resource_type || 'raw');
      if (document) await Document.findByIdAndDelete(document.id);
    } catch {
      // Keep a failed record linked to the Cloudinary file so cleanup can be retried.
    }
    throw error;
  }
};

exports.remove = async (document) => {
  const results = await Promise.allSettled([
    cloudinary.deletePdf(document.cloudinaryPublicId, document.cloudinaryResourceType),
    vectors.deleteDocument(document.id),
    Chat.deleteMany({ documentId: document.id }),
  ]);
  const failures = results.filter((result) => result.status === 'rejected');
  if (failures.length) throw new Error(`Cleanup failed for ${failures.length} associated resource(s). Retry deletion.`);
  await Document.findByIdAndDelete(document.id);
};
