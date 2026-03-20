import type { Config, Context } from "@netlify/functions";
import { getStore } from "@netlify/blobs";

// Serves cached news from Blobs — falls back to live fetch if cache miss
export default async (req: Request, context: Context) => {
  const store = getStore("nyspotlight-news");

  let payload: any = null;

  // Try cache first
  try {
    payload = await store.get("latest-news", { type: "json" });
  } catch (e) {
    console.log("Cache miss, fetching live...");
  }

  // Cache miss — fetch live from free sources (no key needed)
  if (!payload || !payload.articles?.length) {
    payload = await fetchLiveNews();
    // Store for next time
    try { await store.setJSON("latest-news", payload); } catch {}
  }

  // Add cache age header
  const fetchedAt = payload.fetchedAt ? new Date(payload.fetchedAt) : new Date();
  const ageSeconds = Math.floor((Date.now() - fetchedAt.getTime()) / 1000);

  return new Response(JSON.stringify(payload), {
    headers: {
      "Content-Type": "application/json",
      "Cache-Control": "public, max-age=300, stale-while-revalidate=3600",
      "X-Cache-Age": String(ageSeconds),
      "X-Articles-Count": String(payload.articles?.length || 0),
    }
  });
};

async function fetchLiveNews() {
  const GUARDIAN_KEY = Netlify.env.get("GUARDIAN_API_KEY") || "test";
  const NEWSAPI_KEY = Netlify.env.get("NEWSAPI_KEY") || "";

  const allArticles: any[] = [];
  const sections: Record<string, any[]> = {};

  // Guardian API (free with test key — works server-side)
  const guardianQueries = [
    { section: "broadway", tag: "stage/theatre", q: "new+york" },
    { section: "film",     tag: "film/film",     q: "new+york" },
    { section: "music",    tag: "music/music",   q: "" },
    { section: "fashion",  tag: "fashion/fashion", q: "" },
  ];

  for (const { section, tag } of guardianQueries) {
    try {
      const url = `https://content.guardianapis.com/search?tag=${tag}&order-by=newest&page-size=5&show-fields=headline,trailText,thumbnail&api-key=${GUARDIAN_KEY}`;
      const r = await fetch(url, { signal: AbortSignal.timeout(6000) });
      if (r.ok) {
        const data = await r.json() as any;
        const arts = (data.response?.results || []).slice(0, 4).map((a: any) => ({
          title: a.fields?.headline || a.webTitle,
          deck: a.fields?.trailText || "",
          url: a.webUrl,
          img: a.fields?.thumbnail || "",
          source: "The Guardian",
          date: a.webPublicationDate,
          section,
          kicker: getSectionKicker(section),
        }));
        sections[section] = arts;
        allArticles.push(...arts);
      }
    } catch {}
    await new Promise(r => setTimeout(r, 100));
  }

  // NewsAPI fallback
  if (NEWSAPI_KEY && allArticles.length < 8) {
    const queries = ["Broadway theater New York", "New York entertainment film", "fashion New York style"];
    for (const q of queries) {
      try {
        const url = `https://newsapi.org/v2/everything?q=${encodeURIComponent(q)}&language=en&sortBy=publishedAt&pageSize=3&apiKey=${NEWSAPI_KEY}`;
        const r = await fetch(url, { signal: AbortSignal.timeout(6000) });
        if (r.ok) {
          const data = await r.json() as any;
          const arts = (data.articles || [])
            .filter((a: any) => a.title && a.title !== "[Removed]")
            .slice(0, 3)
            .map((a: any) => ({
              title: a.title,
              deck: a.description || "",
              url: a.url,
              img: a.urlToImage || "",
              source: a.source?.name || "News",
              date: a.publishedAt,
              section: "nyc",
              kicker: "NYC News",
            }));
          allArticles.push(...arts);
        }
      } catch {}
      await new Promise(r => setTimeout(r, 150));
    }
  }

  return {
    articles: allArticles,
    sections,
    fetchedAt: new Date().toISOString(),
    count: allArticles.length,
    live: true,
  };
}

function getSectionKicker(section: string): string {
  const kickers: Record<string, string> = {
    broadway: "Broadway Coverage",
    film: "Film Review",
    music: "Music Coverage",
    fashion: "NYC Fashion",
    tv: "Television",
    premiere: "NYC Premiere",
    nyc: "NYC Arts",
    awards: "Awards Season",
  };
  return kickers[section] || "Coverage";
}

export const config: Config = {
  path: "/api/news"
};
