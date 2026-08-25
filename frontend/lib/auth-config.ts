/** Shared on/off switch for the gated Google OAuth feature.
 *
 * Read from `NEXT_PUBLIC_AUTH_ENABLED` so it's inlined identically into
 * server code (auth.ts, route handlers) and client code (AuthGate, Chat) --
 * Next.js statically replaces `NEXT_PUBLIC_`-prefixed env vars at build time
 * in both. Same truthy convention as the backend's AUTH_ENABLED: only
 * "true"/"1" (case-insensitive) count as enabled; unset, "false", "0", or
 * anything else is disabled (today's behavior, unauthenticated).
 */
function parseBool(value: string | undefined): boolean {
  return (value ?? "").trim().toLowerCase() === "true" || (value ?? "").trim() === "1";
}

export const AUTH_ENABLED = parseBool(process.env.NEXT_PUBLIC_AUTH_ENABLED);
