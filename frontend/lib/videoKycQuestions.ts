export interface KYCQuestion {
  type: string
  question: string
  prompt: string
  requiresImage?: boolean
  validation?: (value: string) => boolean
}

export const kycQuestions: KYCQuestion[] = [
  {
    type: 'name',
    question: 'What is your full name as per your government ID?',
    prompt: 'Identify and return only the name from the sentence',
    validation: (value) => value.length >= 3
  },
  {
    type: 'dob',
    question: 'What is your date of birth? (DD-MM-YYYY)',
    prompt: 'Please change only the date of birth in DD-MM-YYYY format',
    validation: (value) => /^\d{2}-\d{2}-\d{4}$/.test(value)
  },
  {
    type: 'address',
    question: 'What is your current residential address?',
    prompt: 'Extract only the residential address and remove any extra text',
    validation: (value) => value.length >= 10
  },
  {
    type: 'aadhar',
    question: 'Please show your Aadhar Card to the camera. Click capture when ready.',
    prompt: 'Extract only Aadhar Number from the image',
    requiresImage: true
  },
  {
    type: 'income',
    question: 'What is your estimated annual income range?',
    prompt: 'Extract only the estimated income range and remove any extra text',
    validation: (value) => value.length >= 3
  },
  {
    type: 'employment',
    question: 'What type of employment are you engaged in?',
    prompt: 'Extract only the type of employment remove any extra text',
    validation: (value) => value.length >= 3
  },
  {
    type: 'profile',
    question: 'Now, let\'s capture your profile photo. Please look directly at the camera.',
    prompt: '',
    requiresImage: true
  },
  {
    type: 'signature',
    question: 'Please show your signature to the camera.',
    prompt: '',
    requiresImage: true
  }
]
