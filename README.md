# VerifyAI - AI-Powered KYC Verification Platform

<div align="center">
  <img src="https://img.shields.io/badge/Next.js-14.2.35-black" alt="Next.js"/>
  <img src="https://img.shields.io/badge/FastAPI-0.104.1-green" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/PostgreSQL-15-blue" alt="PostgreSQL"/>
  <img src="https://img.shields.io/badge/TypeScript-5.0-blue" alt="TypeScript"/>
  <img src="https://img.shields.io/badge/Python-3.12-yellow" alt="Python"/>
  <img src="https://img.shields.io/badge/Tailwind-3.4-cyan" alt="Tailwind"/>
  <img src="https://img.shields.io/badge/Prisma-5.7-purple" alt="Prisma"/>
</div>

<br/>

<div align="center">
  <h3>Complete AI-powered identity verification platform with document analysis, face matching, deepfake detection, and risk scoring</h3>
</div>

## ✨ Features

### 🔐 **Authentication & Security**
- JWT-based authentication with refresh tokens
- Secure password hashing with bcrypt
- Role-based access control (User, Admin, Reviewer, Analyst)
- Session management with automatic expiration

### 📄 **Document Verification**
- **Fake Document Detection**: Advanced algorithms detect forged, tampered, or altered documents
- **OCR Text Extraction**: Extract and validate text from government-issued IDs
- **Security Feature Analysis**: Watermarks, holograms, microprint, and UV elements
- **Multi-format Support**: JPEG, PNG, BMP, TIFF documents up to 10MB

### 👤 **Face Matching & Liveness**
- **Biometric Verification**: Compare document photo with live selfie
- **Liveness Detection**: Prevent spoofing attacks with 3D depth analysis
- **Deepfake Detection**: AI-powered detection of manipulated facial images
- **Quality Assessment**: Face pose, lighting, and clarity validation

### 🛡️ **Risk Assessment & Compliance**
- **AML Screening**: Anti-Money Laundering compliance checks
- **Fraud Detection**: Machine learning models identify suspicious patterns
- **Risk Scoring**: Dynamic risk assessment with configurable thresholds
- **Audit Trail**: Complete verification history and compliance logs

### 🎨 **Modern Frontend**
- **Responsive Design**: Mobile-first approach with Tailwind CSS
- **Real-time Progress**: Live analysis status with step-by-step updates
- **Interactive UI**: Drag-and-drop file uploads with preview
- **Dark Mode**: Automatic theme switching with system preference
- **Toast Notifications**: User-friendly feedback and error handling

### 🔧 **Developer Experience**
- **Type-Safe APIs**: Full TypeScript coverage on frontend and backend
- **Auto-generated Documentation**: Interactive API docs with Swagger UI
- **Database Migrations**: Prisma ORM with automated schema management
- **Comprehensive Logging**: Structured logging with configurable levels
- **Health Checks**: Service monitoring and connectivity testing

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Next.js       │    │    FastAPI       │    │   PostgreSQL    │
│   Frontend      │◄──►│    Backend       │◄──►│   Database      │
│                 │    │                 │    │                 │
│ • React 18      │    │ • Python 3.12   │    │ • Prisma ORM    │
│ • TypeScript    │    │ • Async/Await   │    │ • Connection    │
│ • Tailwind CSS  │    │ • JWT Auth      │    │   Pooling       │
│ • Axios         │    │ • CORS          │    │ • Migrations    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────────┐
                    │   AI/ML Services    │
                    │                     │
                    │ • Document Analysis │
                    │ • Face Recognition  │
                    │ • Deepfake Detection│
                    │ • Risk Assessment   │
                    └─────────────────────┘
```

## 🚀 Quick Start

### Prerequisites
- **Node.js** 18+ and **npm**
- **Python** 3.12+
- **PostgreSQL** 15+ (or use Prisma Postgres Cloud)
- **Git**

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/verifyai.git
cd verifyai
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Edit .env with your database URL
# For Prisma Postgres Cloud: DATABASE_URL="postgresql://..."
# For local PostgreSQL: DATABASE_URL="postgresql://user:pass@localhost:5432/verifyai"

# Run database migrations
npx prisma migrate dev --name init

# Generate Prisma client
npx prisma generate

# Start the backend server
python main.py
```

The backend will start at `http://localhost:8000` with logs:
```
✔ Backend started at http://localhost:8000
✔ Database connected
✔ APIs registered
```

### 3. Frontend Setup

```bash
# Open new terminal and navigate to frontend
cd frontend

# Install Node.js dependencies
npm install

# Copy environment file
cp .env.local.example .env.local

# Edit .env.local with API URL (usually http://localhost:8000)
NEXT_PUBLIC_API_URL=http://localhost:8000

# Start the development server
npm run dev
```

The frontend will start at `http://localhost:3000`

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/api/v1/fake-document/health

## 📋 API Endpoints

### Authentication
```http
POST /api/v1/auth/register     # User registration
POST /api/v1/auth/login        # User login
POST /api/v1/auth/refresh      # Refresh access token
GET  /api/v1/auth/me           # Get current user profile
POST /api/v1/auth/logout       # Logout user
```

### Document Verification
```http
POST /api/v1/fake-document/upload    # Upload document for analysis
GET  /api/v1/fake-document/health    # Service health check
```

### Face Matching
```http
POST /api/v1/face-matching/run       # Compare document photo with selfie
```

### Deepfake Detection
```http
POST /api/v1/deepfake/run           # Analyze video/image for deepfakes
```

### Risk Scoring
```http
POST /api/v1/risk-scoring/run       # Calculate risk assessment
```

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```env
# Database
DATABASE_URL="postgresql://user:pass@host:5432/db"

# JWT Configuration
JWT_SECRET_KEY="your-secret-key-here"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS Origins
CORS_ORIGINS=["http://localhost:3000", "http://localhost:3001"]

# Logging
LOG_LEVEL=INFO
```

#### Frontend (.env.local)
```env
# API Configuration
NEXT_PUBLIC_API_URL=http://localhost:8000

# Optional: Analytics, Monitoring
NEXT_PUBLIC_GA_ID=your-google-analytics-id
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
python -m pytest tests/ -v
```

### Frontend Tests
```bash
cd frontend
npm test
```

### Manual Testing
1. Register a new user account
2. Login and obtain JWT token
3. Upload a document for fake detection
4. Check analysis results and database entries

## 📊 Database Schema

The application uses Prisma ORM with PostgreSQL. Key models include:

- **Users**: Authentication and profile data
- **Sessions**: JWT token management
- **VerificationSessions**: Document verification workflows
- **FeatureResults**: AI analysis results storage
- **AuditLogs**: Compliance and security logging

View the complete schema in `backend/prisma/schema.prisma`

## 🔍 Monitoring & Logging

### Backend Logging
The backend provides structured logging for all operations:
```
[UPLOAD] File received: passport.jpg (image/jpeg)
[PREPROCESS] Converting image to base64...
[OCR] Starting text extraction...
[FORGERY] Analyzing document for tampering...
[DB] Saving results to database...
[DONE] Response sent - Processing time: 1250 ms
```

### Health Checks
```bash
# Backend health
curl http://localhost:8000/api/v1/fake-document/health

# Database connectivity
curl http://localhost:8000/api/v1/health/db
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 for Python code
- Use TypeScript strict mode
- Write comprehensive tests
- Update documentation
- Ensure all CI checks pass

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Next.js** - The React framework for production
- **FastAPI** - Modern, fast web framework for Python
- **Prisma** - Next-generation ORM for TypeScript & Node.js
- **Tailwind CSS** - A utility-first CSS framework
- **PostgreSQL** - Advanced open source relational database

## 📞 Support

For support, email support@verifyai.com or join our [Discord community](https://discord.gg/verifyai).

---

<div align="center">
  <p>Built with ❤️ for secure identity verification</p>
  <p>
    <a href="#features">Features</a> •
    <a href="#quick-start">Quick Start</a> •
    <a href="#api-endpoints">API</a> •
    <a href="#contributing">Contributing</a>
  </p>
</div></content>
<parameter name="filePath">e:\sbs\README.md