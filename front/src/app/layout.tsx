import type { Metadata } from "next";
import {
  ClerkProvider,
  SignedIn,
  SignedOut,
  UserButton,
} from "@clerk/nextjs";
import "./globals.css";

export const metadata: Metadata = {
  title: "KIWI-Video",
  description: "Welcome to KIWI-Video - Your Video Platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ClerkProvider
      appearance={{
        variables: {
          colorPrimary: "#fafafa",
          colorBackground: "#1a1a1a",
          colorInputBackground: "#171717",
          colorInputText: "#fafafa",
          colorText: "#fafafa",
          colorTextSecondary: "#a3a3a3",
          borderRadius: "0.5rem",
        },
        elements: {
          formButtonPrimary:
            "bg-white text-black hover:bg-gray-200 transition-colors",
          card: "bg-kiwi-dark border border-kiwi-gray-800 shadow-card",
          headerTitle: "text-white",
          headerSubtitle: "text-gray-400",
          socialButtonsBlockButton:
            "bg-kiwi-gray-800 border border-kiwi-gray-700 text-white hover:bg-kiwi-gray-700",
          formFieldInput:
            "bg-kiwi-gray-900 border border-kiwi-gray-700 text-white",
          footerActionLink: "text-gray-400 hover:text-white",
        },
      }}
    >
      <html lang="en">
        <body className="bg-kiwi-black text-kiwi-white antialiased">
          {/* Header Navigation */}
          <header className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between px-6 py-4 bg-kiwi-black/80 backdrop-blur-md border-b border-kiwi-gray-800">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-kiwi-gray-600 to-kiwi-gray-800 flex items-center justify-center">
                <svg
                  className="w-5 h-5 text-kiwi-white"
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
              <span className="text-xl font-semibold tracking-tight">
                KIWI-Video
              </span>
            </div>

            {/* User Status */}
            <div className="flex items-center gap-4">
              <SignedOut>
                <a
                  href="/sign-in"
                  className="px-4 py-2 text-sm font-medium text-kiwi-gray-300 hover:text-kiwi-white transition-colors"
                >
                  Sign In
                </a>
                <a
                  href="/sign-up"
                  className="px-4 py-2 text-sm font-medium bg-kiwi-white text-kiwi-black rounded-lg hover:bg-kiwi-gray-200 transition-colors"
                >
                  Sign Up
                </a>
              </SignedOut>
              <SignedIn>
                <a
                  href="/dashboard"
                  className="px-4 py-2 text-sm font-medium text-kiwi-gray-300 hover:text-kiwi-white transition-colors"
                >
                  Dashboard
                </a>
                <UserButton
                  afterSignOutUrl="/"
                  appearance={{
                    elements: {
                      avatarBox: "w-9 h-9",
                    },
                  }}
                />
              </SignedIn>
            </div>
          </header>

          {/* Main Content */}
          <main className="pt-16">{children}</main>
        </body>
      </html>
    </ClerkProvider>
  );
}

