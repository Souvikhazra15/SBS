'use client'

import { Navbar } from '@/components/Navbar'
import { HeroSection } from '@/components/sections/HeroSection'
import { FeaturesSection } from '@/components/sections/FeaturesSection'
import { HowItWorksSection } from '@/components/sections/HowItWorksSection'
import { IntegrationSection } from '@/components/sections/IntegrationSection'
import { TestimonialsSection } from '@/components/sections/TestimonialsSection'
import { CTASection } from '@/components/sections/CTASection'
import { Footer } from '@/components/sections/Footer'

export default function Home() {
  return (
    <main className="min-h-screen bg-white">
      <Navbar />
      
      {/* Add top padding to account for fixed navbar */}
      <div className="pt-16">
        <HeroSection />
        <FeaturesSection />
        <HowItWorksSection />
        <IntegrationSection />
        <TestimonialsSection />
        <CTASection />
        <Footer />
      </div>
    </main>
  )
}
