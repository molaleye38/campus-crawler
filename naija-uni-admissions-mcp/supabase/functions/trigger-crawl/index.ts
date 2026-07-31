// Supabase Edge Function: trigger-crawl
// Receives a request from campuscompassapp.com admin UI, validates API key,
// then triggers the GitHub Actions workflow via repository_dispatch event.

import { serve } from "https://deno.land/std@0.168.0/http/server.ts";

const CRAWL_API_KEY = Deno.env.get("CRAWL_API_KEY")!;
const GITHUB_PAT = Deno.env.get("GITHUB_PAT")!;
const REPO = Deno.env.get("GITHUB_REPO") || "molaleye38/campus-crawler";

const corsHeaders = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type, x-api-key",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
};

serve(async (req) => {
  if (req.method === "OPTIONS") {
    return new Response(null, { status: 204, headers: corsHeaders });
  }

  if (req.method !== "POST") {
    return new Response(JSON.stringify({ error: "Method not allowed" }), {
      status: 405,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }

  const apiKey = req.headers.get("x-api-key");
  if (!apiKey || apiKey !== CRAWL_API_KEY) {
    return new Response(JSON.stringify({ error: "Invalid API key" }), {
      status: 401,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    });
  }

  let body: { max?: number; types?: string; state?: string } = {};
  try {
    body = await req.json();
  } catch {
    body = {};
  }

  const client_payload = {
    max_institutions: String(body.max ?? 50),
    institution_types: body.types ?? "university,polytechnic,college_of_education",
    state: body.state ?? "",
  };

  const resp = await fetch(`https://api.github.com/repos/${REPO}/dispatches`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${GITHUB_PAT}`,
      Accept: "application/vnd.github+json",
      "Content-Type": "application/json",
      "User-Agent": "supabase-edge-function",
    },
    body: JSON.stringify({
      event_type: "run-crawl",
      client_payload,
    }),
  });

  return new Response(
    JSON.stringify({
      triggered: resp.ok,
      github_status: resp.status,
      payload: client_payload,
      run_url: `https://github.com/${REPO}/actions/workflows/crawl.yml`,
    }),
    {
      status: resp.ok ? 202 : 500,
      headers: { ...corsHeaders, "Content-Type": "application/json" },
    }
  );
});
