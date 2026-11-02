function notFound(req, _res, next) {
  next(
    Object.assign(
      new Error(`Route not found: ${req.method} ${req.originalUrl}`),
      { statusCode: 404 }
    )
  );
}

function errorHandler(error, _req, res, _next) {
  console.error('Backend error:', error);

  const status =
    error.statusCode || (error.name === 'MulterError' ? 400 : 500);

  const message =
    status === 500
      ? 'The request could not be completed.'
      : error.message;

  res.status(status).json({
    success: false,
    message,
  });
}

module.exports = { notFound, errorHandler };