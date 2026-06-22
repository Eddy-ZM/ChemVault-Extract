import { defineCloudflareConfig } from "@opennextjs/cloudflare";

export default defineCloudflareConfig({
  // R2 incremental cache can be added later when ISR/image-cache needs are clear.
});
