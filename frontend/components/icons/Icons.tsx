'use client'

export function ShieldVerifyIcon({ className = "w-6 h-6" }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={1.5}
        d="M12 8.25c.75 0 1.5.225 2.25.675m-2.25-.675V6c0-1.5 1.5-3 3-3s3 1.5 3 3v.925M12 8.25c-.75 0-1.5.225-2.25.675m0 0V6c0-1.5-1.5-3-3-3s-3 1.5-3 3v.925m9.75 8.175v3.225c0 1.5-1.5 3-3 3h-6c-1.5 0-3-1.5-3-3v-3.225m12 0l.75-4.5h-12.75l.75 4.5m0 0l-.075.45c0 1.5.75 3 2.25 3h6c1.5 0 2.25-1.5 2.25-3l-.075-.45"
      />
    </svg>
  )
}

export function ZapIcon({ className = "w-6 h-6" }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={1.5}
        d="M13 10V3L4 14h7v7l9-11h-7z"
      />
    </svg>
  )
}

export function CheckCircleIcon({ className = "w-6 h-6" }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={1.5}
        d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
      />
    </svg>
  )
}

export function DocumentIcon({ className = "w-6 h-6" }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={1.5}
        d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.66V6.75a9 9 0 015.25-1.5m-5.25 0A2.25 2.25 0 113.75 7.5M5.25 9a3 3 0 015.25 2.25M5.25 9a3 3 0 018.25 2.25m0 0H20.25A2.25 2.25 0 0022.5 13.5v6.75A2.25 2.25 0 0020.25 22H3.75A2.25 2.25 0 011.5 19.5v-6.75a2.25 2.25 0 012.25-2.25"
      />
    </svg>
  )
}

export function GlobalIcon({ className = "w-6 h-6" }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={1.5}
        d="M12 21a9.004 9.004 0 008.716-6.747M12 21c2.485 0 4.798-.696 6.787-1.923m-11.287-3.423h.75a.75.75 0 010 1.5h-.75m0-4.5h.75a.75.75 0 010 1.5h-.75m5.25-9a6 6 0 11-12 0 6 6 0 0112 0zM12.75 12.75a.75.75 0 11-1.5 0 .75.75 0 011.5 0z"
      />
    </svg>
  )
}

export function APIIcon({ className = "w-6 h-6" }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={1.5}
        d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.537.046-1.06.147-1.565.297m0 0a6.75 6.75 0 010 12.669m1.565-.297a6.75 6.75 0 015.48 2.623m0 0h2.194m.604-1.976a8.25 8.25 0 01-10.605 4.134m7.411-4.134a5.25 5.25 0 017.794 7.794"
      />
    </svg>
  )
}

export function ArrowRightIcon({ className = "w-6 h-6" }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={1.5}
        d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3"
      />
    </svg>
  )
}

export function StarIcon({ className = "w-6 h-6" }: { className?: string }) {
  return (
    <svg className={className} fill="currentColor" viewBox="0 0 24 24">
      <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
    </svg>
  )
}
