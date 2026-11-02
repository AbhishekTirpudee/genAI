const DEFAULT_CONCURRENCY = 2;

exports.DEFAULT_CONCURRENCY = DEFAULT_CONCURRENCY;

exports.parseConcurrency = (value) => {
  if (value === undefined) return DEFAULT_CONCURRENCY;
  if (typeof value !== 'string' || !/^\d+$/.test(value.trim())) {
    throw new Error('INGESTION_CONCURRENCY must be a positive integer.');
  }

  const concurrency = Number(value.trim());
  if (!Number.isSafeInteger(concurrency) || concurrency < 1) {
    throw new Error('INGESTION_CONCURRENCY must be a positive integer.');
  }
  return concurrency;
};
