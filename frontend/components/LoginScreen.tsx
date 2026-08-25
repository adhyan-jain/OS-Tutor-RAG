"use client";

import { signIn } from "next-auth/react";

/** Shown instead of the chat UI when AUTH_ENABLED is on and the visitor
 * isn't signed in yet. Only rendered from AuthGate, which already guards
 * this whole subtree behind a SessionProvider. */
export default function LoginScreen() {
  return (
    <div className="flex flex-col items-center justify-center h-dvh gap-6 px-4 text-center">
      <div className="space-y-2">
        <h1 className="text-lg font-semibold tracking-tight">OS Tutor</h1>
        <p className="text-sm text-[var(--color-muted-foreground)] max-w-xs">
          Sign in with Google to start a conversation with the course tutor.
        </p>
      </div>
      <button
        type="button"
        onClick={() => signIn("google")}
        className="inline-flex items-center gap-2 rounded-md border border-[var(--color-border)] px-4 py-2 text-sm font-medium hover:bg-[var(--color-surface)] transition-colors"
      >
        Sign in with Google
      </button>
    </div>
  );
}
