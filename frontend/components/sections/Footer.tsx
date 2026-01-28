'use client'

import React from 'react'

export function Footer() {
  const currentYear = new Date().getFullYear()

  const footerLinks = {
    Product: [
      { label: 'Features', href: '#' },
      { label: 'Pricing', href: '#' },
      { label: 'Security', href: '#' },
      { label: 'Roadmap', href: '#' },
    ],
    Company: [
      { label: 'About', href: '#' },
      { label: 'Blog', href: '#' },
      { label: 'Careers', href: '#' },
      { label: 'Contact', href: '#' },
    ],
    Legal: [
      { label: 'Privacy', href: '#' },
      { label: 'Terms', href: '#' },
      { label: 'Compliance', href: '#' },
      { label: 'Cookies', href: '#' },
    ],
    Resources: [
      { label: 'Documentation', href: '#' },
      { label: 'API Reference', href: '#' },
      { label: 'Support', href: '#' },
      { label: 'Status', href: '#' },
    ],
  }

  return (
    <footer id="contact" className="bg-dark-900 dark:bg-dark-950 text-dark-400 dark:text-dark-500 transition-colors border-t border-dark-800 dark:border-dark-800">
      <div className="container-wide py-16">
        {/* Main content */}
        <div className="grid md:grid-cols-5 gap-8 mb-12">
          {/* Brand */}
          <div>
            <div className="font-bold text-2xl bg-gradient-to-r from-primary-500 to-primary-600 dark:from-primary-400 dark:to-primary-500 bg-clip-text text-transparent mb-3">Deep Defenders</div>
            <p className="text-sm text-dark-500 dark:text-dark-600">
              Enterprise identity verification platform. Secure. Compliant. Simple.
            </p>
          </div>

          {/* Links */}
          {Object.entries(footerLinks).map(([category, links]) => (
            <div key={category}>
              <h3 className="font-semibold text-white dark:text-dark-200 mb-4">{category}</h3>
              <ul className="space-y-2">
                {links.map((link) => (
                  <li key={link.label}>
                    <a
                      href={link.href}
                      className="text-sm hover:text-white dark:hover:text-dark-300 transition-colors"
                    >
                      {link.label}
                    </a>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* Divider */}
        <div className="border-t border-dark-700 dark:border-dark-800 pt-8 mt-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            {/* Copyright */}
            <p className="text-sm text-dark-500 dark:text-dark-600 mb-4 md:mb-0">
              © {currentYear} Deep Defenders. All rights reserved.
            </p>

            {/* Social links */}
            <div className="flex gap-6">
              <a href="#" className="text-dark-400 dark:text-dark-500 hover:text-white dark:hover:text-dark-300 transition-colors">
                Twitter
              </a>
              <a href="#" className="text-dark-400 dark:text-dark-500 hover:text-white dark:hover:text-dark-300 transition-colors">
                LinkedIn
              </a>
              <a href="#" className="text-dark-400 dark:text-dark-500 hover:text-white dark:hover:text-dark-300 transition-colors">
                GitHub
              </a>
            </div>
          </div>
        </div>
      </div>
    </footer>
  )
}
