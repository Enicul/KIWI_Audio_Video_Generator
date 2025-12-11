"use client";

import { SignIn } from "@clerk/nextjs";

export default function SignInPage() {
  return (
    <div className="min-h-screen bg-kiwi-black bg-pattern flex items-center justify-center p-4">
      {/* Background Decoration */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {/* Gradient Glow */}
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-kiwi-gray-800/20 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-kiwi-gray-700/10 rounded-full blur-3xl" />
      </div>

      {/* Sign In Card Container */}
      <div className="relative z-10 w-full max-w-md animate-slide-up">
        {/* Logo and Title */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-br from-kiwi-gray-700 to-kiwi-gray-900 shadow-card mb-6">
            <svg
              className="w-8 h-8 text-kiwi-white"
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
          <h1 className="text-2xl font-semibold text-kiwi-white mb-2">
            Welcome Back
          </h1>
          <p className="text-kiwi-gray-400">
            Sign in to KIWI-Video to continue
          </p>
        </div>

        {/* Clerk Sign In Component */}
        <div className="bg-kiwi-dark border border-kiwi-gray-800 rounded-2xl shadow-card p-1 backdrop-blur-sm">
          <SignIn
            appearance={{
              elements: {
                rootBox: "w-full",
                card: "bg-transparent shadow-none border-0 w-full",
                headerTitle: "hidden",
                headerSubtitle: "hidden",
                socialButtonsBlockButton:
                  "bg-kiwi-gray-800 border border-kiwi-gray-700 text-kiwi-white hover:bg-kiwi-gray-700 transition-all duration-200",
                socialButtonsBlockButtonText: "font-medium",
                dividerLine: "bg-kiwi-gray-700",
                dividerText: "text-kiwi-gray-500 text-sm",
                formFieldLabel: "text-kiwi-gray-300 text-sm font-medium",
                formFieldInput:
                  "bg-kiwi-gray-900 border border-kiwi-gray-700 text-kiwi-white rounded-lg focus:border-kiwi-gray-500 focus:ring-1 focus:ring-kiwi-gray-500 transition-all duration-200",
                formButtonPrimary:
                  "bg-kiwi-white text-kiwi-black font-medium hover:bg-kiwi-gray-200 transition-all duration-200 rounded-lg",
                footerActionLink:
                  "text-kiwi-gray-400 hover:text-kiwi-white transition-colors",
                identityPreviewText: "text-kiwi-white",
                identityPreviewEditButton:
                  "text-kiwi-gray-400 hover:text-kiwi-white",
                formFieldInputShowPasswordButton: "text-kiwi-gray-400",
                otpCodeFieldInput:
                  "bg-kiwi-gray-900 border border-kiwi-gray-700 text-kiwi-white",
                formFieldWarningText: "text-amber-400",
                formFieldErrorText: "text-red-400",
                alert: "bg-kiwi-gray-800 border border-kiwi-gray-700 text-kiwi-white",
                alertText: "text-kiwi-gray-300",
              },
              layout: {
                socialButtonsPlacement: "top",
                socialButtonsVariant: "blockButton",
              },
            }}
            routing="path"
            path="/sign-in"
            signUpUrl="/sign-up"
          />
        </div>

        {/* Footer Info */}
        <p className="text-center text-kiwi-gray-500 text-sm mt-6">
          Don&apos;t have an account?{" "}
          <a
            href="/sign-up"
            className="text-kiwi-gray-300 hover:text-kiwi-white transition-colors"
          >
            Sign up now
          </a>
        </p>
      </div>
    </div>
  );
}

