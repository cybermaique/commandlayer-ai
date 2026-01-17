"use client";

import { useEffect, useMemo, useState } from "react";

type AuthMode = "off" | "api_key";

type CommandMode = "natural" | "direct";

type CommandLog = {
  id: string;
  raw_text: string;
  status: string;
  created_at: string;
  api_key_id?: string | null;
  api_key_name?: string | null;
  role?: string | null;
  intent_json: Record<string, unknown>;
};

type HealthStatus = {
  status: string;
};

type ApiError = {
  error_code?: string;
  message?: string;
  missing_fields?: string[];
  details?: string[];
};

const DEFAULT_BASE_URL =
  process.env.NEXT_PUBLIC_DEFAULT_BASE_URL ?? "http://localhost:8000";

const STORAGE_KEYS = {
  baseUrl: "commandlayer_base_url",
  authMode: "commandlayer_auth_mode",
  headerName: "commandlayer_header_name",
  sessionApiKey: "commandlayer_api_key",
};

const ACTIONS = [{ value: "assign_task", label: "assign_task" }];

function safeJsonParse(
  value: string
): { ok: true; data: unknown } | { ok: false; error: string } {
  if (!value.trim()) {
    return { ok: true, data: undefined };
  }
  try {
    const parsed = JSON.parse(value) as unknown;
    if (typeof parsed === "object" && parsed !== null) {
      return { ok: true, data: parsed };
    }
    return { ok: false, error: "Payload must be a JSON object" };
  } catch (error) {
    return {
      ok: false,
      error: error instanceof Error ? error.message : "Invalid JSON",
    };
  }
}

function formatLatency(duration: number | null) {
  if (duration === null) return "--";
  return `${duration.toFixed(0)} ms`;
}

function toPrettyJson(value: unknown) {
  if (value === undefined) return "";
  return JSON.stringify(value, null, 2);
}

function normalizeError(status: number, data: unknown): ApiError {
  if (typeof data === "object" && data !== null) {
    const record = data as Record<string, unknown>;
    if (status === 422 && Array.isArray(record.detail)) {
      const details = record.detail
        .map((item) => {
          if (typeof item !== "object" || item === null) return "";
          const entry = item as Record<string, unknown>;
          const location = Array.isArray(entry.loc)
            ? entry.loc.join(".")
            : "field";
          const message =
            typeof entry.msg === "string" ? entry.msg : "Invalid value";
          return `${location}: ${message}`;
        })
        .filter((item) => item.length > 0);
      return {
        error_code: "validation_error",
        message: "Schema validation failed.",
        details,
      };
    }

    const error_code =
      typeof record.error_code === "string" ? record.error_code : undefined;
    const message =
      typeof record.message === "string" ? record.message : undefined;
    const missing_fields = Array.isArray(record.missing_fields)
      ? (record.missing_fields as string[])
      : undefined;
    return { error_code, message, missing_fields };
  }

  return { error_code: "error", message: "Unexpected error response." };
}

export default function Home() {
  const [baseUrl, setBaseUrl] = useState(DEFAULT_BASE_URL);
  const [authMode, setAuthMode] = useState<AuthMode>("off");
  const [headerName, setHeaderName] = useState("X-API-Key");
  const [apiKey, setApiKey] = useState("");
  const [rememberSession, setRememberSession] = useState(false);
  const [testStatus, setTestStatus] = useState<
    "idle" | "loading" | "success" | "error"
  >("idle");
  const [testMessage, setTestMessage] = useState<string>("");

  const [requestedBy, setRequestedBy] = useState("web-console");
  const [commandMode, setCommandMode] = useState<CommandMode>("natural");
  const [rawText, setRawText] = useState("");
  const [action, setAction] = useState(ACTIONS[0].value);
  const [payloadText, setPayloadText] = useState("{}");
  const [fallbackPayloadText, setFallbackPayloadText] = useState("{}");
  const [responseStatus, setResponseStatus] = useState<number | null>(null);
  const [responseLatency, setResponseLatency] = useState<number | null>(null);
  const [responseJson, setResponseJson] = useState<unknown>(null);
  const [responseError, setResponseError] = useState<ApiError | null>(null);
  const [isExecuting, setIsExecuting] = useState(false);

  const [logs, setLogs] = useState<CommandLog[]>([]);
  const [logsStatus, setLogsStatus] = useState<"idle" | "loading" | "error">(
    "idle"
  );
  const [logsError, setLogsError] = useState<string>("");
  const [logsFilter, setLogsFilter] = useState("all");
  const [logsSearch, setLogsSearch] = useState("");
  const [selectedLog, setSelectedLog] = useState<CommandLog | null>(null);

  const [assets, setAssets] = useState<{ id: string; name: string }[]>([]);
  const [tasks, setTasks] = useState<{ id: string; title: string }[]>([]);

  useEffect(() => {
    if (typeof window === "undefined") return;

    const savedBaseUrl = window.localStorage.getItem(STORAGE_KEYS.baseUrl);
    const savedAuthMode = window.localStorage.getItem(STORAGE_KEYS.authMode);
    const savedHeaderName = window.localStorage.getItem(
      STORAGE_KEYS.headerName
    );
    const sessionApiKey = window.sessionStorage.getItem(
      STORAGE_KEYS.sessionApiKey
    );

    if (savedBaseUrl) setBaseUrl(savedBaseUrl);
    if (savedAuthMode === "off" || savedAuthMode === "api_key") {
      setAuthMode(savedAuthMode);
    }
    if (savedHeaderName) setHeaderName(savedHeaderName);

    if (sessionApiKey) {
      setApiKey(sessionApiKey);
      setRememberSession(true);
    }
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(STORAGE_KEYS.baseUrl, baseUrl);
  }, [baseUrl]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(STORAGE_KEYS.authMode, authMode);
  }, [authMode]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(STORAGE_KEYS.headerName, headerName);
  }, [headerName]);

  useEffect(() => {
    if (typeof window === "undefined") return;

    if (rememberSession && apiKey) {
      window.sessionStorage.setItem(STORAGE_KEYS.sessionApiKey, apiKey);
    } else {
      window.sessionStorage.removeItem(STORAGE_KEYS.sessionApiKey);
    }
  }, [apiKey, rememberSession]);

  const authHeaders = useMemo(() => {
    if (authMode !== "api_key" || !apiKey) return {};
    return { [headerName]: apiKey } as Record<string, string>;
  }, [authMode, apiKey, headerName]);

  const filteredLogs = useMemo(() => {
    return logs.filter((log) => {
      if (logsFilter !== "all" && log.status !== logsFilter) return false;
      if (!logsSearch.trim()) return true;
      const search = logsSearch.toLowerCase();
      const rawText = log.raw_text?.toLowerCase() ?? "";
      const actionValue =
        typeof log.intent_json?.action === "string"
          ? log.intent_json.action.toLowerCase()
          : "";
      return rawText.includes(search) || actionValue.includes(search);
    });
  }, [logs, logsFilter, logsSearch]);

  const parsedPayload = useMemo(
    () => safeJsonParse(payloadText),
    [payloadText]
  );
  const parsedFallbackPayload = useMemo(
    () => safeJsonParse(fallbackPayloadText),
    [fallbackPayloadText]
  );

  const buildRequestBody = () => {
    if (commandMode === "natural") {
      const body: Record<string, unknown> = {
        requested_by: requestedBy,
        raw_text: rawText,
      };
      if (
        parsedFallbackPayload.ok &&
        parsedFallbackPayload.data !== undefined
      ) {
        body.payload = parsedFallbackPayload.data;
      }
      return body;
    }

    const body: Record<string, unknown> = {
      requested_by: requestedBy,
      action,
    };
    if (parsedPayload.ok && parsedPayload.data !== undefined) {
      body.payload = parsedPayload.data;
    }
    return body;
  };

  const handleTestConnection = async () => {
    setTestStatus("loading");
    setTestMessage("");
    try {
      const response = await fetch(`${baseUrl}/health`, {
        headers: {
          "Content-Type": "application/json",
          ...authHeaders,
        },
      });
      const data = (await response.json()) as HealthStatus;
      if (!response.ok) {
        setTestStatus("error");
        setTestMessage(`Error ${response.status}`);
        return;
      }
      setTestStatus("success");
      setTestMessage(data.status ?? "ok");
    } catch (error) {
      setTestStatus("error");
      setTestMessage(
        error instanceof Error ? error.message : "Connection failed"
      );
    }
  };

  const handleExecute = async () => {
    if (commandMode === "natural" && !rawText.trim()) {
      setResponseError({
        error_code: "invalid_request",
        message: "raw_text is required.",
      });
      return;
    }

    if (commandMode === "direct" && !action) {
      setResponseError({
        error_code: "invalid_request",
        message: "action is required.",
      });
      return;
    }

    if (commandMode === "direct" && !parsedPayload.ok) {
      setResponseError({
        error_code: "invalid_payload",
        message: parsedPayload.error,
      });
      return;
    }

    if (commandMode === "natural" && !parsedFallbackPayload.ok) {
      setResponseError({
        error_code: "invalid_payload",
        message: parsedFallbackPayload.error,
      });
      return;
    }

    setIsExecuting(true);
    setResponseStatus(null);
    setResponseLatency(null);
    setResponseJson(null);
    setResponseError(null);

    const start = performance.now();
    try {
      const response = await fetch(`${baseUrl}/commands`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...authHeaders,
        },
        body: JSON.stringify(buildRequestBody()),
      });
      const duration = performance.now() - start;
      setResponseLatency(duration);
      setResponseStatus(response.status);

      const data = await response.json();
      if (!response.ok) {
        const normalizedError = normalizeError(response.status, data);
        setResponseError(normalizedError);
        setResponseJson(data);
      } else {
        setResponseJson(data);
      }
    } catch (error) {
      const duration = performance.now() - start;
      setResponseLatency(duration);
      setResponseStatus(0);
      setResponseError({
        error_code: "network_error",
        message: error instanceof Error ? error.message : "Network error",
      });
    } finally {
      setIsExecuting(false);
    }
  };

  const fetchLogs = async () => {
    setLogsStatus("loading");
    setLogsError("");
    try {
      const response = await fetch(
        `${baseUrl}/command-logs?limit=50&offset=0`,
        {
          headers: {
            "Content-Type": "application/json",
            ...authHeaders,
          },
        }
      );
      const data = (await response.json()) as CommandLog[];
      if (!response.ok) {
        const errorMessage =
          (data as unknown as ApiError)?.message ?? "Unable to load logs";
        setLogsStatus("error");
        setLogsError(errorMessage);
        return;
      }
      setLogs(data);
      setLogsStatus("idle");
    } catch (error) {
      setLogsStatus("error");
      setLogsError(
        error instanceof Error ? error.message : "Unable to load logs"
      );
    }
  };

  const fetchReferenceData = async () => {
    try {
      const [assetsResponse, tasksResponse] = await Promise.all([
        fetch(`${baseUrl}/assets`, { headers: authHeaders }),
        fetch(`${baseUrl}/tasks`, { headers: authHeaders }),
      ]);

      if (assetsResponse.ok) {
        const assetData = (await assetsResponse.json()) as {
          id: string;
          name: string;
        }[];
        setAssets(assetData);
      }

      if (tasksResponse.ok) {
        const taskData = (await tasksResponse.json()) as {
          id: string;
          title: string;
        }[];
        setTasks(taskData);
      }
    } catch {
      setAssets([]);
      setTasks([]);
    }
  };

  useEffect(() => {
    fetchLogs();
    fetchReferenceData();
  }, [baseUrl, authMode, apiKey, headerName]);

  const requestPreview = useMemo(
    () => toPrettyJson(buildRequestBody()),
    [
      requestedBy,
      rawText,
      action,
      payloadText,
      fallbackPayloadText,
      commandMode,
    ]
  );

  const handleCopy = async (text: string) => {
    if (!navigator.clipboard) return;
    await navigator.clipboard.writeText(text);
  };

  const setPayloadField = (field: string, value: string) => {
    const parsed = safeJsonParse(payloadText);
    if (!parsed.ok || typeof parsed.data !== "object" || parsed.data === null) {
      setPayloadText(JSON.stringify({ [field]: value }, null, 2));
      return;
    }
    const nextPayload = {
      ...(parsed.data as Record<string, unknown>),
      [field]: value,
    };
    setPayloadText(JSON.stringify(nextPayload, null, 2));
  };

  return (
    <div className="min-h-screen px-6 py-10">
      <div className="mx-auto flex max-w-6xl flex-col gap-6">
        <header className="flex flex-col gap-2">
          <h1 className="text-3xl font-semibold text-slate-100">
            Command Console
          </h1>
          <p className="text-sm text-slate-300">
            Execute allowlisted commands and review recent activity without
            leaving your browser.
          </p>
        </header>

        <section className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-100">Connection</h2>
            <button
              className="rounded-lg border border-slate-600 bg-white px-3 py-1 text-sm font-medium text-slate-900"
              onClick={handleTestConnection}
            >
              Test Connection
            </button>
          </div>

          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <div className="flex flex-col gap-2">
              <label htmlFor="base-url">Base URL</label>
              <input
                id="base-url"
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={baseUrl}
                onChange={(event) => setBaseUrl(event.target.value)}
              />
            </div>
            <div className="flex flex-col gap-2">
              <label htmlFor="auth-mode">Auth mode</label>
              <select
                id="auth-mode"
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={authMode}
                onChange={(event) =>
                  setAuthMode(event.target.value as AuthMode)
                }
              >
                <option value="off">Off</option>
                <option value="api_key">API Key</option>
              </select>
            </div>
            <div className="flex flex-col gap-2">
              <label htmlFor="header-name">Header name</label>
              <input
                id="header-name"
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={headerName}
                onChange={(event) => setHeaderName(event.target.value)}
              />
            </div>
            <div className="flex flex-col gap-2">
              <label htmlFor="api-key">API Key</label>
              <input
                id="api-key"
                type="password"
                placeholder={
                  authMode === "api_key" ? "Enter API key" : "Disabled"
                }
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={apiKey}
                onChange={(event) => setApiKey(event.target.value)}
                disabled={authMode !== "api_key"}
              />
              <label className="flex items-center gap-2 text-xs text-slate-300">
                <input
                  type="checkbox"
                  className="h-4 w-4"
                  checked={rememberSession}
                  onChange={(event) => setRememberSession(event.target.checked)}
                  disabled={authMode !== "api_key"}
                />
                Remember for session only (stored in sessionStorage)
              </label>
            </div>
          </div>
          <div className="mt-4 text-sm">
            {testStatus === "loading" && (
              <span className="text-slate-300">Testing...</span>
            )}
            {testStatus === "success" && (
              <span className="text-emerald-300">Connected: {testMessage}</span>
            )}
            {testStatus === "error" && (
              <span className="text-rose-300">
                Connection failed: {testMessage}
              </span>
            )}
          </div>
        </section>

        <section className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-slate-100">Command</h2>
            <button
              className="rounded-lg border border-slate-600 bg-white px-3 py-1 text-sm font-medium text-slate-900 disabled:opacity-60"
              onClick={handleExecute}
              disabled={isExecuting}
            >
              {isExecuting ? "Running..." : "Execute"}
            </button>
          </div>

          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <div className="flex flex-col gap-2">
              <label htmlFor="requested-by">requested_by</label>
              <input
                id="requested-by"
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={requestedBy}
                onChange={(event) => setRequestedBy(event.target.value)}
              />
            </div>
            <div className="flex flex-col gap-2">
              <label htmlFor="command-mode">Mode</label>
              <select
                id="command-mode"
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={commandMode}
                onChange={(event) =>
                  setCommandMode(event.target.value as CommandMode)
                }
              >
                <option value="natural">Natural language</option>
                <option value="direct">Direct action</option>
              </select>
            </div>
          </div>

          {commandMode === "natural" ? (
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <div className="flex flex-col gap-2">
                <label htmlFor="raw-text">raw_text</label>
                <textarea
                  id="raw-text"
                  className="min-h-[120px] rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  value={rawText}
                  onChange={(event) => setRawText(event.target.value)}
                />
              </div>
              <div className="flex flex-col gap-2">
                <label htmlFor="fallback-payload">
                  Fallback payload (optional JSON)
                </label>
                <textarea
                  id="fallback-payload"
                  className="min-h-[120px] rounded-lg border border-slate-300 px-3 py-2 font-mono text-xs"
                  value={fallbackPayloadText}
                  onChange={(event) =>
                    setFallbackPayloadText(event.target.value)
                  }
                />
                {!parsedFallbackPayload.ok && (
                  <span className="text-xs text-rose-300">
                    {parsedFallbackPayload.error}
                  </span>
                )}
              </div>
            </div>
          ) : (
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <div className="flex flex-col gap-2">
                <label htmlFor="action">Action</label>
                <select
                  id="action"
                  className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
                  value={action}
                  onChange={(event) => setAction(event.target.value)}
                >
                  {ACTIONS.map((option) => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
                {action === "assign_task" && (
                  <div className="mt-2 grid gap-2">
                    <label className="text-xs text-slate-300">
                      Quick payload builder
                    </label>
                    <select
                      className="rounded-lg border border-slate-300 px-3 py-2 text-xs"
                      onChange={(event) =>
                        setPayloadField("asset_id", event.target.value)
                      }
                    >
                      <option value="">Select asset</option>
                      {assets.map((asset) => (
                        <option key={asset.id} value={asset.id}>
                          {asset.name}
                        </option>
                      ))}
                    </select>
                    <select
                      className="rounded-lg border border-slate-300 px-3 py-2 text-xs"
                      onChange={(event) =>
                        setPayloadField("task_id", event.target.value)
                      }
                    >
                      <option value="">Select task</option>
                      {tasks.map((task) => (
                        <option key={task.id} value={task.id}>
                          {task.title}
                        </option>
                      ))}
                    </select>
                  </div>
                )}
              </div>
              <div className="flex flex-col gap-2">
                <label htmlFor="payload">Payload JSON</label>
                <textarea
                  id="payload"
                  className="min-h-[160px] rounded-lg border border-slate-300 px-3 py-2 font-mono text-xs"
                  value={payloadText}
                  onChange={(event) => setPayloadText(event.target.value)}
                />
                {!parsedPayload.ok && (
                  <span className="text-xs text-rose-300">
                    {parsedPayload.error}
                  </span>
                )}
              </div>
            </div>
          )}

          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-slate-100">
                  Request preview
                </h3>
                <button
                  className="text-xs font-medium text-slate-200"
                  onClick={() => handleCopy(requestPreview)}
                >
                  Copy
                </button>
              </div>
              <pre className="mt-2 text-xs text-slate-200">
                {requestPreview}
              </pre>
            </div>
            <div className="rounded-xl border border-slate-800 bg-slate-950/60 p-4">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold text-slate-100">
                  Response
                </h3>
                <button
                  className="text-xs font-medium text-slate-200"
                  onClick={() => handleCopy(toPrettyJson(responseJson))}
                >
                  Copy
                </button>
              </div>
              <div className="mt-2 flex flex-wrap gap-2 text-xs text-slate-300">
                <span>Status: {responseStatus ?? "--"}</span>
                <span>Latency: {formatLatency(responseLatency)}</span>
              </div>
              {responseError && (
                <div className="mt-2 rounded-lg border border-rose-500/40 bg-rose-500/10 p-2 text-xs text-rose-200">
                  <div className="font-semibold">
                    {responseError.error_code ?? "error"}
                  </div>
                  <div>{responseError.message}</div>
                  {responseError.missing_fields && (
                    <div>
                      Missing: {responseError.missing_fields.join(", ")}
                    </div>
                  )}
                  {responseError.details &&
                    responseError.details.length > 0 && (
                      <ul className="mt-2 list-disc space-y-1 pl-4">
                        {responseError.details.map((detail, index) => (
                          <li key={index}>{detail}</li>
                        ))}
                      </ul>
                    )}
                </div>
              )}
              <pre className="mt-2 text-xs text-slate-200">
                {responseJson ? toPrettyJson(responseJson) : "No response yet."}
              </pre>
            </div>
          </div>
        </section>

        <section className="rounded-2xl border border-slate-800 bg-slate-900/40 p-6">
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div>
              <h2 className="text-lg font-semibold text-slate-100">
                Recent activity
              </h2>
              <p className="text-sm text-slate-300">
                Last 50 command executions
              </p>
            </div>
            <div className="flex flex-wrap gap-3">
              <select
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
                value={logsFilter}
                onChange={(event) => setLogsFilter(event.target.value)}
              >
                <option value="all">All statuses</option>
                <option value="success">Success</option>
                <option value="noop">No-op</option>
                <option value="error">Error</option>
              </select>
              <input
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm"
                placeholder="Search action or raw text"
                value={logsSearch}
                onChange={(event) => setLogsSearch(event.target.value)}
              />
              <button
                className="rounded-lg border border-slate-600 bg-white px-3 py-2 text-sm font-medium text-slate-900"
                onClick={fetchLogs}
              >
                Refresh
              </button>
            </div>
          </div>

          <div className="mt-4 overflow-hidden rounded-xl border border-slate-800">
            <table className="min-w-full divide-y divide-slate-800 text-sm">
              <thead className="bg-slate-950">
                <tr>
                  <th className="px-4 py-2 text-left font-semibold text-slate-200">
                    Created
                  </th>
                  <th className="px-4 py-2 text-left font-semibold text-slate-200">
                    Status
                  </th>
                  <th className="px-4 py-2 text-left font-semibold text-slate-200">
                    Action
                  </th>
                  <th className="px-4 py-2 text-left font-semibold text-slate-200">
                    API Key
                  </th>
                  <th className="px-4 py-2 text-left font-semibold text-slate-200">
                    Role
                  </th>
                  <th className="px-4 py-2 text-left font-semibold text-slate-200"></th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800 bg-slate-900/60">
                {logsStatus === "loading" && (
                  <tr>
                    <td colSpan={6} className="px-4 py-3 text-slate-300">
                      Loading logs...
                    </td>
                  </tr>
                )}
                {logsStatus === "error" && (
                  <tr>
                    <td colSpan={6} className="px-4 py-3 text-rose-300">
                      {logsError}
                    </td>
                  </tr>
                )}
                {logsStatus !== "loading" && filteredLogs.length === 0 && (
                  <tr>
                    <td colSpan={6} className="px-4 py-3 text-slate-300">
                      No logs match the filters.
                    </td>
                  </tr>
                )}
                {filteredLogs.map((log) => (
                  <tr key={log.id}>
                    <td className="px-4 py-3 text-slate-200">
                      {new Date(log.created_at).toLocaleString()}
                    </td>
                    <td className="px-4 py-3 text-slate-200">{log.status}</td>
                    <td className="px-4 py-3 text-slate-200">
                      {typeof log.intent_json?.action === "string"
                        ? log.intent_json.action
                        : log.raw_text}
                    </td>
                    <td className="px-4 py-3 text-slate-200">
                      {log.api_key_name ?? "--"}
                    </td>
                    <td className="px-4 py-3 text-slate-200">
                      {log.role ?? "--"}
                    </td>
                    <td className="px-4 py-3 text-right">
                      <button
                        className="text-xs font-semibold text-slate-200"
                        onClick={() => setSelectedLog(log)}
                      >
                        View
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </div>

      {selectedLog && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 px-6">
          <div className="max-h-[80vh] w-full max-w-2xl overflow-auto rounded-2xl border border-slate-700 bg-slate-900 p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-lg font-semibold text-slate-100">
                  Execution details
                </h3>
                <p className="text-xs text-slate-300">
                  Log ID: {selectedLog.id}
                </p>
              </div>
              <button
                className="text-sm font-semibold text-slate-200"
                onClick={() => setSelectedLog(null)}
              >
                Close
              </button>
            </div>
            <div className="mt-4 grid gap-4 text-sm text-slate-200">
              <div>
                <div className="text-xs text-slate-400">Status</div>
                <div>{selectedLog.status}</div>
              </div>
              <div>
                <div className="text-xs text-slate-400">API Key ID</div>
                <div>{selectedLog.api_key_id ?? "--"}</div>
              </div>
              <div>
                <div className="text-xs text-slate-400">Intent JSON</div>
                <pre className="mt-2 rounded-lg border border-slate-800 bg-slate-950/70 p-3 text-xs text-slate-200">
                  {toPrettyJson(selectedLog.intent_json)}
                </pre>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
