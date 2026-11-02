const pdfParse = require('pdf-parse');
const chunkText = require('../utils/chunkText');
const ApiError = require('../utils/ApiError');

exports.extractAndChunk = async (buffer) => {
  const parsed = await pdfParse(buffer);
  const chunks = chunkText(parsed.text || '');
  if (!chunks.length) throw new ApiError(422, 'No readable text was found in this PDF. Scanned PDFs need OCR before they can be searched.');
  return { pageCount: parsed.numpages || 0, chunks };
};
