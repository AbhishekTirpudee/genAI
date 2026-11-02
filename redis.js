const IORedis = require('ioredis');

if (!process.env.REDIS_URL) throw new Error('REDIS_URL is required.');

const connection = new IORedis(process.env.REDIS_URL, {
  maxRetriesPerRequest: null,
  enableReadyCheck: true,
});

module.exports = { connection };
