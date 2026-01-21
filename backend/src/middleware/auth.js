const { verifyAccessToken } = require('../utils/jwt')

function authenticateToken(req, res, next) {
  const token = req.cookies.accessToken || req.headers.authorization?.split(' ')[1]

  if (!token) {
    return res.status(401).json({ error: 'Access token required' })
  }

  const decoded = verifyAccessToken(token)
  
  if (!decoded) {
    return res.status(403).json({ error: 'Invalid or expired token' })
  }

  req.user = decoded
  next()
}

module.exports = { authenticateToken }
