#!/usr/bin/env python3
"""
INVOICE GENERATOR + PAYMENT REMINDER BOT — S.C. Thomas Internal Agency
Generates PDF invoices, tracks payment status, sends reminders for overdue invoices.
Usage:
  python invoice_bot.py --create --client "Client Name" --amount 2500 --description "SEO Services March"
  python invoice_bot.py --remind  (sends reminders for all overdue invoices)
  python invoice_bot.py --status  (prints all invoice statuses)
"""

import os
import json
import argparse
import smtplib
import requests
from datetime import datetime, timedelta
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ─── CONFIG ───────────────────────────────────────────────────────────────────
GMAIL_USER      = os.getenv("GMAIL_USER", "seanb041992@gmail.com")
GMAIL_APP_PASS  = os.getenv("GMAIL_APP_PASS", "")
CHAIRMAN_EMAIL  = os.getenv("CHAIRMAN_EMAIL", "seanb041992@gmail.com")
PAYPAL_ME_LINK  = os.getenv("PAYPAL_ME_LINK", "https://paypal.me/yourhandle")  # Update this
INVOICE_DIR     = Path("invoices")
INVOICE_DIR.mkdir(exist_ok=True)
STATE_FILE      = Path("invoice_state.json")

# Your business info
BUSINESS_NAME    = os.getenv("BUSINESS_NAME", "S.C. Thomas")
BUSINESS_EMAIL   = os.getenv("BUSINESS_EMAIL", "seanb041992@gmail.com")
BUSINESS_ADDRESS = os.getenv("BUSINESS_ADDRESS", "New York, NY")
PAYMENT_TERMS    = int(os.getenv("PAYMENT_TERMS", "15"))  # Net 15 default

# ─── STATE ────────────────────────────────────────────────────────────────────
def load_invoices():
    if STATE_FILE.exists():
        with open(STATE_FILE) as f: return json.load(f)
    return {}

def save_invoices(invoices):
    with open(STATE_FILE, "w") as f: json.dump(invoices, f, indent=2)

def next_invoice_number(invoices):
    if not invoices: return f"INV-{datetime.now().year}-001"
    nums = [int(k.split("-")[-1]) for k in invoices.keys() if k.split("-")[-1].isdigit()]
    next_num = (max(nums) + 1) if nums else 1
    return f"INV-{datetime.now().year}-{next_num:03d}"

# ─── INVOICE CREATOR ──────────────────────────────────────────────────────────
def create_invoice(client_name, client_email, amount, description, line_items=None):
    invoices    = load_invoices()
    invoice_num = next_invoice_number(invoices)
    issue_date  = datetime.now()
    due_date    = issue_date + timedelta(days=PAYMENT_TERMS)

    if not line_items:
        line_items = [{"description": description, "qty": 1, "rate": amount, "total": amount}]

    invoice = {
        "number":       invoice_num,
        "client_name":  client_name,
        "client_email": client_email,
        "amount":       amount,
        "description":  description,
        "line_items":   line_items,
        "issue_date":   issue_date.isoformat(),
        "due_date":     due_date.isoformat(),
        "status":       "sent",
        "reminders_sent": 0,
        "paid_date":    None,
    }

    invoices[invoice_num] = invoice
    save_invoices(invoices)

    # Generate HTML invoice
    html = build_invoice_html(invoice)
    invoice_file = INVOICE_DIR / f"{invoice_num}.html"
    with open(invoice_file, "w") as f: f.write(html)

    # Send to client
    if client_email:
        send_invoice_email(invoice, html)
    
    # Notify Chairman
    notify_chairman_created(invoice)
    
    print(f"[invoice-bot] Created {invoice_num} for {client_name} — ${amount:,.2f} — Due {due_date.strftime('%b %d, %Y')}")
    return invoice

def build_invoice_html(inv):
    issue_str = datetime.fromisoformat(inv["issue_date"]).strftime("%B %d, %Y")
    due_str   = datetime.fromisoformat(inv["due_date"]).strftime("%B %d, %Y")
    items_html = "".join([
        f"""<tr>
          <td style="padding:10px 12px;border-bottom:1px solid #eee;">{item['description']}</td>
          <td style="padding:10px 12px;border-bottom:1px solid #eee;text-align:center;">{item['qty']}</td>
          <td style="padding:10px 12px;border-bottom:1px solid #eee;text-align:right;">${item['rate']:,.2f}</td>
          <td style="padding:10px 12px;border-bottom:1px solid #eee;text-align:right;">${item['total']:,.2f}</td>
        </tr>"""
        for item in inv.get("line_items", [])
    ])
    return f"""<!DOCTYPE html><html><head><meta charset="UTF-8"></head>
<body style="font-family:Arial,sans-serif;max-width:700px;margin:40px auto;color:#111;padding:0 20px;">
  <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:40px;">
    <div><h1 style="margin:0;font-size:32px;letter-spacing:2px;">INVOICE</h1>
         <p style="color:#888;margin:4px 0 0;">{BUSINESS_NAME}</p>
         <p style="color:#888;margin:2px 0;">{BUSINESS_ADDRESS}</p>
         <p style="color:#888;margin:2px 0;">{BUSINESS_EMAIL}</p></div>
    <div style="text-align:right;">
      <p style="font-size:20px;font-weight:bold;margin:0;">{inv['number']}</p>
      <p style="color:#888;margin:4px 0 0;">Issued: {issue_str}</p>
      <p style="color:#c62828;font-weight:bold;margin:2px 0;">Due: {due_str}</p>
    </div>
  </div>
  <div style="background:#f5f5f5;padding:16px 20px;margin-bottom:32px;border-left:4px solid #111;">
    <strong>BILL TO:</strong><br>{inv['client_name']}<br>{inv.get('client_email','')}
  </div>
  <table width="100%" style="border-collapse:collapse;margin-bottom:24px;">
    <thead><tr style="background:#111;color:#fff;">
      <th style="padding:10px 12px;text-align:left;">Description</th>
      <th style="padding:10px 12px;text-align:center;">Qty</th>
      <th style="padding:10px 12px;text-align:right;">Rate</th>
      <th style="padding:10px 12px;text-align:right;">Total</th>
    </tr></thead>
    <tbody>{items_html}</tbody>
  </table>
  <div style="text-align:right;margin-bottom:32px;">
    <div style="display:inline-block;background:#111;color:#fff;padding:12px 24px;">
      <span style="font-size:20px;font-weight:bold;">TOTAL: ${inv['amount']:,.2f}</span>
    </div>
  </div>
  <div style="background:#f9f9f9;padding:16px 20px;margin-bottom:24px;">
    <strong>Payment Methods:</strong><br>
    PayPal: <a href="{PAYPAL_ME_LINK}/{inv['amount']}">{PAYPAL_ME_LINK}</a><br>
    <em>Please include invoice number {inv['number']} in payment notes.</em>
  </div>
  <p style="color:#888;font-size:13px;">Payment due within {PAYMENT_TERMS} days of invoice date. Late payments subject to 1.5%/month fee.</p>
</body></html>"""

def send_invoice_email(inv, html):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"Invoice {inv['number']} — ${inv['amount']:,.2f} — Due {datetime.fromisoformat(inv['due_date']).strftime('%b %d, %Y')}"
    msg["From"]    = GMAIL_USER
    msg["To"]      = inv["client_email"]
    msg.attach(MIMEText(html, "html"))
    _send(inv["client_email"], msg)

def notify_chairman_created(inv):
    body = f"Invoice {inv['number']} created for {inv['client_name']} — ${inv['amount']:,.2f} — Due {datetime.fromisoformat(inv['due_date']).strftime('%b %d, %Y')}"
    msg = MIMEMultipart()
    msg["Subject"] = f"✅ Invoice Created: {inv['number']}"
    msg["From"]    = GMAIL_USER
    msg["To"]      = CHAIRMAN_EMAIL
    msg.attach(MIMEText(body))
    _send(CHAIRMAN_EMAIL, msg)

def _send(to, msg):
    if not GMAIL_APP_PASS: print(f"[invoice-bot] No email creds — would send to {to}"); return
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as s:
            s.login(GMAIL_USER, GMAIL_APP_PASS)
            s.sendmail(GMAIL_USER, to, msg.as_string())
    except Exception as e:
        print(f"[invoice-bot] Email failed: {e}")

# ─── REMINDER ENGINE ──────────────────────────────────────────────────────────
def send_reminders():
    invoices = load_invoices()
    now      = datetime.now()
    reminded = 0

    for inv_num, inv in invoices.items():
        if inv["status"] in ["paid", "cancelled"]: continue
        due_date  = datetime.fromisoformat(inv["due_date"])
        days_overdue = (now - due_date).days

        if days_overdue < 0: continue  # Not due yet

        reminders_sent = inv.get("reminders_sent", 0)

        # Reminder schedule: Day 0 (due), Day 7, Day 14, Day 30
        should_remind = (
            (days_overdue == 0  and reminders_sent == 0) or
            (days_overdue >= 7  and reminders_sent == 1) or
            (days_overdue >= 14 and reminders_sent == 2) or
            (days_overdue >= 30 and reminders_sent == 3)
        )

        if should_remind and inv.get("client_email"):
            send_reminder_email(inv, days_overdue)
            invoices[inv_num]["reminders_sent"] = reminders_sent + 1
            reminded += 1

    save_invoices(invoices)
    print(f"[invoice-bot] Sent {reminded} payment reminders")

def send_reminder_email(inv, days_overdue):
    urgency = "FINAL NOTICE — " if days_overdue >= 30 else ("OVERDUE — " if days_overdue > 0 else "")
    subject = f"{urgency}Invoice {inv['number']} — ${inv['amount']:,.2f} Due"
    tone    = "This is our final notice before escalation." if days_overdue >= 30 else ("This invoice is now past due." if days_overdue > 0 else "This invoice is due today.")
    
    body = f"""Hi {inv['client_name'].split()[0]},

{tone} Invoice {inv['number']} for ${inv['amount']:,.2f} {"was" if days_overdue > 0 else "is"} due {f"{days_overdue} days ago" if days_overdue > 0 else "today"}.

Pay now: {PAYPAL_ME_LINK}/{inv['amount']}
Reference: {inv['number']}

If payment has already been sent, please disregard this message.

Sean
{BUSINESS_NAME}"""

    msg = MIMEMultipart()
    msg["Subject"] = subject
    msg["From"]    = GMAIL_USER
    msg["To"]      = inv["client_email"]
    msg.attach(MIMEText(body))
    _send(inv["client_email"], msg)
    print(f"[invoice-bot] Reminder sent: {inv['number']} — {inv['client_name']} ({days_overdue}d overdue)")

def mark_paid(invoice_num):
    invoices = load_invoices()
    if invoice_num in invoices:
        invoices[invoice_num]["status"]    = "paid"
        invoices[invoice_num]["paid_date"] = datetime.now().isoformat()
        save_invoices(invoices)
        print(f"[invoice-bot] {invoice_num} marked as PAID")

def print_status():
    invoices = load_invoices()
    now = datetime.now()
    print(f"\n{'='*60}")
    print(f"INVOICE STATUS — {now.strftime('%Y-%m-%d')}")
    print(f"{'='*60}")
    total_outstanding = 0
    for num, inv in sorted(invoices.items()):
        due   = datetime.fromisoformat(inv["due_date"])
        days  = (now - due).days
        status_str = f"PAID ✅" if inv["status"] == "paid" else (f"OVERDUE {days}d 🔴" if days > 0 else f"Due in {-days}d")
        print(f"{num} | {inv['client_name']:<20} | ${inv['amount']:>8,.2f} | {status_str}")
        if inv["status"] != "paid": total_outstanding += inv["amount"]
    print(f"{'='*60}")
    print(f"OUTSTANDING: ${total_outstanding:,.2f}")

# ─── CLI ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--create",      action="store_true")
    p.add_argument("--remind",      action="store_true")
    p.add_argument("--status",      action="store_true")
    p.add_argument("--paid",        type=str, help="Mark invoice number as paid")
    p.add_argument("--client",      type=str)
    p.add_argument("--email",       type=str, default="")
    p.add_argument("--amount",      type=float)
    p.add_argument("--description", type=str, default="Services")
    args = p.parse_args()

    if args.create:
        if not args.client or not args.amount:
            print("Usage: --create --client 'Name' --email 'email@' --amount 1000 --description 'Services'")
        else:
            create_invoice(args.client, args.email, args.amount, args.description)
    elif args.remind:  send_reminders()
    elif args.status:  print_status()
    elif args.paid:    mark_paid(args.paid)
    else:
        print_status()
        send_reminders()

# SETUP: pip install requests
# GITHUB ACTIONS: Run --remind daily at 9am ET
# cron: '0 14 * * *'
