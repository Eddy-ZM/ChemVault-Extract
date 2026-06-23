export class ChemVaultError extends Error {
  code?: string;
  statusCode?: number;
  details: Record<string, unknown>;
  requestId?: string | null;

  constructor(
    message: string,
    options: {
      code?: string;
      statusCode?: number;
      details?: Record<string, unknown>;
      requestId?: string | null;
    } = {},
  ) {
    super(message);
    this.name = "ChemVaultError";
    this.code = options.code;
    this.statusCode = options.statusCode;
    this.details = options.details ?? {};
    this.requestId = options.requestId;
  }
}
