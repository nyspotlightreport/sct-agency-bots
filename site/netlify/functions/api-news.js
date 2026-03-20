// Simple serverless function — fetches live news directly, no Blobs needed
exports.handler = async (event) => {
  const GUARDIAN_KEY  = process.env.GUARDIAN_API_KEY  || "test";
  const NEWSAPI_KEY   = process.env.NEWSAPI_KEY       || "";
  const ANTHROPIC_KEY = process.env.ANTHROPIC_API_KEY || "";

  const allArticles = [];

  // Guardian API (free with test key)
  const guardianSections = [
    { section:"broadway", tag:"stage/theatre" },
    { section:"film",     tag:"film/film"     },
    { section:"music",    tag:"music/music"   },
    { section:"fashion",  tag:"fashion/fashion"},
    { section:"tv",       tag:"tv-and-radio/tv-and-radio"},
    { section:"nyc",      tag:"us-news/new-york"},
  ];

  for (const { section, tag } of guardianSections) {
    try {
      const r = await fetch(
        `https://content.guardianapis.com/search?tag=${tag}&order-by=newest&page-size=5&show-fields=headline,trailText,thumbnail&api-key=${GUARDIAN_KEY}`,
        { signal: AbortSignal.timeout(6000) }
      );
      if (r.ok) {
        const data = await r.json();
        (data.response?.results || []).slice(0,4).forEach(a => {
          allArticles.push({
            title:   a.fields?.headline || a.webTitle,
            deck:    a.fields?.trailText || "",
            url:     a.webUrl,
            img:     a.fields?.thumbnail || "",
            source:  "The Guardian",
            date:    a.webPublicationDate,
            section,
            kicker:  ({broadway:"Broadway Coverage",film:"Film Review",music:"Music Coverage",
                       fashion:"NYC Fashion",tv:"Television",nyc:"NYC News"})[section]||"Coverage"
          });
        });
      }
    } catch {}
    await new Promise(r => setTimeout(r, 80));
  }

  // NewsAPI
  if (NEWSAPI_KEY) {
    const nQueries = [
      { q:"Broadway theater New York musical premiere 2026", section:"broadway" },
      { q:"film premiere New York cinema review 2026",       section:"film"     },
      { q:"fashion designer New York NYFW 2026",             section:"fashion"  },
    ];
    for (const { q, section } of nQueries) {
      try {
        const r = await fetch(
          `https://newsapi.org/v2/everything?q=${encodeURIComponent(q)}&language=en&sortBy=publishedAt&pageSize=3&apiKey=${NEWSAPI_KEY}`,
          { signal: AbortSignal.timeout(6000) }
        );
        if (r.ok) {
          const data = await r.json();
          (data.articles||[]).filter(a=>a.title&&a.title!=="[Removed]").slice(0,3).forEach(a=>{
            allArticles.push({
              title:a.title,deck:a.description||"",url:a.url,
              img:a.urlToImage||"",source:a.source?.name||"News",
              date:a.publishedAt,section,kicker:"Breaking News"
            });
          });
        }
      } catch {}
      await new Promise(r=>setTimeout(r,100));
    }
  }

  // Claude editorial enhancement
  if (ANTHROPIC_KEY && allArticles.length > 0) {
    try {
      const list = allArticles.slice(0,8).map((a,i)=>
        `${i+1}. [${a.section.toUpperCase()}] "${a.title}" — ${(a.deck||"").substring(0,80)}`
      ).join("\n");

      const res = await fetch("https://api.anthropic.com/v1/messages",{
        method:"POST",
        headers:{"x-api-key":ANTHROPIC_KEY,"anthropic-version":"2023-06-01","Content-Type":"application/json"},
        body:JSON.stringify({
          model:"claude-haiku-4-5-20251001",max_tokens:800,
          messages:[{role:"user",content:`You are S.C. Thomas, Editor in Chief of NY Spotlight Report — New York's entertainment authority. Write a sharp 1-line kicker and 1-sentence editorial deck for each article. Direct, authoritative, NYC-focused.\n\nReturn ONLY JSON array: [{"index":1,"kicker":"...","editorialDeck":"..."},...]\n\nArticles:\n${list}`}]
        }),
        signal:AbortSignal.timeout(12000)
      });
      if(res.ok){
        const cd=await res.json();
        const text=(cd.content?.[0]?.text||"[]").replace(/```json|```/g,"").trim();
        JSON.parse(text).forEach(e=>{
          if(allArticles[e.index-1]){
            allArticles[e.index-1].kicker=e.kicker;
            allArticles[e.index-1].editorialDeck=e.editorialDeck;
          }
        });
      }
    } catch(e){ console.warn("Claude:",e.message); }
  }

  return {
    statusCode: 200,
    headers: {
      "Content-Type": "application/json",
      "Cache-Control": "public, max-age=300, stale-while-revalidate=1800",
      "Access-Control-Allow-Origin": "*",
    },
    body: JSON.stringify({
      articles:   allArticles,
      fetchedAt:  new Date().toISOString(),
      count:      allArticles.length,
      sources:    ["guardian"+(NEWSAPI_KEY?",newsapi":"")+(ANTHROPIC_KEY?"+claude":"")],
      live:       true,
    })
  };
};
