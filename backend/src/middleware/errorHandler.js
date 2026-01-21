function errorHandler(err, req, res, next) {
  console.error('Error:', err)

  // Prisma errors
  if (err.code === 'P2002') {
    return res.status(409).json({ error: 'Email already exists' })
  }

  // Validation errors
  if (err.name === 'ValidationError') {
    return res.status(400).json({ error: err.message })
  }

  // Default error
  res.status(err.status || 500).json({
    error: err.message || 'Internal server error'
  })
}

module.exports = { errorHandler }
