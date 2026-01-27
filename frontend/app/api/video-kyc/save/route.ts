import { NextRequest, NextResponse } from 'next/server'

interface SaveKYCRequest {
  sessionId: string
  name: string
  dob: string
  address: string
  income: string
  employment: string
  aadhar: string
  profile: string
  signature: string
  pan?: string
}

export async function POST(request: NextRequest) {
  try {
    const data: SaveKYCRequest = await request.json()

    // Validate required fields
    const requiredFields = ['name', 'dob', 'address', 'income', 'employment', 'aadhar', 'profile']
    for (const field of requiredFields) {
      if (!data[field as keyof SaveKYCRequest]) {
        return NextResponse.json(
          { error: `Missing required field: ${field}` },
          { status: 400 }
        )
      }
    }

    // In a real implementation, you would:
    // 1. Save to database (Prisma)
    // 2. Create verification record
    // 3. Trigger background verification jobs
    // 4. Send notifications

    // Simulate database save
    await new Promise(resolve => setTimeout(resolve, 1500))

    // Calculate risk score (simulated)
    const riskScore = Math.random() * 3 + 7 // 7-10 range (low risk)

    return NextResponse.json(
      {
        success: true,
        sessionId: data.sessionId,
        status: 'saved',
        riskScore: parseFloat(riskScore.toFixed(2)),
        message: 'KYC data saved successfully'
      },
      { status: 200 }
    )
  } catch (error) {
    console.error('Save error:', error)
    return NextResponse.json(
      { error: 'Failed to save KYC data' },
      { status: 500 }
    )
  }
}
