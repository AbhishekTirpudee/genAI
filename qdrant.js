const { QdrantClient } = require('@qdrant/js-client-rest');

if (!process.env.QDRANT_URL) throw new Error('QDRANT_URL is required.');
module.exports = new QdrantClient({ url: process.env.QDRANT_URL, apiKey: process.env.QDRANT_API_KEY || undefined });
