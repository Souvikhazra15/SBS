const express = require('express')
const bcrypt = require('bcrypt')
const prisma = require('../config/prisma')
const { generateAccessToken, generateRefreshToken, verifyRefreshToken } = require('../utils/jwt')
const { authenticateToken } = require('../middleware/auth')

const router = express.Router()

// Register/Signup
router.post('/signup', async (req, res, next) => {
  try {
    const { email, password, firstName, lastName, phone } = req.body

    // Validation
    if (!email || !password) {
      return res.status(400).json({ error: 'Email and password are required' })
    }

    if (password.length < 8) {
      return res.status(400).json({ error: 'Password must be at least 8 characters' })
    }

    // Check if user exists
    const existingUser = await prisma.user.findUnique({ where: { email } })
    if (existingUser) {
      return res.status(409).json({ error: 'Email already registered' })
    }

    // Hash password
    const passwordHash = await bcrypt.hash(password, 10)

    // Create user
    const user = await prisma.user.create({
      data: {
        email,
        passwordHash,
        firstName: firstName || null,
        lastName: lastName || null,
        phone: phone || null,
        status: 'PENDING_VERIFICATION'
      }
    })

    // Generate tokens
    const accessToken = generateAccessToken(user.id, user.email, user.role)
    const refreshToken = generateRefreshToken(user.id)

    // Create session
    const session = await prisma.session.create({
      data: {
        userId: user.id,
        token: accessToken,
        refreshToken,
        ipAddress: req.ip,
        userAgent: req.headers['user-agent'],
        expiresAt: new Date(Date.now() + 15 * 60 * 1000) // 15 minutes
      }
    })

    // Create audit log
    await prisma.auditLog.create({
      data: {
        userId: user.id,
        action: 'USER_CREATED',
        resource: 'User',
        resourceId: user.id,
        ipAddress: req.ip,
        userAgent: req.headers['user-agent']
      }
    })

    // Set cookies
    res.cookie('accessToken', accessToken, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 15 * 60 * 1000 // 15 minutes
    })

    res.cookie('refreshToken', refreshToken, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 7 * 24 * 60 * 60 * 1000 // 7 days
    })

    res.status(201).json({
      message: 'User created successfully',
      user: {
        id: user.id,
        email: user.email,
        firstName: user.firstName,
        lastName: user.lastName,
        role: user.role,
        status: user.status
      }
    })
  } catch (error) {
    next(error)
  }
})

// Login
router.post('/login', async (req, res, next) => {
  try {
    const { email, password } = req.body

    // Validation
    if (!email || !password) {
      return res.status(400).json({ error: 'Email and password are required' })
    }

    // Find user
    const user = await prisma.user.findUnique({ where: { email } })
    if (!user) {
      return res.status(401).json({ error: 'Invalid email or password' })
    }

    // Verify password
    const isValidPassword = await bcrypt.compare(password, user.passwordHash)
    if (!isValidPassword) {
      return res.status(401).json({ error: 'Invalid email or password' })
    }

    // Check if account is active
    if (user.status === 'SUSPENDED' || user.status === 'DEACTIVATED') {
      return res.status(403).json({ error: 'Account is suspended or deactivated' })
    }

    // Generate tokens
    const accessToken = generateAccessToken(user.id, user.email, user.role)
    const refreshToken = generateRefreshToken(user.id)

    // Create session
    await prisma.session.create({
      data: {
        userId: user.id,
        token: accessToken,
        refreshToken,
        ipAddress: req.ip,
        userAgent: req.headers['user-agent'],
        expiresAt: new Date(Date.now() + 15 * 60 * 1000)
      }
    })

    // Update last login
    await prisma.user.update({
      where: { id: user.id },
      data: { lastLoginAt: new Date() }
    })

    // Create audit log
    await prisma.auditLog.create({
      data: {
        userId: user.id,
        action: 'USER_LOGIN',
        ipAddress: req.ip,
        userAgent: req.headers['user-agent']
      }
    })

    // Set cookies
    res.cookie('accessToken', accessToken, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 15 * 60 * 1000
    })

    res.cookie('refreshToken', refreshToken, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 7 * 24 * 60 * 60 * 1000
    })

    res.json({
      message: 'Login successful',
      user: {
        id: user.id,
        email: user.email,
        firstName: user.firstName,
        lastName: user.lastName,
        role: user.role,
        status: user.status
      }
    })
  } catch (error) {
    next(error)
  }
})

// Logout
router.post('/logout', authenticateToken, async (req, res, next) => {
  try {
    const token = req.cookies.accessToken

    // Delete session
    await prisma.session.deleteMany({
      where: { token }
    })

    // Create audit log
    await prisma.auditLog.create({
      data: {
        userId: req.user.userId,
        action: 'USER_LOGOUT',
        ipAddress: req.ip,
        userAgent: req.headers['user-agent']
      }
    })

    // Clear cookies
    res.clearCookie('accessToken')
    res.clearCookie('refreshToken')

    res.json({ message: 'Logout successful' })
  } catch (error) {
    next(error)
  }
})

// Refresh token
router.post('/refresh', async (req, res, next) => {
  try {
    const refreshToken = req.cookies.refreshToken

    if (!refreshToken) {
      return res.status(401).json({ error: 'Refresh token required' })
    }

    const decoded = verifyRefreshToken(refreshToken)
    if (!decoded) {
      return res.status(403).json({ error: 'Invalid refresh token' })
    }

    // Find session
    const session = await prisma.session.findFirst({
      where: { refreshToken },
      include: { user: true }
    })

    if (!session) {
      return res.status(403).json({ error: 'Session not found' })
    }

    // Generate new access token
    const accessToken = generateAccessToken(
      session.user.id,
      session.user.email,
      session.user.role
    )

    // Update session
    await prisma.session.update({
      where: { id: session.id },
      data: {
        token: accessToken,
        expiresAt: new Date(Date.now() + 15 * 60 * 1000)
      }
    })

    // Set new access token cookie
    res.cookie('accessToken', accessToken, {
      httpOnly: true,
      secure: process.env.NODE_ENV === 'production',
      sameSite: 'lax',
      maxAge: 15 * 60 * 1000
    })

    res.json({ message: 'Token refreshed' })
  } catch (error) {
    next(error)
  }
})

// Get current user
router.get('/me', authenticateToken, async (req, res, next) => {
  try {
    const user = await prisma.user.findUnique({
      where: { id: req.user.userId },
      select: {
        id: true,
        email: true,
        firstName: true,
        lastName: true,
        phone: true,
        role: true,
        status: true,
        createdAt: true,
        lastLoginAt: true
      }
    })

    if (!user) {
      return res.status(404).json({ error: 'User not found' })
    }

    res.json({ user })
  } catch (error) {
    next(error)
  }
})

module.exports = router
