# Video-KYC Implementation

## Overview
A comprehensive Video-KYC (Know Your Customer) verification system integrated into the main application with real-time video capabilities, voice/text input, AI-powered verification, and agent review.

## Features

### 1. **Conversational Interface**
- Natural language questions guide users through verification
- Support for both voice and text input
- Text-to-speech feedback for accessibility
- Real-time chat interface showing conversation history

### 2. **Live Video Capture**
- WebRTC-based real-time camera access
- Live face detection overlay with guidelines
- Instant image capture for documents and selfies
- Mirrored view for better user experience

### 3. **Multi-Step Verification**
The system collects the following information:
1. Full name
2. Date of birth (DD-MM-YYYY format)
3. Residential address
4. Aadhar Card (with image capture)
5. Annual income range
6. Employment type
7. Profile photo (live capture)
8. Signature (image capture)

### 4. **AI-Powered Analysis**
- Document authenticity verification
- Face matching between document and live photo
- Liveness detection to prevent spoofing
- Risk score calculation

### 5. **Agent Review**
- Automatic agent assignment
- Human oversight for final approval
- Complete audit trail

### 6. **Security & Compliance**
- End-to-end encryption
- KYC/AML compliant
- Complete audit logs
- Secure session management

## Technology Stack

### Frontend
- **Next.js 14** - React framework
- **TypeScript** - Type safety
- **Zustand** - State management
- **Tailwind CSS** - Styling
- **Web Speech API** - Voice input/output
- **WebRTC** - Camera access

### Backend APIs
- `/api/video-kyc/upload` - Image upload and storage
- `/api/video-kyc/verify` - Face verification and liveness check
- `/api/video-kyc/save` - Save KYC data
- `/api/video-kyc/tts` - Text-to-speech (client-side fallback)

## File Structure

```
frontend/
├── app/
│   ├── video-kyc/
│   │   └── page.tsx                 # Main Video-KYC page
│   └── api/
│       └── video-kyc/
│           ├── upload/
│           │   └── route.ts         # Image upload API
│           ├── verify/
│           │   └── route.ts         # Face verification API
│           ├── save/
│           │   └── route.ts         # Save KYC data API
│           └── tts/
│               └── route.ts         # Text-to-speech API
├── components/
│   └── videokyc/
│       ├── VideoKYCWebcam.tsx      # Camera component
│       ├── ChatInterface.tsx        # Chat UI
│       └── VoiceInput.tsx          # Voice recognition
└── lib/
    ├── stores/
    │   └── videoKycStore.ts        # Zustand state management
    └── videoKycQuestions.ts        # Question configuration
```

## Usage

### Starting a Verification Session

1. Navigate to `/video-kyc`
2. Click "Start Verification"
3. Grant camera permissions
4. Follow the on-screen instructions

### Voice Input
- Click the microphone button
- Speak your answer clearly
- The system will transcribe and process your response

### Text Input
- Type your answer in the text field
- Press Enter or click "Submit Answer"

### Image Capture
- Position yourself/document in the frame
- Click the capture button when ready
- The system will automatically process and upload

## State Management

The application uses Zustand for state management with the following structure:

```typescript
interface VideoKYCState {
  sessionId: string | null
  sessionStatus: 'idle' | 'verification-flow' | ...
  kycData: KYCData
  currentStep: number
  currentQuestion: string
  messages: ChatMessage[]
  agentName: string | null
  documentVerified: boolean
  faceMatched: boolean
  livenessChecked: boolean
  riskScore: number | null
  // ... actions
}
```

## API Integration

### Upload Image
```typescript
const formData = new FormData()
formData.append('image', blob, 'capture.png')
formData.append('name', kycData.name)
formData.append('dob', kycData.dob)
formData.append('type', 'aadhar' | 'profile' | 'signature')

const response = await fetch('/api/video-kyc/upload', {
  method: 'POST',
  body: formData
})
```

### Verify Face
```typescript
const response = await fetch('/api/video-kyc/verify', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    profile: profileImageUrl,
    aadhar: aadharImageUrl,
    name: name,
    dob: dob
  })
})
```

### Save KYC Data
```typescript
const response = await fetch('/api/video-kyc/save', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    sessionId,
    ...kycData
  })
})
```

## Customization

### Adding New Questions

Edit `lib/videoKycQuestions.ts`:

```typescript
export const kycQuestions: KYCQuestion[] = [
  {
    type: 'field_name',
    question: 'Your question here?',
    prompt: 'AI processing prompt',
    requiresImage: false, // or true for image capture
    validation: (value) => value.length >= 3
  },
  // ... more questions
]
```

### Modifying UI Theme

The application uses Tailwind CSS with dark mode support. Modify colors in:
- `tailwind.config.ts` for global colors
- Component className props for specific styling

## Browser Compatibility

- **Chrome/Edge**: Full support
- **Firefox**: Full support  
- **Safari**: Partial (voice input may require fallback)
- **Mobile**: Supported with responsive design

## Security Considerations

1. **Camera Permissions**: Always request user consent
2. **Data Encryption**: All uploads use HTTPS
3. **Session Management**: Unique session IDs per verification
4. **Input Validation**: All inputs validated before processing
5. **Rate Limiting**: Implement on production APIs

## Future Enhancements

1. Integration with actual face-api.js for real face detection
2. Backend storage (AWS S3, Azure Blob)
3. Real-time agent dashboard
4. Multi-language support
5. Mobile app integration
6. Biometric verification
7. Blockchain-based audit trail

## Dependencies

```json
{
  "zustand": "^4.4.7",           // State management
  "next": "^14.0.0",             // React framework
  "react": "^18.2.0",            // UI library
  "typescript": "^5.0.0"         // Type safety
}
```

## Development

```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start
```

## Testing

Visit `http://localhost:3000/video-kyc` to test the implementation.

## Support

For issues or questions, please refer to the main project documentation or contact the development team.

---

**Note**: This is a demo implementation. For production use, integrate actual face recognition libraries, secure storage solutions, and comprehensive backend APIs.
