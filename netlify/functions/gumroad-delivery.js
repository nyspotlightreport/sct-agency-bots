const PRODUCT_MAP = {
  "hrmta":  { file: "100_instagram_captions.pdf",         name: "100 Instagram Caption Templates" },
  "uizhhy": { file: "content_creation_checklist.pdf",     name: "Content Creation Checklist" },
  "arleib": { file: "annual_business_plan_template.pdf",  name: "Annual Business Plan Template" },
  "ubcsk":  { file: "daily_habit_tracker_30day.pdf",      name: "Daily Habit Tracker — 30 Day Reset" },
  "shtebf": { file: "weekly_meal_prep_planner.pdf",       name: "Weekly Meal Prep Planner" },
  "tzmuw":  { file: "monthly_budget_planner.pdf",         name: "Monthly Budget Planner" },
  "anlxcn": { file: "50_chatgpt_prompts_business.pdf",    name: "50 ChatGPT Prompts for Business" },
  "jdimsu": { file: "30_day_social_content_calendar.pdf", name: "30-Day Social Media Calendar" },
  "cxacdr": { file: "90_day_goal_planner.pdf",            name: "90-Day Goal Planner" },
  "ybryh":  { file: "passive_income_zero_cost_guide.pdf", name: "Passive Income Zero-Cost Guide" },
};
const BASE = "https://nyspotlightreport.com/downloads";

exports.handler = async (event) => {
  if (event.httpMethod !== "POST") return { statusCode: 200, body: "OK" };
  try {
    const p    = new URLSearchParams(event.body);
    const email     = p.get("email") || "";
    const permalink = p.get("product_permalink") || "";
    const name      = p.get("full_name") || "there";
    const product   = PRODUCT_MAP[permalink];
    if (!product || !email) return { statusCode: 200, body: "skip" };

    const downloadUrl = `${BASE}/${product.file}`;

    // Send via Gmail SMTP using nodemailer
    const nodemailer = require("nodemailer");
    const transporter = nodemailer.createTransport({
      service: "gmail",
      auth: { user: process.env.GMAIL_USER, pass: process.env.GMAIL_APP_PASS }
    });

    await transporter.sendMail({
      from: `"NY Spotlight Report" <${process.env.GMAIL_USER}>`,
      to: email,
      subject: `Your Download Is Ready: ${product.name}`,
      html: `<div style="font-family:sans-serif;max-width:500px;margin:40px auto;">
        <h2 style="color:#0D1B2A;">Hi ${name}! 🎉</h2>
        <p>Thank you for your purchase. Your download is ready:</p>
        <p><strong>${product.name}</strong></p>
        <a href="${downloadUrl}" style="display:inline-block;background:#C9A84C;color:#fff;padding:14px 28px;border-radius:8px;text-decoration:none;font-weight:700;font-size:16px;margin:20px 0;">
          ⬇ Download Your PDF
        </a>
        <p style="font-size:13px;color:#999;">
          Or copy this link: <a href="${downloadUrl}">${downloadUrl}</a><br>
          This link is yours to keep forever.
        </p>
        <p style="font-size:13px;color:#999;">— NY Spotlight Report<br>nyspotlightreport.com</p>
      </div>`
    });

    console.log(`✅ Delivered ${product.name} to ${email}`);
    return { statusCode: 200, body: JSON.stringify({ success: true }) };
  } catch (err) {
    console.error(err);
    return { statusCode: 500, body: "error" };
  }
};
