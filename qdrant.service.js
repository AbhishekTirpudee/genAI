// const { randomUUID } = require('crypto');
// const qdrant = require('../config/qdrant');
// const ApiError = require('../utils/ApiError');

// const collection = process.env.QDRANT_COLLECTION || 'pdf-docs';
// const vectorSize = Number(process.env.QDRANT_VECTOR_SIZE || 3072);
// let collectionReady;

// async function ensureCollection() {
//   if (!collectionReady) collectionReady = (async () => {
//     const existing = await qdrant.getCollections();
//     if (!existing.collections.some((item) => item.name === collection)) {
//       try {
//         await qdrant.createCollection(collection, { vectors: { size: vectorSize, distance: 'Cosine' } });
//       } catch (error) {
//         const afterCreate = await qdrant.getCollections();
//         if (!afterCreate.collections.some((item) => item.name === collection)) throw error;
//       }
//     }
//     const details = await qdrant.getCollection(collection);
//     const configuredVectors = details.config?.params?.vectors;
//     const configuredSize = typeof configuredVectors?.size === 'number' ? configuredVectors.size : null;
//     if (configuredSize !== null && configuredSize !== vectorSize) {
//       throw new ApiError(503, `Qdrant collection ${collection} uses vector size ${configuredSize}, but the configured model expects ${vectorSize}.`);
//     }
//   })().catch((error) => { collectionReady = undefined; throw error; });
//   return collectionReady;
// }

// exports.storeChunks = async (documentId, chunks, embeddings) => {
//   await ensureCollection();
//   const points = chunks.map((text, index) => ({
//     id: randomUUID(), vector: embeddings[index],
//     payload: { documentId: String(documentId), chunkIndex: index, text },
//   }));
//   for (let offset = 0; offset < points.length; offset += 64) {
//     await qdrant.upsert(collection, { wait: true, points: points.slice(offset, offset + 64) });
//   }
// };

// exports.search = async (documentId, vector, limit = 5) => {
//   await ensureCollection();
//   const response = await qdrant.query(collection, {
//     query: vector, limit, with_payload: true, with_vector: false,
//     filter: { must: [{ key: 'documentId', match: { value: String(documentId) } }] },
//   });
//   return response.points || [];
// };

// exports.deleteDocument = async (documentId) => {
//   const collections = await qdrant.getCollections();
//   if (!collections.collections.some((item) => item.name === collection)) return;
//   await qdrant.delete(collection, { wait: true, filter: { must: [{ key: 'documentId', match: { value: String(documentId) } }] } });
// };



const { createHash } = require('crypto');
const qdrant = require('../config/qdrant');
const ApiError = require('../utils/ApiError');

const collection = process.env.QDRANT_COLLECTION || 'pdf-docs';
const vectorSize = Number(process.env.QDRANT_VECTOR_SIZE || 3072);

let collectionReady;

async function ensureCollection() {
  if (!collectionReady) {
    collectionReady = (async () => {
      // 1. Check whether the collection exists
      const existing = await qdrant.getCollections();

      if (
        !existing.collections.some(
          (item) => item.name === collection
        )
      ) {
        try {
          await qdrant.createCollection(collection, {
            vectors: {
              size: vectorSize,
              distance: 'Cosine',
            },
          });
        } catch (error) {
          // Another request may have created it at the same time
          const afterCreate = await qdrant.getCollections();

          if (
            !afterCreate.collections.some(
              (item) => item.name === collection
            )
          ) {
            throw error;
          }
        }
      }

      // 2. Verify vector size
      const details = await qdrant.getCollection(collection);

      const configuredVectors =
        details.config?.params?.vectors;

      const configuredSize =
        typeof configuredVectors?.size === 'number'
          ? configuredVectors.size
          : null;

      if (
        configuredSize !== null &&
        configuredSize !== vectorSize
      ) {
        throw new ApiError(
          503,
          `Qdrant collection ${collection} uses vector size ${configuredSize}, but the configured model expects ${vectorSize}.`
        );
      }

      // 3. Create payload index for documentId
      //    This is required because chat/search filters
      //    Qdrant results using documentId.
      try {
        await qdrant.createPayloadIndex(collection, {
          field_name: 'documentId',
          field_schema: 'keyword',
          wait: true,
        });
      } catch (error) {
        // Index may already exist.
        // Ignore "already exists" errors.
        const message = String(
          error?.message || ''
        ).toLowerCase();

        if (
          !message.includes('already exists') &&
          !message.includes('already exist')
        ) {
          throw error;
        }
      }
    })().catch((error) => {
      collectionReady = undefined;
      throw error;
    });
  }

  return collectionReady;
}


// Store PDF chunks + embeddings in Qdrant
exports.storeChunks = async (
  documentId,
  chunks,
  embeddings
) => {
  await ensureCollection();

  const points = chunks.map((text, index) => ({
    // Stable point IDs make repeated ingestion upserts idempotent per document chunk.
    id: createHash('sha256').update(`${documentId}:${index}`).digest('hex').slice(0, 32)
      .replace(/^(.{8})(.{4})(.{4})(.{4})(.{12})$/, '$1-$2-$3-$4-$5'),

    vector: embeddings[index],

    payload: {
      documentId: String(documentId),
      chunkIndex: index,
      text,
    },
  }));

  // Upload in batches
  for (
    let offset = 0;
    offset < points.length;
    offset += 64
  ) {
    await qdrant.upsert(collection, {
      wait: true,
      points: points.slice(offset, offset + 64),
    });
  }
};


// Search only inside the selected document
exports.search = async (
  documentId,
  vector,
  limit = 5
) => {
  await ensureCollection();

  const response = await qdrant.query(collection, {
    query: vector,

    limit,

    with_payload: true,

    with_vector: false,

    filter: {
      must: [
        {
          key: 'documentId',
          match: {
            value: String(documentId),
          },
        },
      ],
    },
  });

  return response.points || [];
};


// Delete all vectors belonging to a document
exports.deleteDocument = async (documentId) => {
  const collections = await qdrant.getCollections();

  if (
    !collections.collections.some(
      (item) => item.name === collection
    )
  ) {
    return;
  }

  await qdrant.delete(collection, {
    wait: true,

    filter: {
      must: [
        {
          key: 'documentId',
          match: {
            value: String(documentId),
          },
        },
      ],
    },
  });
};
