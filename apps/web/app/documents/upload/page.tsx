import { UploadForm } from "@/app/documents/upload/upload-form";

export default function UploadPage() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-2">
        <h1 className="text-2xl font-semibold tracking-normal">Upload</h1>
        <p className="text-sm text-muted-foreground">Create a document record and queue the first extraction job.</p>
      </div>
      <UploadForm />
    </div>
  );
}
