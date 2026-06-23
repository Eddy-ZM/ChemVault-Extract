"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import Script from "next/script";
import { LogIn, UserPlus } from "lucide-react";
import type { AuthTokenResponse } from "@chemvault-extract/schemas";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { storeAuthSession } from "@/lib/auth-client";

type AuthMode = "login" | "register";
type TurnstileApi = {
  render: (
    container: HTMLElement | string,
    options: {
      sitekey: string;
      callback?: (token: string) => void;
      "expired-callback"?: () => void;
      "error-callback"?: () => void;
    },
  ) => string;
  reset: (widgetId?: string) => void;
  remove?: (widgetId: string) => void;
};

declare global {
  interface Window {
    turnstile?: TurnstileApi;
  }
}

const TURNSTILE_SITE_KEY =
  process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY ?? process.env.NEXT_PUBLIC_CLOUDFLARE_TURNSTILE_SITE_KEY ?? "";

export function AuthForm({ mode }: { mode: AuthMode }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [turnstileReady, setTurnstileReady] = useState(false);
  const [turnstileToken, setTurnstileToken] = useState<string | null>(null);
  const [turnstileError, setTurnstileError] = useState<string | null>(null);
  const turnstileRef = useRef<HTMLDivElement | null>(null);
  const turnstileWidgetId = useRef<string | null>(null);
  const isRegister = mode === "register";
  const requiresTurnstile = isRegister && Boolean(TURNSTILE_SITE_KEY);

  useEffect(() => {
    if (!requiresTurnstile || !turnstileReady || !turnstileRef.current || turnstileWidgetId.current) {
      return;
    }
    if (!window.turnstile) {
      setTurnstileError("Cloudflare Turnstile is not available yet.");
      return;
    }

    turnstileWidgetId.current = window.turnstile.render(turnstileRef.current, {
      sitekey: TURNSTILE_SITE_KEY,
      callback: (token) => {
        setTurnstileToken(token);
        setTurnstileError(null);
      },
      "expired-callback": () => {
        setTurnstileToken(null);
        setTurnstileError("Human verification expired. Please complete it again.");
      },
      "error-callback": () => {
        setTurnstileToken(null);
        setTurnstileError("Cloudflare Turnstile failed to load. Please retry.");
      },
    });

    return () => {
      if (turnstileWidgetId.current && window.turnstile?.remove) {
        window.turnstile.remove(turnstileWidgetId.current);
      }
      turnstileWidgetId.current = null;
    };
  }, [requiresTurnstile, turnstileReady]);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const password = String(formData.get("password") ?? "");
    const confirmPassword = String(formData.get("confirmPassword") ?? "");
    if (isRegister && password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    if (requiresTurnstile && !turnstileToken) {
      setError("Complete the Cloudflare human verification before registering.");
      return;
    }
    const payload =
      mode === "register"
        ? {
            name: String(formData.get("name") ?? ""),
            email: String(formData.get("email") ?? ""),
            password,
            turnstileToken,
          }
        : {
            email: String(formData.get("email") ?? ""),
            password,
          };
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/auth/${mode}`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(payload),
      });
      const body = (await response.json()) as AuthTokenResponse | { detail?: string };
      if (!response.ok) {
        throw new Error(("detail" in body ? body.detail : null) ?? "Authentication failed");
      }
      if ("accessToken" in body && typeof body.accessToken === "string") {
        storeAuthSession({ accessToken: body.accessToken, user: body.user });
      }
      router.push(searchParams.get("next") || "/dashboard");
      router.refresh();
    } catch (err) {
      resetTurnstile();
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setLoading(false);
    }
  }

  function resetTurnstile() {
    setTurnstileToken(null);
    if (turnstileWidgetId.current && window.turnstile) {
      window.turnstile.reset(turnstileWidgetId.current);
    }
  }

  return (
    <div className="mx-auto flex min-h-[calc(100vh-8rem)] w-full max-w-md items-center">
      {requiresTurnstile ? (
        <Script
          src="https://challenges.cloudflare.com/turnstile/v0/api.js?render=explicit"
          strategy="afterInteractive"
          onLoad={() => setTurnstileReady(true)}
          onError={() => setTurnstileError("Cloudflare Turnstile could not load.")}
        />
      ) : null}
      <Card className="w-full">
        <CardHeader>
          <CardTitle>{isRegister ? "Create account" : "Log in"}</CardTitle>
          <CardDescription>
            {isRegister ? "Start a private ChemVault Extract workspace." : "Access your ChemVault Extract workspace."}
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {error ? (
            <Alert variant="destructive">
              <AlertTitle>{isRegister ? "Registration failed" : "Login failed"}</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          ) : null}
          <form className="flex flex-col gap-4" onSubmit={onSubmit}>
            {isRegister ? (
              <div className="flex flex-col gap-2">
                <Label htmlFor="name">Name</Label>
                <Input id="name" name="name" autoComplete="name" />
              </div>
            ) : null}
            <div className="flex flex-col gap-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" name="email" type="email" autoComplete="email" required />
            </div>
            <div className="flex flex-col gap-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                name="password"
                type="password"
                autoComplete={isRegister ? "new-password" : "current-password"}
                minLength={isRegister ? 8 : undefined}
                required
              />
            </div>
            {isRegister ? (
              <div className="flex flex-col gap-2">
                <Label htmlFor="confirmPassword">Confirm password</Label>
                <Input
                  id="confirmPassword"
                  name="confirmPassword"
                  type="password"
                  autoComplete="new-password"
                  minLength={8}
                  required
                />
              </div>
            ) : null}
            {requiresTurnstile ? (
              <div className="flex flex-col gap-2">
                <Label>Human verification</Label>
                <div
                  ref={turnstileRef}
                  className="min-h-[68px] overflow-hidden rounded-md border bg-white px-2 py-2"
                />
                <p className={turnstileError ? "text-xs text-destructive" : "text-xs text-muted-foreground"}>
                  {turnstileError ?? "Protected by Cloudflare Turnstile."}
                </p>
              </div>
            ) : null}
            <Button type="submit" disabled={loading}>
              {isRegister ? <UserPlus data-icon="inline-start" /> : <LogIn data-icon="inline-start" />}
              {loading ? "Working" : isRegister ? "Create account" : "Log in"}
            </Button>
          </form>
          <div className="text-sm text-muted-foreground">
            {isRegister ? (
              <Link className="underline-offset-4 hover:underline" href="/login">
                Already have an account? Log in
              </Link>
            ) : (
              <Link className="underline-offset-4 hover:underline" href="/register">
                Need an account? Register
              </Link>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
