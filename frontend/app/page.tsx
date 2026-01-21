'use client'

import { Navbar } from '@/components/Navbar'
import { HeroSection } from '@/components/sections/HeroSection'
import { FeaturesSection } from '@/components/sections/FeaturesSection'
import { IdentityVerificationSection } from '@/components/sections/IdentityVerificationSection'
import { HowItWorksSection } from '@/components/sections/HowItWorksSection'
import { IntegrationSection } from '@/components/sections/IntegrationSection'
import { TestimonialsSection } from '@/components/sections/TestimonialsSection'
import { CTASection } from '@/components/sections/CTASection'
import { Footer } from '@/components/sections/Footer'

export default function Home() {
  return (
    <main className="min-h-screen bg-white dark:bg-dark-900 transition-colors">
      <Navbar />
      
      {/* Add top padding to account for fixed navbar */}
      <div className="pt-16">
        <HeroSection />
        <FeaturesSection />
        <IdentityVerificationSection />
        <HowItWorksSection />
        <IntegrationSection />
        <TestimonialsSection />
        <CTASection />
        <Footer />
      </div>
    </main>
  )
}

