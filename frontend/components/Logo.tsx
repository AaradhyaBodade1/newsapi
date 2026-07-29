export default function Logo({ size = 32 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" aria-hidden className="shrink-0">
      <defs>
        <linearGradient id="arkaBlueGrad" x1="0" y1="1" x2="1" y2="0">
          <stop offset="0" stopColor="#1e3a8a" />
          <stop offset="1" stopColor="#3b82f6" />
        </linearGradient>
        <linearGradient id="arkaOrangeGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="#fb923c" />
          <stop offset="1" stopColor="#c2410c" />
        </linearGradient>
      </defs>
      <rect width="100" height="100" rx="22" fill="#ffffff" />
      <path
        d="M18 76 C 10 58, 22 34, 45 27 L 80 10"
        fill="none"
        stroke="url(#arkaBlueGrad)"
        strokeWidth="11"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <polygon points="93,4 84,17 76,4" fill="url(#arkaBlueGrad)" />
      <path
        d="M32 80 L50 22 L68 80"
        fill="none"
        stroke="#ffffff"
        strokeWidth="17"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path
        d="M32 80 L50 22 L68 80"
        fill="none"
        stroke="url(#arkaOrangeGrad)"
        strokeWidth="10"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
