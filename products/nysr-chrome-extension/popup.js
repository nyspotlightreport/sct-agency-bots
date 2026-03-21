// NYSR AI Companion — Popup Script
// Commercial grade Chrome extension for NY Spotlight Report

const SYSTEM_PROMPT = `You are SC Thomas, founder of NY Spotlight Report — an AI-powered 
content agency in Coram, NY. Expert in passive income, AI automation, content marketing.
Voice: direct, expert, peer-level. Never generic. Always specific with numbers and results.
Brand: NY Spotlight Report | nyspotlightreport.com | ProFlow AI`;

async function callClaude(prompt, maxTokens = 800) {
  const { apiKey } = await chrome.storage.local.get('apiKey');
  if (!apiKey) {
    showToast('Add API key in Settings');
    return null;
  }
  
  const response = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': apiKey,
      'anthropic-version': '2023-06-01'
    },
    body: JSON.stringify({
      model: 'claude-haiku-4-5-20251001',
      max_tokens: maxTokens,
      system: SYSTEM_PROMPT,
      messages: [{ role: 'user', content: prompt }]
    })
  });
  
  if (!response.ok) {
    const err = await response.json();
    showToast(`API Error: ${err.error?.message?.slice(0,50)}`);
    return null;
  }
  
  const data = await response.json();
  return data.content?.[0]?.text || '';
}

async function getPageContent() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const results = await chrome.scripting.executeScript({
    target: { tabId: tab.id },
    func: () => document.body.innerText.slice(0, 3000)
  });
  return { url: tab.url, title: tab.title, content: results[0]?.result || '' };
}

function showOutput(elementId, text) {
  const el = document.getElementById(elementId);
  el.textContent = text;
  el.classList.add('visible');
}

function showLoading(btnId) {
  const btn = document.getElementById(btnId);
  if (btn) { btn.disabled = true; btn.textContent = '⟳ Generating...'; }
}

function resetBtn(btnId, text) {
  const btn = document.getElementById(btnId);
  if (btn) { btn.disabled = false; btn.textContent = text; }
}

function showToast(msg) {
  const toast = document.getElementById('toast');
  toast.textContent = msg;
  toast.classList.add('show');
  setTimeout(() => toast.classList.remove('show'), 2500);
}

function copyToClipboard(text) {
  navigator.clipboard.writeText(text);
  showToast('Copied to clipboard!');
}

async function compose() {
  const prompt = document.getElementById('composePrompt').value;
  const tone = document.getElementById('toneSelect').value;
  if (!prompt) return showToast('Enter a prompt first');
  
  showLoading('composeBtn');
  
  const result = await callClaude(
    `Write in a ${tone} tone: ${prompt}\n\nMake it specific, authentic, and ready to use immediately.`,
    600
  );
  
  resetBtn('composeBtn', 'Generate Content');
  
  if (result) {
    showOutput('composeOutput', result);
    document.getElementById('composeOutput').onclick = () => copyToClipboard(result);
    showToast('Click output to copy');
  }
}

async function analyzePage() {
  const page = await getPageContent();
  showOutput('analyzeOutput', 'Analyzing...');
  
  const result = await callClaude(
    `Analyze this webpage for business opportunities:\nURL: ${page.url}\nTitle: ${page.title}\nContent: ${page.content}\n\nProvide: 1) What this page is 2) Business opportunity 3) Recommended action for NY Spotlight Report`,
    500
  );
  
  if (result) showOutput('analyzeOutput', result);
}

async function summarizePage() {
  const page = await getPageContent();
  showOutput('analyzeOutput', 'Summarizing...');
  
  const result = await callClaude(
    `Summarize this page in 3 bullet points for business use:\n${page.title}\n${page.content}`,
    300
  );
  
  if (result) showOutput('analyzeOutput', result);
}

async function extractLeads() {
  const page = await getPageContent();
  showOutput('analyzeOutput', 'Extracting...');
  
  const result = await callClaude(
    `Extract any business/contact information from this page:\n${page.content}\n\nFormat: Name, Title, Company, Email, Phone, LinkedIn`,
    400
  );
  
  if (result) showOutput('analyzeOutput', result);
}

const QUICK_TEMPLATES = {
  linkedin_post: 'Write a high-engagement LinkedIn post about AI automation for entrepreneurs. Include: a surprising statistic, the problem, the solution, a call to action. Under 200 words.',
  tweet: 'Write a 5-tweet thread about passive income with AI bots. Hook tweet first. End with CTA to nyspotlightreport.com',
  cold_email: 'Write a cold email to a small business owner about ProFlow AI (AI content automation). Subject line + body. Under 150 words. High conversion focused.',
  blog_intro: 'Write a compelling blog post intro (150 words) about how AI is replacing content teams. Use a specific stat or surprising claim as the hook.',
  reply: 'Based on the current page content, write a professional, value-adding reply/comment that builds authority.',
  seo_meta: 'Write an SEO title tag (60 chars max) and meta description (155 chars max) for the current page.'
};

async function quickAction(type) {
  const output = document.getElementById('actionsOutput');
  output.textContent = 'Generating...';
  output.classList.add('visible');
  
  let prompt = QUICK_TEMPLATES[type] || type;
  
  if (type === 'reply' || type === 'seo_meta') {
    const page = await getPageContent();
    prompt = QUICK_TEMPLATES[type] + '\n\nPage context: ' + page.content.slice(0, 1000);
  }
  
  const result = await callClaude(prompt, 400);
  if (result) {
    showOutput('actionsOutput', result);
    output.onclick = () => copyToClipboard(result);
    showToast('Click to copy');
  }
}

function switchTab(name) {
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  
  const tabs = ['compose','analyze','actions','settings'];
  const idx = tabs.indexOf(name);
  document.querySelectorAll('.tab')[idx].classList.add('active');
  document.getElementById('panel-' + name).classList.add('active');
}

async function saveSettings() {
  const apiKey = document.getElementById('apiKeyInput').value;
  if (apiKey) {
    await chrome.storage.local.set({ apiKey });
    showToast('Settings saved ✓');
    document.getElementById('statusDot').style.background = '#22D3A0';
  }
}

// Load saved settings
chrome.storage.local.get(['apiKey'], ({ apiKey }) => {
  if (apiKey) {
    document.getElementById('apiKeyInput').value = apiKey;
    document.getElementById('statusDot').style.background = '#22D3A0';
  } else {
    document.getElementById('statusDot').style.background = '#EF4444';
  }
});

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
  if (e.ctrlKey && e.key === 'Enter') compose();
});
