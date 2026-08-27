"use client";

import { SessionProvider, signOut, useSession } from "next-auth/react";
import Chat from "./Chat";
import LoginScreen from "./LoginScreen";
import { AUTH_ENABLED } from "@/lib/auth-config";

/** Renders the signed-in chat UI once a session exists; otherwise a login
 * screen. Only ever mounted under the SessionProvider AuthGate adds when
 * AUTH_ENABLED is on. */
function Gated() {
  const { data: session, status } = useSession();

  if (status === "loading") {
    return <div className="flex items-center justify-center h-dvh" />;
  }
  if (!session) {
    return <LoginScreen />;
  }
  return <Chat apiToken={session.apiToken} onLogout={() => signOut()} />;
}

/** Top-of-tree gate for the whole app: when AUTH_ENABLED is off (the
 * default), this is a pure passthrough to <Chat /> -- no SessionProvider, no
 * useSession call, no next-auth/react code executes at all, so there is zero
 * behavior change versus the pre-auth app. When on, it wraps everything in a
 * SessionProvider and shows a login screen until the visitor is signed in. */
export default function AuthGate() {
  if (!AUTH_ENABLED) {
    return <Chat />;
  }
  return (
    <SessionProvider>
      <Gated />
    </SessionProvider>
  );
}
