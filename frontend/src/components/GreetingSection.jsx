export default function GreetingSection() {
  return (
    <div className="flex flex-col items-center justify-center flex-1 px-8 relative">
      {/* Micron logo top-right area */}
      <div className="absolute top-8 right-8">
        <div className="w-20 h-20 rounded-full border border-gray-200 bg-white/60 backdrop-blur-sm flex items-center justify-center shadow-sm">
          <svg width="44" height="36" viewBox="0 0 44 36" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path
              d="M2 34V2L14 20L22 8L30 20L42 2V34"
              stroke="url(#micron-grad)"
              strokeWidth="3.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              fill="none"
            />
            <defs>
              <linearGradient id="micron-grad" x1="2" y1="2" x2="42" y2="34" gradientUnits="userSpaceOnUse">
                <stop offset="0%" stopColor="#10a37f" />
                <stop offset="100%" stopColor="#0d8f6f" />
              </linearGradient>
            </defs>
          </svg>
        </div>
      </div>

      {/* Greeting text */}
      <div className="text-center mb-10 mt-4">
        <h1 className="text-4xl font-bold mb-1">
          <span className="text-[#10a37f]">Hello, Employee</span>
        </h1>
        <h2 className="text-3xl font-semibold text-gray-400">How can I help you today?</h2>
      </div>
    </div>
  )
}
