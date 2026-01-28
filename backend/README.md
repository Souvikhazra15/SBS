# Deep Defenders Backend - Prisma Database Schema

Complete database structure for the KYC/Identity Verification Platform.

## Database Models

### User Management
- **User** - User accounts with authentication, profile, and settings
- **Session** - User sessions with JWT tokens and refresh tokens
- **ApiKey** - API keys for programmatic access

### Verification Process
- **Verification** - Main verification workflow tracking
- **Document** - Document uploads with OCR and fraud detection
- **FaceMatch** - Face matching between document and selfie
- **LivenessCheck** - Liveness and deepfake detection
- **AMLCheck** - Anti-Money Laundering compliance checks
- **FraudCheck** - Fraud detection signals and indicators
- **RiskAssessment** - ML-based risk scoring

### Audit & Analytics
- **AuditLog** - Comprehensive audit trail
- **VerificationMetrics** - Daily analytics and KPIs

## Setup Instructions

### 1. Install Dependencies

```bash
cd backend
npm install
```

### 2. Configure Database

Copy `.env.example` to `.env` and update the `DATABASE_URL`:

```bash
cp .env.example .env
```

For PostgreSQL (recommended):
```env
DATABASE_URL="postgresql://username:password@localhost:5432/deepdefenders?schema=public"
```

For MySQL:
```env
DATABASE_URL="mysql://username:password@localhost:3306/deepdefenders"
```

For SQLite (development only):
```env
DATABASE_URL="file:./dev.db"
```

### 3. Run Migrations

Create and apply database migrations:

```bash
npm run prisma:migrate
```

### 4. Generate Prisma Client

```bash
npm run prisma:generate
```

### 5. Open Prisma Studio (Optional)

Explore your data visually:

```bash
npm run prisma:studio
```

## Available Scripts

- `npm run prisma:generate` - Generate Prisma Client
- `npm run prisma:migrate` - Create and run migrations
- `npm run prisma:studio` - Open Prisma Studio
- `npm run prisma:deploy` - Deploy migrations (production)
- `npm run prisma:reset` - Reset database (⚠️ deletes all data)

## Database Schema Overview

### User Journey Flow

1. **Signup** → Creates `User` record with `PENDING_VERIFICATION` status
2. **Login** → Creates `Session` with JWT token
3. **Start Verification** → Creates `Verification` record
4. **Upload Document** → Creates `Document` record with OCR processing
5. **Face Match** → Creates `FaceMatch` comparing document photo to selfie
6. **Liveness Check** → Creates `LivenessCheck` for deepfake detection
7. **AML Check** → Creates `AMLCheck` screening against watchlists
8. **Fraud Check** → Creates `FraudCheck` analyzing fraud signals
9. **Risk Assessment** → Creates `RiskAssessment` with final score
10. **Completion** → Updates `Verification` status to `COMPLETED/REJECTED`

### Key Features

✅ **Multi-level KYC** - Support for BASIC, STANDARD, ENHANCED, PREMIUM verification levels
✅ **Document Verification** - OCR, authenticity checks, tampering detection
✅ **Biometric Face Matching** - Face recognition with confidence scoring
✅ **Liveness Detection** - Anti-spoofing and deepfake detection
✅ **AML Compliance** - Sanctions screening (OFAC, UN, EU, Interpol)
✅ **Fraud Detection** - IP/device fingerprinting, duplicate detection
✅ **Risk Scoring** - ML-based risk assessment with component scores
✅ **Audit Trail** - Comprehensive logging for compliance
✅ **Analytics** - Daily metrics and KPIs

### Security Features

- Password hashing (implement with bcrypt)
- JWT authentication with refresh tokens
- Two-factor authentication support
- API key management with scoped permissions
- Rate limiting support
- Session management
- Audit logging for all actions

## Next Steps

1. Implement API server (Express/Fastify/NestJS)
2. Add authentication middleware
3. Implement document upload (AWS S3/Cloudinary)
4. Integrate OCR service (AWS Textract/Google Vision)
5. Add face matching (AWS Rekognition/Face++)
6. Implement AML screening provider
7. Build ML risk scoring model
8. Add webhook notifications
9. Create admin dashboard

## Production Considerations

- Use PostgreSQL for production
- Enable connection pooling (PgBouncer)
- Set up read replicas for analytics
- Implement database backups
- Add database monitoring
- Use environment-specific .env files
- Enable SSL for database connections
- Implement rate limiting
- Add request caching (Redis)
- Set up error tracking (Sentry)

## Support

For questions or issues with the schema, please refer to:
- [Prisma Documentation](https://www.prisma.io/docs)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
