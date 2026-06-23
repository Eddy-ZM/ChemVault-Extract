export interface Env {
  BACKEND_API_URL: string;
  INTERNAL_WORKER_TOKEN: string;
}

type QueueMessageBody = string | { delivery_id?: string; deliveryId?: string };

type PreparedAttempt = {
  url: string;
  body: string;
  headers: Record<string, string>;
  timeoutSeconds?: number;
  timeout_seconds?: number;
};

type AttemptResult = {
  status: string;
  retryDelaySeconds?: number;
  retry_delay_seconds?: number;
};

export default {
  async queue(batch: MessageBatch<QueueMessageBody>, env: Env): Promise<void> {
    for (const message of batch.messages) {
      await processMessage(message, env);
    }
  },
};

async function processMessage(message: Message<QueueMessageBody>, env: Env): Promise<void> {
  const deliveryId = deliveryIdFromMessage(message.body);
  if (!deliveryId) {
    message.ack();
    return;
  }

  try {
    const attempt = await prepareAttempt(env, deliveryId);
    const response = await postWebhook(attempt);
    const responsePreview = await safeResponsePreview(response);
    const result = await completeAttempt(env, deliveryId, {
      responseStatusCode: response.status,
      responseBodyPreview: responsePreview,
    });
    finishMessage(message, result);
  } catch (error) {
    if (error instanceof NonRetryableDeliveryError) {
      message.ack();
      return;
    }
    const result = await completeAttempt(env, deliveryId, {
      responseStatusCode: null,
      error: error instanceof Error ? error.message : "Webhook delivery failed.",
    });
    finishMessage(message, result);
  }
}

function deliveryIdFromMessage(body: QueueMessageBody): string | null {
  if (typeof body === "string") return body;
  return body.delivery_id ?? body.deliveryId ?? null;
}

async function prepareAttempt(env: Env, deliveryId: string): Promise<PreparedAttempt> {
  const response = await fetch(`${env.BACKEND_API_URL}/internal/webhook-deliveries/${deliveryId}/attempt`, {
    method: "POST",
    headers: internalHeaders(env),
  });
  if (response.status === 409 || response.status === 404) {
    throw new NonRetryableDeliveryError(`Delivery ${deliveryId} is not deliverable.`);
  }
  if (!response.ok) throw new Error(`Failed to prepare delivery ${deliveryId}: ${response.status}`);
  return (await response.json()) as PreparedAttempt;
}

async function postWebhook(attempt: PreparedAttempt): Promise<Response> {
  const controller = new AbortController();
  const timeoutSeconds = attempt.timeoutSeconds ?? attempt.timeout_seconds ?? 10;
  const timeout = setTimeout(() => controller.abort(), timeoutSeconds * 1000);
  try {
    return await fetch(attempt.url, {
      method: "POST",
      headers: attempt.headers,
      body: attempt.body,
      signal: controller.signal,
    });
  } finally {
    clearTimeout(timeout);
  }
}

async function completeAttempt(
  env: Env,
  deliveryId: string,
  payload: { responseStatusCode: number | null; responseBodyPreview?: string; error?: string },
): Promise<AttemptResult> {
  const response = await fetch(`${env.BACKEND_API_URL}/internal/webhook-deliveries/${deliveryId}/result`, {
    method: "POST",
    headers: { ...internalHeaders(env), "content-type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) throw new Error(`Failed to complete delivery ${deliveryId}: ${response.status}`);
  return (await response.json()) as AttemptResult;
}

function finishMessage(message: Message<QueueMessageBody>, result: AttemptResult): void {
  if (result.status === "queued") {
    message.retry({ delaySeconds: result.retryDelaySeconds ?? result.retry_delay_seconds ?? 60 });
    return;
  }
  message.ack();
}

async function safeResponsePreview(response: Response): Promise<string> {
  try {
    return (await response.text()).slice(0, 2000);
  } catch {
    return "";
  }
}

function internalHeaders(env: Env): Record<string, string> {
  return { authorization: `Bearer ${env.INTERNAL_WORKER_TOKEN}` };
}

class NonRetryableDeliveryError extends Error {}
