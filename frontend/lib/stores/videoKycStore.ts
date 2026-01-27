import { create } from 'zustand'

export interface KYCData {
  name: string
  dob: string
  address: string
  income: string
  employment: string
  aadhar: string
  pan: string
  profile: string
  signature: string
  status: 'pending' | 'approved' | 'rejected'
}

export interface ChatMessage {
  text: string
  type: 'agent' | 'user'
  timestamp: Date
}

interface VideoKYCState {
  // Session
  sessionId: string | null
  sessionStatus: 'idle' | 'document-upload' | 'video-recording' | 'ai-analysis' | 'agent-review' | 'completed' | 'rejected'
  
  // KYC Data
  kycData: KYCData
  
  // Pipeline
  currentStep: number
  currentQuestion: string
  
  // Chat
  messages: ChatMessage[]
  
  // Agent
  agentName: string | null
  
  // Verification Status
  documentVerified: boolean
  faceMatched: boolean
  livenessChecked: boolean
  riskScore: number | null
  
  // Actions
  setSessionId: (id: string) => void
  setSessionStatus: (status: VideoKYCState['sessionStatus']) => void
  updateKYCData: (key: keyof KYCData, value: string) => void
  setCurrentStep: (step: number) => void
  setCurrentQuestion: (question: string) => void
  addMessage: (message: Omit<ChatMessage, 'timestamp'>) => void
  setAgentName: (name: string) => void
  setDocumentVerified: (verified: boolean) => void
  setFaceMatched: (matched: boolean) => void
  setLivenessChecked: (checked: boolean) => void
  setRiskScore: (score: number) => void
  reset: () => void
}

const initialKYCData: KYCData = {
  name: '',
  dob: '',
  address: '',
  income: '',
  employment: '',
  aadhar: '',
  pan: '',
  profile: '',
  signature: '',
  status: 'pending'
}

export const useVideoKYCStore = create<VideoKYCState>((set) => ({
  sessionId: null,
  sessionStatus: 'idle',
  kycData: initialKYCData,
  currentStep: 0,
  currentQuestion: '',
  messages: [],
  agentName: null,
  documentVerified: false,
  faceMatched: false,
  livenessChecked: false,
  riskScore: null,
  
  setSessionId: (id) => set({ sessionId: id }),
  setSessionStatus: (status) => set({ sessionStatus: status }),
  updateKYCData: (key, value) => set((state) => ({
    kycData: { ...state.kycData, [key]: value }
  })),
  setCurrentStep: (step) => set({ currentStep: step }),
  setCurrentQuestion: (question) => set({ currentQuestion: question }),
  addMessage: (message) => set((state) => ({
    messages: [...state.messages, { ...message, timestamp: new Date() }]
  })),
  setAgentName: (name) => set({ agentName: name }),
  setDocumentVerified: (verified) => set({ documentVerified: verified }),
  setFaceMatched: (matched) => set({ faceMatched: matched }),
  setLivenessChecked: (checked) => set({ livenessChecked: checked }),
  setRiskScore: (score) => set({ riskScore: score }),
  reset: () => set({
    sessionId: null,
    sessionStatus: 'idle',
    kycData: initialKYCData,
    currentStep: 0,
    currentQuestion: '',
    messages: [],
    agentName: null,
    documentVerified: false,
    faceMatched: false,
    livenessChecked: false,
    riskScore: null
  })
}))
