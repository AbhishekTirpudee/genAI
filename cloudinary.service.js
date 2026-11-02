const cloudinary = require('../config/cloudinary');
const { UnrecoverableError } = require('bullmq');

const permanentDownloadStatuses = new Set([401, 403, 404]);

exports.resolveDeliveryType = (document) => {
  if (document.cloudinaryDeliveryType) return document.cloudinaryDeliveryType;
  const match = document.cloudinaryUrl?.match(/\/raw\/(upload|private|authenticated)(?:\/|$)/i);
  return match ? match[1].toLowerCase() : 'upload';
};

exports.downloadPdf = async (document) => {
  const resourceType = document.cloudinaryResourceType || 'raw';
  const deliveryType = exports.resolveDeliveryType(document);
  const publicId = document.cloudinaryPublicId;
  const format = resourceType === 'raw' ? (publicId.match(/\.([^.\/]+)$/)?.[1] || 'pdf') : 'pdf';
  const expiresAt = Math.floor(Date.now() / 1000) + 5 * 60;
  const signedUrl = cloudinary.utils.private_download_url(publicId, format, {
    resource_type: resourceType,
    type: deliveryType,
    expires_at: expiresAt,
  });

  const response = await fetch(signedUrl, { signal: AbortSignal.timeout(30_000) });
  if (!response.ok) {
    await response.body?.cancel().catch(() => {});
    const message = `Cloudinary signed PDF download failed (HTTP ${response.status}, delivery type ${deliveryType}).`;
    const error = permanentDownloadStatuses.has(response.status)
      ? new UnrecoverableError(message)
      : new Error(message);
    error.statusCode = response.status;
    error.nonRetryable = permanentDownloadStatuses.has(response.status);
    throw error;
  }

  try {
    return Buffer.from(await response.arrayBuffer());
  } finally {
    await response.body?.cancel().catch(() => {});
  }
};

exports.uploadPdf = (buffer, originalName) => new Promise((resolve, reject) => {
  const safeName = originalName.replace(/[^a-zA-Z0-9._-]/g, '_').replace(/\.pdf$/i, '');
  const stream = cloudinary.uploader.upload_stream({
    resource_type: 'raw', folder: process.env.CLOUDINARY_FOLDER || 'papertrail',
    public_id: `${Date.now()}-${safeName}.pdf`, format: 'pdf',
  }, (error, result) => error ? reject(error) : resolve(result));
  stream.end(buffer);
});

exports.deletePdf = (publicId, resourceType = 'raw') => cloudinary.uploader.destroy(publicId, { resource_type: resourceType, invalidate: true });
