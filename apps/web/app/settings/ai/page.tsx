import { AiSettingsForm } from "@/components/ai-settings-form";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { getUserAiSettings } from "@/lib/api";

export default async function AiSettingsPage() {
  try {
    const settings = await getUserAiSettings();
    return (
      <div className="flex flex-col gap-6">
        <div className="flex flex-col gap-2">
          <h1 className="text-2xl font-semibold tracking-normal">AI settings</h1>
          <p className="text-sm text-muted-foreground">OpenAI model and API key configuration.</p>
        </div>
        <AiSettingsForm initialSettings={settings} />
      </div>
    );
  } catch (err) {
    return (
      <Alert variant="destructive">
        <AlertTitle>Settings unavailable</AlertTitle>
        <AlertDescription>{err instanceof Error ? err.message : "Unable to load AI settings"}</AlertDescription>
      </Alert>
    );
  }
}
