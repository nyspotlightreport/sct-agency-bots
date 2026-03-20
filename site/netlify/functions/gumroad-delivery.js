const PRODUCT_MAP = {
  "hrmta":  { file: "100_instagram_captions.pdf",         name: "100 Instagram Caption Templates" },
  "uizhhy": { file: "content_creation_checklist.pdf",     name: "Content Creation Checklist" },
  "arleib": { file: "annual_business_plan_template.pdf",  name: "Annual Business Plan Template" },
  "ubcsk":  { file: "daily_habit_tracker_30day.pdf",      name: "Daily Habit Tracker" },
  "shtebf": { file: "weekly_meal_prep_planner.pdf",       name: "Weekly Meal Prep Planner" },
  "tzmuw":  { file: "monthly_budget_planner.pdf",         name: "Monthly Budget Planner" },
  "anlxcn": { file: "50_chatgpt_prompts_business.pdf",    name: "50 ChatGPT Prompts for Business" },
  "jdimsu": { file: "30_day_social_content_calendar.pdf", name: "30-Day Social Media Calendar" },
  "cxacdr": { file: "90_day_goal_planner.pdf",            name: "90-Day Goal Planner" },
  "ybryh":  { file: "passive_income_zero_cost_guide.pdf", name: "Passive Income Zero-Cost Guide" },
};

exports.handler = async (event) => {
  const headers = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "POST, GET, OPTIONS",
    "Content-Type": "application/json"
  };

  if (event.httpMethod === "OPTIONS") {
    return { statusCode: 200, headers, body: "" };
  }

  if (event.httpMethod === "GET") {
    return { statusCode: 200, headers, body: JSON.stringify({ status: "Gumroad delivery webhook active", products: Object.keys(PRODUCT_MAP).length }) };
  }

  try {
    const params = new URLSearchParams(event.body || "");
    const email     = params.get("email") || "";
    const permalink = params.get("product_permalink") || "";
    const buyerName = params.get("full_name") || "there";
    const product   = PRODUCT_MAP[permalink];

    if (!product || !email) {
      console.log("Unknown product or no email:", permalink, email);
      return { statusCode: 200, headers, body: JSON.stringify({ received: true }) };
    }

    const BASE = "https://nyspotlightreport.com/downloads";
    const downloadUrl = `${BASE}/${product.file}`;

    console.log(`SALE: ${product.name} -> ${email} -> ${downloadUrl}`);

    const https = require("https");
    const { URL } = require("url");

    const gmailUser = process.env.GMAIL_USER || "nyspotlightreport@gmail.com";
    const gmailPass = process.env.GMAIL_APP_PASS || "";

    if (gmailPass) {
      const nodemailer = require("nodemailer");
      const transporter = nodemailer.createTransport({
        service: "gmail",
        auth: { user: gmailUser, pass: gmailPass }
      });
      await transporter.sendMail({
        from: `"NY Spotlight Report" <${gmailUser}>`,
        to: email,
        subject: `Download ready: ${product.name}`,
        html: `<div style="font-family:sans-serif;max-width:520px;margin:0 auto;padding:40px 20px;">
          <h2 style="color:#0D1B2A;margin:0 0 16px;">Hi ${buyerName}!</h2>
          <p style="color:#444;margin:0 0 24px;">Your purchase of <strong>${product.name}</strong> is confirmed. Click below to download instantly.</p>
          <a href="${downloadUrl}" style="display:inline-block;background:#C9A84C;color:#fff;padding:14px 32px;border-radius:8px;text-decoration:none;font-weight:700;font-size:16px;">Download Your PDF</a>
          <p style="color:#999;font-size:12px;margin:24px 0 0;">Direct link: <a href="${downloadUrl}" style="color:#999;">${downloadUrl}</a></p>
          <p style="color:#bbb;font-size:12px;margin:8px 0 0;">NY Spotlight Report &bull; nyspotlightreport.com</p>
        </div>`
      });
      console.log("Email sent to", email);
    }

    return { statusCode: 200, headers, body: JSON.stringify({ success: true, delivered: email }) };
  } catch (err) {
    console.error("Delivery error:", err.message);
    return { statusCode: 200, headers, body: JSON.stringify({ received: true }) };
  }
};
