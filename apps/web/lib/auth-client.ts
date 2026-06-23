import type { User } from "@chemvault-extract/schemas";

const TOKEN_KEY = "chemvault_token";
const USER_KEY = "chemvault_user";

export function storeAuthSession({ accessToken, user }: { accessToken?: string | null; user?: User | null }) {
  if (!isBrowser()) return;
  if (accessToken) {
    window.localStorage.setItem(TOKEN_KEY, accessToken);
  }
  if (user) {
    storeUser(user);
  }
}

export function storeUser(user: User) {
  if (!isBrowser()) return;
  window.localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function readStoredUser(): User | null {
  if (!isBrowser()) return null;
  const raw = window.localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    const parsed = JSON.parse(raw) as Partial<User>;
    if (typeof parsed.id === "string" && typeof parsed.email === "string") {
      return parsed as User;
    }
  } catch {
    window.localStorage.removeItem(USER_KEY);
  }
  return null;
}

export function clearAuthSession() {
  if (!isBrowser()) return;
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(USER_KEY);
}

function isBrowser() {
  return typeof window !== "undefined";
}
