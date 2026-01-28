# DeepDefenders

A comprehensive AI-powered Video-KYC (Know Your Customer) identity verification platform with real-time video processing, OCR document scanning, face matching, and automated risk assessment.

## 🚀 Features

### Core Verification Features
- **Real-time Video KYC**: Conversational video verification with live agent support
- **ID Document OCR**: Automatic extraction of ID numbers from government documents
- **Face Matching**: Biometric verification against document photos
- **Liveness Detection**: Anti-spoofing measures to ensure physical presence
- **Deepfake Detection**: AI-powered analysis to detect manipulated media
- **Risk Scoring**: Comprehensive risk assessment with automated decision making
- **Agent Review**: Human oversight for edge cases and final approval

### User Experience
- **Multi-step Verification Flow**: Guided process with progress tracking
- **Voice & Text Input**: Flexible input methods for accessibility
- **Real-time Feedback**: Instant validation and status updates
- **Mobile Responsive**: Works seamlessly on all devices
- **Dark/Light Theme**: User preference-based theming

### Enterprise Features
- **Audit Trail**: Complete verification history and logs
- **Compliance Ready**: KYC/AML compliant with regulatory standards
- **Scalable Architecture**: Built for high-volume processing
- **API-First Design**: RESTful APIs for easy integration

## 🛠 Tech Stack

### Backend
- **FastAPI**: High-performance async web framework
- **Prisma ORM**: Type-safe database access with PostgreSQL
- **PaddleOCR**: Advanced OCR for document processing
- **OpenCV**: Computer vision for image processing
- **PyTorch**: Deep learning models for AI analysis
- **JWT Authentication**: Secure token-based auth

### Frontend
- **Next.js 14**: React framework with App Router
- **TypeScript**: Type-safe development
- **Tailwind CSS**: Utility-first styling
- **Zustand**: Lightweight state management
- **React Webcam**: Camera integration
- **Web Speech API**: Voice input support

### Database
- **PostgreSQL**: Robust relational database
- **Prisma Migrations**: Version-controlled schema management

### AI/ML Models
- **Face Detection**: MTCNN for facial landmark detection
- **Face Recognition**: FaceNet embeddings for matching
- **Deepfake Detection**: Custom CNN models
- **Document Analysis**: OCR with pattern recognition

## 📋 Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.8+ and pip
- **PostgreSQL** 13+
- **Git** for version control

## 🚀 Quick Start

### 1. Clone the Repository
```bash
git clone <repository-url>
cd video-kyc-platform
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env

# Update database URL in .env
# DATABASE_URL="postgresql://username:password@localhost:5432/video_kyc"

# Run database migrations
npx prisma migrate deploy

# Generate Prisma client
npx prisma generate

# Start the backend server
python main.py
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory (in new terminal)
cd frontend

# Install dependencies
npm install

# Copy environment file
cp .env.local.example .env.local

# Start development server
npm run dev
```

### 4. Access the Application

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs

## 📖 Usage

### User Flow

1. **Registration**: User creates account with email verification
2. **Video-KYC Initiation**: Start verification session
3. **Information Collection**: Answer conversational questions
4. **ID Document Capture**: Scan government-issued ID with OCR
5. **Biometric Verification**: Face matching and liveness detection
6. **AI Analysis**: Automated document and risk analysis
7. **Agent Review**: Human verification for complex cases
8. **Completion**: Final approval and certificate generation

### API Usage

#### Start Video-KYC Session
```bash
POST /api/v1/video-kyc/session/start
Authorization: Bearer <token>
```

#### Upload ID Document
```bash
POST /api/v1/video-kyc/capture-id
Content-Type: multipart/form-data
FormData:
  - file: <image_file>
  - session_id: <session_id>
```

#### Submit Answer
```bash
POST /api/v1/video-kyc/answer/submit
{
  "sessionId": "string",
  "questionId": "string",
  "answerText": "string",
  "answerType": "text|voice"
}
```

## 🗄 Database Schema

### Core Tables

#### Users
- User management with role-based access
- Profile information and verification status

#### Video KYC Sessions
- Session management and progress tracking
- KYC data collection and verification results

#### Video KYC Documents
- OCR results and document verification
- Image storage and processing metadata

#### Verification Results
- AI analysis results and risk scores
- Audit trail for compliance

### Key Relationships
```
User (1) ──── (N) VideoKYCSession
VideoKYCSession (1) ──── (N) VideoKycDocument
VideoKYCSession (1) ──── (N) VerificationResult
```

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```env
DATABASE_URL=postgresql://user:pass@localhost:5432/video_kyc
JWT_SECRET=your-super-secret-jwt-key
WEBHOOK_URL=https://your-webhook-endpoint.com
REDIS_URL=redis://localhost:6379
```

#### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_WS_URL=ws://localhost:8000
```

### Database Configuration

The application uses Prisma for database management:

```bash
# Create new migration
npx prisma migrate dev --name <migration_name>

# Reset database (development only)
npx prisma migrate reset

# View database
npx prisma studio
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest tests/ -v
```

### Frontend Tests
```bash
cd frontend
npm test
```

### End-to-End Tests
```bash
npm run test:e2e
```

## 📊 Monitoring & Logging

### Application Logs
- Structured logging with JSON format
- Log levels: DEBUG, INFO, WARNING, ERROR
- Centralized log aggregation support

### Performance Monitoring
- API response times
- Database query performance
- AI model inference times

### Health Checks
- `/health` endpoint for service status
- Database connectivity checks
- External service dependencies

## 🔒 Security

### Authentication
- JWT-based authentication
- Refresh token rotation
- Multi-factor authentication support

### Data Protection
- End-to-end encryption for sensitive data
- GDPR compliant data handling
- Secure file storage with access controls

### API Security
- Rate limiting and throttling
- Input validation and sanitization
- CORS configuration
- Helmet.js security headers

## 🚀 Deployment

### Production Checklist
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] SSL certificates installed
- [ ] Domain configured
- [ ] Monitoring and logging set up
- [ ] Backup strategy implemented

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up -d

# Scale services
docker-compose up -d --scale backend=3
```

### Cloud Deployment
- **AWS**: ECS/EKS with RDS PostgreSQL
- **GCP**: Cloud Run with Cloud SQL
- **Azure**: Container Apps with PostgreSQL

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create feature branch: `git checkout -b feature/your-feature`
3. Make changes and add tests
4. Run linting: `npm run lint`
5. Commit changes: `git commit -am 'Add new feature'`
6. Push to branch: `git push origin feature/your-feature`
7. Create Pull Request

### Code Standards
- **TypeScript**: Strict type checking enabled
- **Python**: Black formatting and Flake8 linting
- **Git**: Conventional commit messages
- **Testing**: Minimum 80% code coverage

### Branch Strategy
- `main`: Production-ready code
- `develop`: Integration branch
- `feature/*`: Feature development
- `hotfix/*`: Critical bug fixes

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Documentation
- [API Documentation](http://localhost:8000/docs)
- [Video-KYC Guide](./frontend/VIDEO_KYC_README.md)
- [Architecture Overview](./docs/architecture.md)

### Community
- **Issues**: [GitHub Issues](https://github.com/your-repo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-repo/discussions)
- **Email**: support@yourcompany.com

### Troubleshooting
- Check application logs
- Verify database connectivity
- Ensure all dependencies are installed
- Review environment configuration

---

**Built with ❤️ for secure and compliant identity verification**</content>
<parameter name="filePath">e:\sbs\README.md
