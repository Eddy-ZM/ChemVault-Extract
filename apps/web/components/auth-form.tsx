"use client";

import { useEffect, useMemo } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { ArrowRight, LogIn, UserPlus } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

type AuthMode = "login" | "register";

const USER_CENTER_URL = process.env.NEXT_PUBLIC_CHEMVAULT_USER_URL ?? "https://user.chemvault.science";

export function AuthForm({ mode }: { mode: AuthMode }) {
  const searchParams = useSearchParams();
  const isRegister = mode === "register";
  const targetUrl = useMemo(() => buildUserCenterUrl(mode, searchParams.get("next")), [mode, searchParams]);

  useEffect(() => {
    window.location.replace(targetUrl);
  }, [targetUrl]);

  return (
    <div className="mx-auto flex min-h-[calc(100vh-8rem)] w-full max-w-md items-center">
      <Card className="w-full">
        <CardHeader>
          <CardTitle>{isRegister ? "Create ChemVault account" : "Log in with ChemVault"}</CardTitle>
          <CardDescription>
            {isRegister
              ? "ChemVault Extract uses the unified ChemVault User Center for registration, profile, and security."
              : "Redirecting you to ChemVault User Center for secure sign-in."}
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <Button asChild>
            <Link href={targetUrl}>
              {isRegister ? <UserPlus data-icon="inline-start" /> : <LogIn data-icon="inline-start" />}
              Continue to User Center
              <ArrowRight data-icon="inline-end" />
            </Link>
          </Button>
          <p className="text-sm text-muted-foreground">
            After authentication, you will return to ChemVault Extract with a shared ChemVault session.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

function buildUserCenterUrl(mode: AuthMode, next: string | null): string {
  const base = USER_CENTER_URL.replace(/\/$/, "");
  const currentOrigin = typeof window === "undefined" ? "https://app.chemvault.science" : window.location.origin;
  const returnTo = new URL(next && next.startsWith("/") ? next : "/dashboard", currentOrigin).toString();
  const url = new URL(`/${mode}`, base);
  url.searchParams.set("returnTo", returnTo);
  return url.toString();
}
