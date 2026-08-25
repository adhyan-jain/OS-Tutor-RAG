import type { DefaultSession } from "next-auth";

// Adds the custom-signed backend API JWT (see auth.ts's jwt/session
// callbacks) to NextAuth's Session and JWT types.
declare module "next-auth" {
  interface Session {
    apiToken?: string;
    user?: DefaultSession["user"];
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    apiToken?: string;
  }
}
