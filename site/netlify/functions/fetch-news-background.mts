import type { Config } from "@netlify/functions";
import { getStore } from "@netlify/blobs";

// Runs every hour — fetches real news, writes stories with Claude, stores in Blobs
export default async (req: Request) => {
  const NEWSAPI_KEY = Netlify.env.get("NEWSAPI_KEY") || "";
  const ANTHROPIC_KEY = Netlify.env.get("ANTHROPIC_API_KEY") || "";
  const GUARDIAN_KEY = Netlify.env.get("GUARDIAN_API_KEY") || "test";

  console.log("🔄 Fetching news...", new Date().toISOString());

  const store = getStore("nyspotlight-news");

  // ── FETCH FROM MULTIPLE SOURCES ──────────────────────────────────────────
  const sections: Record<string, any[]> = {
    broadway: [], film: [], music: [], fashion: [],
    premiere: [], tv: [], nyc: [], awards: []
  };

  const queries = [
    { section: "broadway", q: "Broadway theater New York musical play opening" },
    { section: "film",     q: "film premiere movie New York cinema review" },
    { section: "music",    q: "music concert New York Carnegie Hall album" },
    { section: "fashion",  q: "fashion NYFW New York designer style" },
    { section: "tv",       q: "television streaming series Emmy drama" },
    { section: "nyc",      q: "New York City entertainment arts culture" },
    { section: "awards",   q: "Oscar Grammy Tony Emmy awards season" },
  ];

  // NewsAPI fetch
  if (NEWSAPI_KEY) {
    for (const { section, q } of queries.slice(0, 5)) {
      try {
        const url = `https://newsapi.org/v2/everything?q=${encodeURIComponent(q)}&language=en&sortBy=publishedAt&pageSize=4&apiKey=${NEWSAPI_KEY}`;
        const r = await fetch(url, { signal: AbortSignal.timeout(8000) });
        if (r.ok) {
          const data = await r.json() as any;
          const articles = (data.articles || []).filter((a: any) =>
            a.title && a.title !== "[Removed]" && a.url && !a.url.includes("removed")
          ).slice(0, 4);
          sections[section].push(...articles.map((a: any) => ({
            title: a.title,
            deck: a.description || "",
            url: a.url,
            img: a.urlToImage || "",
            source: a.source?.name || "News",
            date: a.publishedAt,
            section,
          })));
        }
      } catch (e) {
        console.warn(`NewsAPI ${section} failed:`, e);
      }
      await new Promise(r => setTimeout(r, 200));
    }
  }

  // Guardian API (free with test key)
  const guardianQueries = [
    { section: "broadway", tag: "stage/theatre" },
    { section: "film",     tag: "film/film" },
    { section: "music",    tag: "music/music" },
    { section: "fashion",  tag: "fashion/fashion" },
  ];

  for (const { section, tag } of guardianQueries) {
    try {
      const url = `https://content.guardianapis.com/search?tag=${tag}&order-by=newest&page-size=4&show-fields=headline,trailText,thumbnail&api-key=${GUARDIAN_KEY}`;
      const r = await fetch(url, { signal: AbortSignal.timeout(8000) });
      if (r.ok) {
        const data = await r.json() as any;
        const results = (data.response?.results || []).slice(0, 4);
        sections[section].push(...results.map((a: any) => ({
          title: a.fields?.headline || a.webTitle,
          deck: a.fields?.trailText || "",
          url: a.webUrl,
          img: a.fields?.thumbnail || "",
          source: "The Guardian",
          date: a.webPublicationDate,
          section,
        })));
      }
    } catch (e) {
      console.warn(`Guardian ${section} failed:`, e);
    }
    await new Promise(r => setTimeout(r, 150));
  }

  // Alpha Vantage news sentiment for entertainment stocks
  const AV_KEY = Netlify.env.get("ALPHA_VANTAGE_API_KEY") || "";
  if (AV_KEY) {
    try {
      const url = `https://www.alphavantage.co/query?function=NEWS_SENTIMENT&topics=entertainment&limit=5&apikey=${AV_KEY}`;
      const r = await fetch(url, { signal: AbortSignal.timeout(8000) });
      if (r.ok) {
        const data = await r.json() as any;
        const feed = (data.feed || []).slice(0, 3);
        sections.nyc.push(...feed.map((a: any) => ({
          title: a.title,
          deck: a.summary?.substring(0, 200) || "",
          url: a.url,
          img: a.banner_image || "",
          source: a.source,
          date: a.time_published,
          section: "nyc",
        })));
      }
    } catch (e) {
      console.warn("Alpha Vantage news failed:", e);
    }
  }

  // ── ENHANCE WITH CLAUDE ───────────────────────────────────────────────────
  // Pick top 8 articles and write editorial summaries
  let allArticles: any[] = [];
  for (const [sec, arts] of Object.entries(sections)) {
    allArticles.push(...arts.slice(0, 2).map(a => ({ ...a, section: sec })));
  }
  allArticles = allArticles.filter(a => a.title && a.title.length > 10);

  if (ANTHROPIC_KEY && allArticles.length > 0) {
    try {
      const articleList = allArticles.slice(0, 10).map((a, i) =>
        `${i + 1}. [${a.section.toUpperCase()}] "${a.title}" — ${a.deck?.substring(0, 100) || "No description"}`
      ).join("\n");

      const body = JSON.stringify({
        model: "claude-haiku-4-5-20251001",
        max_tokens: 1000,
        messages: [{
          role: "user",
          content: `You are the editorial voice of NY Spotlight Report, a New York entertainment authority.

For each article below, write a SHORT (1-sentence) editorial kicker and a SHORT (2-sentence max) editorial deck in the style of S.C. Thomas — authoritative, direct, New York-centric.

Return ONLY a JSON array: [{"index":1,"kicker":"...","editorialDeck":"..."},...]

Articles:
${articleList}`
        }]
      });

      const claudeRes = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: {
          "x-api-key": ANTHROPIC_KEY,
          "anthropic-version": "2023-06-01",
          "Content-Type": "application/json"
        },
        body,
        signal: AbortSignal.timeout(20000)
      });

      if (claudeRes.ok) {
        const claudeData = await claudeRes.json() as any;
        const text = claudeData.content?.[0]?.text || "[]";
        const clean = text.replace(/```json|```/g, "").trim();
        const enhancements = JSON.parse(clean);
        if (Array.isArray(enhancements)) {
          enhancements.forEach(e => {
            if (allArticles[e.index - 1]) {
              allArticles[e.index - 1].kicker = e.kicker;
              allArticles[e.index - 1].editorialDeck = e.editorialDeck;
            }
          });
        }
      }
    } catch (e) {
      console.warn("Claude enhancement failed:", e);
    }
  }

  // ── STORE IN BLOBS ────────────────────────────────────────────────────────
  const payload = {
    articles: allArticles,
    sections,
    fetchedAt: new Date().toISOString(),
    count: allArticles.length,
  };

  await store.setJSON("latest-news", payload);
  await store.setJSON("latest-news-" + new Date().toISOString().split("T")[0], payload);

  console.log(`✅ Stored ${allArticles.length} articles`);
};

export const config: Config = {
  schedule: "@hourly"
};
