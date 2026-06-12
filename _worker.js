const AI_SERVER_URL = "https://bd9d-123-141-94-188.ngrok-free.app";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, ngrok-skip-browser-warning",
};

export default {
  async fetch(request, env) {
    if (request.method === "OPTIONS") {
      return new Response(null, { headers: corsHeaders });
    }

    const url = new URL(request.url);

    if (url.pathname === "/health" && request.method === "GET") {
      return proxyRequest(request, "/health");
    }

    if (url.pathname === "/analyze" && request.method === "POST") {
      return proxyRequest(request, "/analyze");
    }

    if (url.pathname === "/ask" && request.method === "POST") {
      return proxyRequest(request, "/ask");
    }

    if (env.ASSETS) {
      return env.ASSETS.fetch(request);
    }

    return jsonResponse({ error: "Static assets binding is not available." }, 500);
  },
};

async function proxyRequest(request, pathname) {
  const targetUrl = `${AI_SERVER_URL.replace(/\/$/, "")}${pathname}`;
  const headers = new Headers(request.headers);
  headers.delete("host");
  headers.set("ngrok-skip-browser-warning", "true");

  const response = await fetch(targetUrl, {
    method: request.method,
    headers,
    body: request.method === "GET" ? undefined : request.body,
  });

  const responseHeaders = new Headers(response.headers);
  for (const [key, value] of Object.entries(corsHeaders)) {
    responseHeaders.set(key, value);
  }

  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers: responseHeaders,
  });
}

function jsonResponse(data, status) {
  return Response.json(data, {
    status,
    headers: corsHeaders,
  });
}
