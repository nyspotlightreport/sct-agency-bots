
/* NY SPOTLIGHT REPORT — EXIT INTENT POPUP
   Shows after 30 seconds OR on exit intent
   Promotes: Newsletter + Sleep No More/Life & Trust/Death of Rasputin coverage
   NO ProFlow/SaaS content on NYSR pages — constitution law
*/
(function() {
  var SHOWN_KEY = 'nysr_popup_shown';
  var SHOWN_SESSION = 'nysr_popup_session';
  
  // Don't show more than once per session or more than once per 7 days
  var lastShown = localStorage.getItem(SHOWN_KEY);
  if (sessionStorage.getItem(SHOWN_SESSION)) return;
  if (lastShown && (Date.now() - parseInt(lastShown)) < 7 * 24 * 60 * 60 * 1000) return;

  var styles = `
    #nysr-popup-overlay {
      position: fixed; inset: 0; background: rgba(0,0,0,.72);
      z-index: 99999; display: flex; align-items: center; justify-content: center;
      opacity: 0; transition: opacity .35s; font-family: Georgia, serif;
    }
    #nysr-popup-overlay.show { opacity: 1; }
    #nysr-popup {
      background: #1A1A2E; border: 1px solid #C9A84C; border-radius: 10px;
      max-width: 520px; width: 92%; padding: 40px 36px; position: relative;
      box-shadow: 0 24px 80px rgba(0,0,0,.6); text-align: center; color: #e8e4d9;
    }
    #nysr-popup .close-btn {
      position: absolute; top: 14px; right: 18px; background: none; border: none;
      color: #888; font-size: 1.4em; cursor: pointer; line-height: 1;
    }
    #nysr-popup .close-btn:hover { color: #C9A84C; }
    #nysr-popup .eyebrow {
      font-family: Arial, sans-serif; font-size: .7em; letter-spacing: .2em;
      text-transform: uppercase; color: #C9A84C; margin-bottom: 14px;
    }
    #nysr-popup h2 {
      font-size: 1.6em; color: #fff; margin-bottom: 10px; line-height: 1.25;
    }
    #nysr-popup p {
      font-size: .92em; color: #bbb; margin-bottom: 22px; line-height: 1.65;
    }
    #nysr-popup .highlights {
      display: flex; gap: 10px; justify-content: center; margin-bottom: 24px;
      flex-wrap: wrap;
    }
    #nysr-popup .badge {
      background: rgba(201,168,76,.12); border: 1px solid rgba(201,168,76,.3);
      color: #C9A84C; font-family: Arial,sans-serif; font-size: .72em;
      padding: 5px 12px; border-radius: 20px; letter-spacing: .06em;
      text-transform: uppercase;
    }
    #nysr-popup form { display: flex; gap: 10px; }
    #nysr-popup input[type=email] {
      flex: 1; padding: 12px 16px; border: 1px solid #333; border-radius: 6px;
      background: #0d0d1a; color: #e8e4d9; font-size: .9em; outline: none;
    }
    #nysr-popup input[type=email]:focus { border-color: #C9A84C; }
    #nysr-popup button[type=submit] {
      background: #C9A84C; color: #1A1A2E; font-family: Arial,sans-serif;
      font-weight: 700; font-size: .84em; padding: 12px 20px; border: none;
      border-radius: 6px; cursor: pointer; text-transform: uppercase;
      letter-spacing: .06em; white-space: nowrap;
    }
    #nysr-popup button[type=submit]:hover { background: #e0c068; }
    #nysr-popup .no-thanks {
      margin-top: 14px; font-family: Arial,sans-serif; font-size: .75em;
      color: #555; cursor: pointer;
    }
    #nysr-popup .no-thanks:hover { color: #888; }
    #nysr-popup .success { color: #81c784; font-size: .95em; margin-top: 12px; display: none; }
    @media (max-width: 480px) {
      #nysr-popup form { flex-direction: column; }
      #nysr-popup { padding: 30px 22px; }
    }
  `;

  function createPopup() {
    var style = document.createElement('style');
    style.textContent = styles;
    document.head.appendChild(style);

    var overlay = document.createElement('div');
    overlay.id = 'nysr-popup-overlay';
    overlay.innerHTML = `
      <div id="nysr-popup">
        <button class="close-btn" onclick="closeNYSRPopup()" aria-label="Close">&times;</button>
        <div class="eyebrow">NY Spotlight Report &bull; ISSN 2026-0147</div>
        <h2>New York's Immersive Theater Scene Has Never Looked Like This</h2>
        <p>Inside coverage of Sleep No More, Life and Trust, The Death of Rasputin,
        and the stories nobody else is telling. Plus books, fashion, nightlife, and culture
        &#8212; all from the streets of New York.</p>
        <div class="highlights">
          <span class="badge">Sleep No More</span>
          <span class="badge">Life &amp; Trust</span>
          <span class="badge">Death of Rasputin</span>
          <span class="badge">NYC Culture</span>
        </div>
        <form id="nysr-popup-form" onsubmit="submitNYSRPopup(event)">
          <input type="email" id="nysr-popup-email" placeholder="Your email address" required>
          <button type="submit">Subscribe</button>
        </form>
        <div class="success" id="nysr-popup-success">
          &#10003; You&#8217;re in. Welcome to the inside.
        </div>
        <div class="no-thanks" onclick="closeNYSRPopup()">No thanks, I&#8217;ll miss out</div>
      </div>`;
    document.body.appendChild(overlay);
    setTimeout(function() { overlay.classList.add('show'); }, 50);
    overlay.addEventListener('click', function(e) {
      if (e.target === overlay) closeNYSRPopup();
    });
  }

  window.closeNYSRPopup = function() {
    var el = document.getElementById('nysr-popup-overlay');
    if (el) { el.style.opacity = '0'; setTimeout(function() { el.remove(); }, 350); }
    sessionStorage.setItem(SHOWN_SESSION, '1');
    localStorage.setItem(SHOWN_KEY, Date.now().toString());
  };

  window.submitNYSRPopup = function(e) {
    e.preventDefault();
    var email = document.getElementById('nysr-popup-email').value;
    if (!email) return;
    // Submit to Netlify function
    fetch('/.netlify/functions/subscribe', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({email: email, source: 'exit_popup'})
    }).catch(function(){});
    document.getElementById('nysr-popup-form').style.display = 'none';
    document.getElementById('nysr-popup-success').style.display = 'block';
    setTimeout(function() { closeNYSRPopup(); }, 3000);
    localStorage.setItem(SHOWN_KEY, Date.now().toString());
    sessionStorage.setItem(SHOWN_SESSION, '1');
  };

  // Trigger: exit intent (mouseleave top of page) OR 30 second timer
  var triggered = false;
  function trigger() {
    if (triggered) return;
    triggered = true;
    createPopup();
  }

  // Exit intent
  document.addEventListener('mouseleave', function(e) {
    if (e.clientY <= 5) trigger();
  });

  // 30 second fallback
  setTimeout(trigger, 30000);

  // Mobile: scroll to bottom
  window.addEventListener('scroll', function() {
    var scrolled = (window.scrollY + window.innerHeight) / document.documentElement.scrollHeight;
    if (scrolled > 0.85) trigger();
  }, {passive: true});

})();
