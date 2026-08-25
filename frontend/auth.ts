/** NextAuth (Auth.js) config -- gated behind AUTH_ENABLED, off by default.
 *
 * When disabled, `providers` is an empty array and this module never
 * requires GOOGLE_CLIENT_ID/GOOGLE_CLIENT_SECRET/NEXTAUTH_SECRET to be set:
 * NextAuth() itself doesn't validate provider credentials at construction
 * time, only when an actual OAuth flow is attempted, so importing this file
 * (e.g. from the /api/auth/[...nextauth] route handler) is a safe no-op with
 * zero env vars present -- matching the "disabled must be a complete no-op"
 * requirement.
 *
 * When enabled, the `jwt`/`session` callbacks mint a small custom JWT
 * (email + short expiry) signed with NEXTAUTH_SECRET -- reused here as the
 * shared secret with the backend rather than introducing a separate
 * API_JWT_SECRET, to keep the env var count down (see .env.example) -- and
 * expose it to the client as `session.apiToken` so a client component can
 * read it via useSession() and attach `Authorization: Bearer <token>` to
 * backend requests.
 */
import NextAuth from "next-auth";
import Google from "next-auth/providers/google";
import jwt from "jsonwebtoken";

import { AUTH_ENABLED } from "@/lib/auth-config";

const API_JWT_SECRET = process.env.NEXTAUTH_SECRET ?? "";

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: AUTH_ENABLED
    ? [
        Google({
          clientId: process.env.GOOGLE_CLIENT_ID,
          clientSecret: process.env.GOOGLE_CLIENT_SECRET,
        }),
      ]
    : [],
  session: { strategy: "jwt" },
  callbacks: {
    async jwt({ token, user }) {
      if (user?.email) {
        token.email = user.email;
      }
      if (token.email) {
        token.apiToken = jwt.sign({ email: token.email }, API_JWT_SECRET, {
          expiresIn: "1h",
        });
      }
      return token;
    },
    async session({ session, token }) {
      if (typeof token.apiToken === "string") {
        session.apiToken = token.apiToken;
      }
      return session;
    },
  },
});
