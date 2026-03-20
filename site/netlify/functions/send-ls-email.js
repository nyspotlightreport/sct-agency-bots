exports.handler = async () => {
  try {
    const user = process.env.GMAIL_USER;
    const pass = process.env.GMAIL_APP_PASS;
    if (!user || !pass) return { statusCode: 200, body: "no creds" };

    const nodemailer = require("nodemailer");
    const t = nodemailer.createTransport({ service: "gmail", auth: { user, pass } });
    await t.sendMail({
      from: `"S.C. Thomas | NY Spotlight Report" <${user}>`,
      to: "hello@lemonsqueezy.com",
      replyTo: user,
      subject: "Re: Your application has been received: nysr",
      html: `<div style="font-family:sans-serif;max-width:560px;line-height:1.6;">
        <p>Hi team,</p>
        <p>Thank you for the quick response. Happy to share product samples to expedite onboarding.</p>
        <p><strong>About the store:</strong> NY Spotlight Report is a New York-based digital media brand selling productivity and business tools — planners, prompt packs, content templates, and strategy guides — targeting entrepreneurs and content creators.</p>
        <p><strong>Product samples (live now):</strong></p>
        <ul>
          <li><strong>90-Day Goal Planner</strong> ($12.99) — <a href="https://spotlightny.gumroad.com/l/cxacdr">spotlightny.gumroad.com/l/cxacdr</a></li>
          <li><strong>50 ChatGPT Prompts for Business</strong> ($7.99) — <a href="https://spotlightny.gumroad.com/l/anlxcn">spotlightny.gumroad.com/l/anlxcn</a></li>
          <li><strong>Passive Income Zero-Cost Guide</strong> ($14.99) — <a href="https://spotlightny.gumroad.com/l/ybryh">spotlightny.gumroad.com/l/ybryh</a></li>
        </ul>
        <p>10 products live in total. All instant PDF downloads. Store: <a href="https://spotlightny.gumroad.com">spotlightny.gumroad.com</a></p>
        <p>Website: <a href="https://nyspotlightreport.com">nyspotlightreport.com</a></p>
        <p>We want to use LemonSqueezy specifically for the built-in affiliate program (30% commission) to grow sales without paid ads. Please let me know if you need anything else.</p>
        <p>Best,<br>S.C. Thomas<br>Chairman, NY Spotlight Report<br>nyspotlightreport@gmail.com</p>
      </div>`
    });
    return { statusCode: 200, body: JSON.stringify({ sent: true, to: "hello@lemonsqueezy.com" }) };
  } catch(e) {
    return { statusCode: 500, body: e.message };
  }
};
