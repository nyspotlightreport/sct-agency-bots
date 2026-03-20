const { getStore } = require("@netlify/blobs");

// Serves cached news from Blobs — falls back to live fetch if cache miss
exports.handler = async (event, context) => {
  const store = getStore("nyspotlight-news");
  let payload = null;

  try {
    payload = await store.get("latest-news", { type: "json" });
  } catch (e) {}

  if (!payload || !payload.articles?.length) {
    payload = await fetchLiveNews();
    try { await store.setJSON("latest-news", payload); } catch {}
  }

  const fetchedAt = payload.fetchedAt ? new Date(payload.fetchedAt) : new Date();
  const ageSeconds = Math.floor((Date.now() - fetchedAt.getTime()) / 1000);

  return {
    statusCode: 200,
    headers: {
      "Content-Type": "application/json",
      "Cache-Control": "public, max-age=300",
      "X-Cache-Age": String(ageSeconds),
      "X-Articles-Count": String(payload.articles?.length || 0),
      "Access-Control-Allow-Origin": "*",
    },
    body: JSON.stringify(payload)
  };
};

async function fetchLiveNews() {
  const GUARDIAN_KEY = process.env.GUARDIAN_API_KEY || "test";
  const NEWSAPI_KEY  = process.env.NEWSAPI_KEY || "";
  const ANTHROPIC_KEY = process.env.ANTHROPIC_API_KEY || "";

  const allArticles = [];

  const guardianQueries = [
    { section: "broadway", tag: "stage/theatre" },
    { section: "film",     tag: "film/film"     },
    { section: "music",    tag: "music/music"   },
    { section: "fashion",  tag: "fashion/fashion"},
    { section: "tv",       tag: "tv-and-radio/tv-and-radio" },
  ];

  for (const { section, tag } of guardianQueries) {
    try {
      const url = `https://content.guardianapis.com/search?tag=${tag}&order-by=newest&page-size=5&show-fields=headline,trailText,thumbnail&api-key=${GUARDIAN_KEY}`;
      const r = await fetch(url, { signal: AbortSignal.timeout(6000) });
      if (r.ok) {
        const data = await r.json();
        const arts = (data.response?.results || []).slice(0, 4).map(a => ({
          title:   a.fields?.headline || a.webTitle,
          deck:    a.fields?.trailText || "",
          url:     a.webUrl,
          img:     a.fields?.thumbnail || "",
          source:  "The Guardian",
          date:    a.webPublicationDate,
          section,
          kicker:  getSectionKicker(section),
        }));
        allArticles.push(...arts);
      }
    } catch (e) {}
    await new Promise(r => setTimeout(r, 100));
  }

  // NewsAPI boost
  if (NEWSAPI_KEY && allArticles.length < 10) {
    const queries = [
      { q: "Broadway theater New York opening", section: "broadway" },
      { q: "New York City entertainment film premiere", section: "premiere" },
      { q: "fashion designer New York style", section: "fashion" },
    ];
    for (const { q, section } of queries) {
      try {
        const url = `https://newsapi.org/v2/everything?q=${encodeURIComponent(q)}&language=en&sortBy=publishedAt&pageSize=3&apiKey=${NEWSAPI_KEY}`;
        const r = await fetch(url, { signal: AbortSignal.timeout(6000) });
        if (r.ok) {
          const data = await r.json();
          const arts = (data.articles || [])
            .filter(a => a.title && a.title !== "[Removed]" && !a.url?.includes("removed"))
            .slice(0, 3)
            .map(a => ({
              title:  a.title,
              deck:   a.description || "",
              url:    a.url,
              img:    a.urlToImage || "",
              source: a.source?.name || "News",
              date:   a.publishedAt,
              section,
              kicker: getSectionKicker(section),
            }));
          allArticles.push(...arts);
        }
      } catch (e) {}
      await new Promise(r => setTimeout(r, 150));
    }
  }

  // Claude editorial enhancement
  if (ANTHROPIC_KEY && allArticles.length > 0) {
    try {
      const articleList = allArticles.slice(0, 8).map((a, i) =>
        `${i+1}. [${a.section.toUpperCase()}] "${a.title}" — ${(a.deck||"").substring(0,80)}`
      ).join("\n");

      const claudeRes = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: {
          "x-api-key": ANTHROPIC_KEY,
          "anthropic-version": "2023-06-01",
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          model: "claude-haiku-4-5-20251001",
          max_tokens: 800,
          messages: [{
            role: "user",
            content: `You are S.C. Thomas, Editor in Chief of NY Spotlight Report — New York's entertainment authority. Write a sharp 1-line kicker and 1-sentence editorial deck for each article. Direct, authoritative, NYC-focused.

Return ONLY JSON array: [{"index":1,"kicker":"...","editorialDeck":"..."},...]

Articles:\n${articleList}`
          }]
        }),
        signal: AbortSignal.timeout(15000)
      });

      if (claudeRes.ok) {
        const cd = await claudeRes.json();
        const text = cd.content?.[0]?.text || "[]";
        const clean = text.replace(/```json|```/g, "").trim();
        const enhancements = JSON.parse(clean);
        if (Array.isArray(enhancements)) {
          enhancements.forEach(e => {
            if (allArticles[e.index - 1]) {
              allArticles[e.index-1].kicker = e.kicker;
              allArticles[e.index-1].editorialDeck = e.editorialDeck;
            }
          });
        }
      }
    } catch (e) {}
  }

  return {
    articles: allArticles,
    fetchedAt: new Date().toISOString(),
    count: allArticles.length,
    live: true,
  };
}

function getSectionKicker(section) {
  return { broadway:"Broadway Coverage", film:"Film Review", music:"Music Coverage",
           fashion:"NYC Fashion", tv:"Television", premiere:"NYC Premiere",
           nyc:"NYC Arts", awards:"Awards Season" }[section] || "Coverage";
}
