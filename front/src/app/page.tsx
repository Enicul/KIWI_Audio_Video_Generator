import { SignedIn, SignedOut } from "@clerk/nextjs";
import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-screen bg-kiwi-black bg-pattern">
      {/* Hero Section */}
      <section className="relative flex flex-col items-center justify-center min-h-screen px-6 py-20">
        {/* Background Decoration */}
        <div className="absolute inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-1/4 left-1/3 w-[500px] h-[500px] bg-kiwi-gray-800/15 rounded-full blur-3xl" />
          <div className="absolute bottom-1/4 right-1/3 w-[400px] h-[400px] bg-kiwi-gray-700/10 rounded-full blur-3xl" />
        </div>

        <div className="relative z-10 max-w-4xl mx-auto text-center animate-fade-in">
          {/* Logo */}
          <div className="inline-flex items-center justify-center w-20 h-20 rounded-3xl bg-gradient-to-br from-kiwi-gray-700 to-kiwi-gray-900 shadow-card mb-8">
            <svg
              className="w-10 h-10 text-kiwi-white"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
              />
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>

          {/* Title */}
          <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold text-kiwi-white mb-6 tracking-tight">
            KIWI-Video
          </h1>

          {/* Subtitle */}
          <p className="text-xl md:text-2xl text-kiwi-gray-400 mb-12 max-w-2xl mx-auto leading-relaxed">
            Simple, Efficient Video Platform
            <br />
            <span className="text-kiwi-gray-500">Built for Creators and Viewers</span>
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <SignedOut>
              <Link
                href="/sign-in"
                className="group relative px-8 py-4 bg-kiwi-white text-kiwi-black font-medium rounded-xl hover:bg-kiwi-gray-200 transition-all duration-300 shadow-card hover:shadow-card-hover"
              >
                <span className="relative z-10">Get Started</span>
              </Link>
              <Link
                href="/sign-up"
                className="px-8 py-4 border border-kiwi-gray-700 text-kiwi-white font-medium rounded-xl hover:bg-kiwi-gray-800 hover:border-kiwi-gray-600 transition-all duration-300"
              >
                Create Account
              </Link>
            </SignedOut>
            <SignedIn>
              <Link
                href="/dashboard"
                className="group relative px-8 py-4 bg-kiwi-white text-kiwi-black font-medium rounded-xl hover:bg-kiwi-gray-200 transition-all duration-300 shadow-card hover:shadow-card-hover"
              >
                <span className="relative z-10">Go to Dashboard</span>
              </Link>
            </SignedIn>
          </div>
        </div>

        {/* Features */}
        <div className="relative z-10 mt-24 grid grid-cols-1 md:grid-cols-3 gap-6 max-w-5xl mx-auto px-6">
          {/* Feature Card 1 */}
          <div className="group p-6 bg-kiwi-dark/50 border border-kiwi-gray-800 rounded-2xl backdrop-blur-sm hover:border-kiwi-gray-700 transition-all duration-300">
            <div className="w-12 h-12 rounded-xl bg-kiwi-gray-800 flex items-center justify-center mb-4 group-hover:bg-kiwi-gray-700 transition-colors">
              <svg
                className="w-6 h-6 text-kiwi-gray-300"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-kiwi-white mb-2">
              Lightning Fast
            </h3>
            <p className="text-kiwi-gray-400 text-sm leading-relaxed">
              Advanced architecture for smooth video playback experience
            </p>
          </div>

          {/* Feature Card 2 */}
          <div className="group p-6 bg-kiwi-dark/50 border border-kiwi-gray-800 rounded-2xl backdrop-blur-sm hover:border-kiwi-gray-700 transition-all duration-300">
            <div className="w-12 h-12 rounded-xl bg-kiwi-gray-800 flex items-center justify-center mb-4 group-hover:bg-kiwi-gray-700 transition-colors">
              <svg
                className="w-6 h-6 text-kiwi-gray-300"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-kiwi-white mb-2">
              Secure & Reliable
            </h3>
            <p className="text-kiwi-gray-400 text-sm leading-relaxed">
              Enterprise-grade security to protect your data and privacy
            </p>
          </div>

          {/* Feature Card 3 */}
          <div className="group p-6 bg-kiwi-dark/50 border border-kiwi-gray-800 rounded-2xl backdrop-blur-sm hover:border-kiwi-gray-700 transition-all duration-300">
            <div className="w-12 h-12 rounded-xl bg-kiwi-gray-800 flex items-center justify-center mb-4 group-hover:bg-kiwi-gray-700 transition-colors">
              <svg
                className="w-6 h-6 text-kiwi-gray-300"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z"
                />
              </svg>
            </div>
            <h3 className="text-lg font-semibold text-kiwi-white mb-2">
              Clean Design
            </h3>
            <p className="text-kiwi-gray-400 text-sm leading-relaxed">
              Minimalist interface design, focused on content
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="border-t border-kiwi-gray-800 py-8 px-6">
        <div className="max-w-5xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded-md bg-kiwi-gray-800 flex items-center justify-center">
              <svg
                className="w-4 h-4 text-kiwi-gray-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z"
                />
              </svg>
            </div>
            <span className="text-kiwi-gray-500 text-sm">KIWI-Video</span>
          </div>
          <p className="text-kiwi-gray-600 text-sm">
            © {new Date().getFullYear()} KIWI-Video. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}

