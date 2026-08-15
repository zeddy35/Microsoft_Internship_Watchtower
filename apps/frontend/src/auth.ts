import NextAuth from "next-auth";
import MicrosoftEntraID from "next-auth/providers/microsoft-entra-id";

/**
 * Microsoft Entra ID sign-in.
 *
 * Auth is opt-in: with no Entra app registered the dashboard stays open, which
 * is what makes `npm run dev` work on a laptop with nothing but the API
 * running. Set the three AUTH_MICROSOFT_ENTRA_ID_* variables (documented in
 * README.md) and the same routes become protected without a code change.
 */
export const isAuthConfigured = Boolean(
  process.env.AUTH_MICROSOFT_ENTRA_ID_ID &&
    process.env.AUTH_MICROSOFT_ENTRA_ID_SECRET,
);

export const { handlers, auth, signIn, signOut } = NextAuth({
  providers: [
    MicrosoftEntraID({
      clientId: process.env.AUTH_MICROSOFT_ENTRA_ID_ID,
      clientSecret: process.env.AUTH_MICROSOFT_ENTRA_ID_SECRET,
      // Omitted, this defaults to /common/v2.0/ and lets any Microsoft account
      // in. Set it to your tenant to restrict sign-in to your directory.
      issuer: process.env.AUTH_MICROSOFT_ENTRA_ID_ISSUER,
    }),
  ],
  pages: {
    signIn: "/signin",
  },
  callbacks: {
    authorized: ({ auth: session }) => Boolean(session?.user),
  },
});
