"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { LogIn, UserPlus } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

type AuthMode = "login" | "register";

export function AuthForm({ mode }: { mode: AuthMode }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const payload =
      mode === "register"
        ? {
            name: String(formData.get("name") ?? ""),
            email: String(formData.get("email") ?? ""),
            password: String(formData.get("password") ?? ""),
          }
        : {
            email: String(formData.get("email") ?? ""),
            password: String(formData.get("password") ?? ""),
          };
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`/api/auth/${mode}`, {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(payload),
      });
      const body = await response.json();
      if (!response.ok) {
        throw new Error(body.detail ?? "Authentication failed");
      }
      if (typeof body.accessToken === "string") {
        window.localStorage.setItem("chemvault_token", body.accessToken);
      }
      router.push(searchParams.get("next") || "/dashboard");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setLoading(false);
    }
  }

  const isRegister = mode === "register";
  return (
    <div className="mx-auto flex min-h-[calc(100vh-8rem)] w-full max-w-md items-center">
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
