"use client";

import { FormEvent, useState } from "react";
import type { ContactMessage } from "@chemvault-extract/schemas";
import { Loader2, Send } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function ContactForm() {
  const [result, setResult] = useState<ContactMessage | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const formData = new FormData(event.currentTarget);
    const payload = {
      name: String(formData.get("name") ?? ""),
      email: String(formData.get("email") ?? ""),
      role: String(formData.get("role") ?? ""),
      organization: String(formData.get("organization") ?? ""),
      message: String(formData.get("message") ?? ""),
    };
    setIsSubmitting(true);
    setError(null);
    setResult(null);
    try {
      const response = await fetch("/api/contact", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(payload),
      });
      const body = await response.json();
      if (!response.ok) throw new Error(body.detail ?? "Unable to send message");
      setResult(body as ContactMessage);
      event.currentTarget.reset();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to send message");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr]">
      <Card className="shadow-none">
        <CardHeader>
          <CardTitle>Contact the ChemVault team</CardTitle>
          <CardDescription>Messages are saved in the application database. Email sending is not enabled yet.</CardDescription>
        </CardHeader>
        <CardContent>
          <form className="grid gap-4" onSubmit={onSubmit}>
            <div className="grid gap-2">
              <Label htmlFor="name">Name</Label>
              <Input id="name" name="name" required disabled={isSubmitting} />
            </div>
            <div className="grid gap-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" name="email" type="email" required disabled={isSubmitting} />
            </div>
            <div className="grid gap-2 sm:grid-cols-2">
              <div className="grid gap-2">
                <Label htmlFor="role">Role</Label>
                <Input id="role" name="role" placeholder="Researcher, PI, student..." disabled={isSubmitting} />
              </div>
              <div className="grid gap-2">
                <Label htmlFor="organization">Institution / company</Label>
                <Input id="organization" name="organization" disabled={isSubmitting} />
              </div>
            </div>
            <div className="grid gap-2">
              <Label htmlFor="message">Message</Label>
              <textarea
                id="message"
                name="message"
                required
                disabled={isSubmitting}
                className="min-h-36 rounded-md border border-input bg-background px-3 py-2 text-sm"
              />
            </div>
            <Button type="submit" className="w-fit" disabled={isSubmitting}>
              {isSubmitting ? <Loader2 data-icon="inline-start" className="animate-spin" /> : <Send data-icon="inline-start" />}
              {isSubmitting ? "Sending" : "Send message"}
            </Button>
          </form>
        </CardContent>
      </Card>

      <div className="grid gap-4">
        {result ? (
          <Alert>
            <AlertTitle>Message saved</AlertTitle>
            <AlertDescription>Thanks, {result.name}. Your message was saved for follow-up.</AlertDescription>
          </Alert>
        ) : null}
        {error ? (
          <Alert variant="destructive">
            <AlertTitle>Message not saved</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        ) : null}
        <Card className="shadow-none">
          <CardHeader>
            <CardTitle>Good fits for a conversation</CardTitle>
            <CardDescription>Research groups evaluating literature extraction, lab report digitisation, or shared scientific databases.</CardDescription>
          </CardHeader>
          <CardContent className="grid gap-3 text-sm text-muted-foreground">
            <p>Tell us what documents you want to process, expected monthly volume, and what export formats matter.</p>
            <p>Do not include confidential API keys, payment details, or sensitive personal data in this form.</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
