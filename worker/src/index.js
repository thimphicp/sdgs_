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
      return proxyRequest(request, env, "/health");
    }

    if (url.pathname === "/analyze" && request.method === "POST") {
      return proxyRequest(request, env, "/analyze");
    }

    if (url.pathname === "/ask" && request.method === "POST") {
      return proxyRequest(request, env, "/ask");
    }

    return jsonResponse({ error: "Not found" }, 404);
  },
};

async function proxyRequest(request, env, pathname) {
  if (!env.AI_SERVER_URL) {
    return jsonResponse(
      { error: "AI_SERVER_URL is not configured in Worker environment." },
      500,
    );
  }

  const targetUrl = `${env.AI_SERVER_URL.replace(/\/$/, "")}${pathname}`;
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
