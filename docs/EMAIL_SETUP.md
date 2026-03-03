# Remembra Email System - Setup Guide

Complete guide for setting up transactional emails in Remembra Cloud.

## Overview

Remembra's email system sends transactional emails for:
- ✉️ Welcome emails with API keys
- ⚠️ Usage warnings (80% of limit)
- 🚨 Limit exceeded notifications
- 💰 Payment receipts
- 🔄 Subscription cancellations

## Quick Start

### 1. Choose Your Provider

**Option A: Resend (Recommended)**
- ✅ FREE: 3,000 emails/month
- ✅ Modern developer experience
- ✅ Better deliverability
- ✅ $20 for 50k emails

**Option B: SMTP (Gmail/Google Workspace)**
- ⚠️ Daily limits (100-500 emails)
- ⚠️ Not ideal for transactional emails
- ✅ Free (if you already have account)

### 2. Get API Credentials

#### Resend Setup
1. Sign up at [resend.com](https://resend.com)
2. Go to API Keys page
3. Create a new API key
4. Copy the key (starts with `re_`)

#### SMTP Setup (Gmail)
1. Enable 2FA on your Google account
2. Go to [App Passwords](https://myaccount.google.com/apppasswords)
3. Create app password for "Mail"
4. Copy the 16-character password

### 3. Install Dependencies

```bash
cd /Users/dolphy/projects/remembra
pip install -r requirements-email.txt
```

### 4. Configure Environment Variables

Add to your `.env` file or environment:

#### For Resend:
```bash
RESEND_API_KEY=re_your_api_key_here
```

#### For SMTP (Gmail):
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=partnerships@dolphytech.com
SMTP_PASSWORD=your_app_password_here
```

### 5. Test the Email System

```bash
# Test with Resend
RESEND_API_KEY=your_key python scripts/test_email.py \
  --provider resend \
  --email admin@dolphytech.com \
  --all

# Test with SMTP
SMTP_USERNAME=partnerships@dolphytech.com \
SMTP_PASSWORD=your_password \
python scripts/test_email.py \
  --provider smtp \
  --email admin@dolphytech.com
```

### 6. Verify Emails Arrive

Check your test email inbox. You should receive:
- Welcome email with API key
- Usage warning email
- Limit exceeded email
- Payment receipt email
- Subscription cancelled email

---

## Integration with Provisioning

The email system is already integrated with provisioning:

```python
from remembra.cloud.email import EmailService, EmailProvider
from remembra.cloud.provisioning import TenantProvisioner

# Create email service
email_service = EmailService.create(provider=EmailProvider.RESEND)

# Create provisioner with email support
provisioner = TenantProvisioner(
    meter=meter,
    key_manager=key_manager,
    email_service=email_service,  # ← Enables email sending
)

# Provision user - automatically sends welcome email
result = await provisioner.provision(
    email="user@example.com",  # ← Email required for welcome email
    name="John Doe",
    plan=PlanTier.PRO,
)
```

---

## Integration with Stripe Webhooks

Example webhook handler for sending emails on billing events:

```python
from remembra.cloud.email import EmailService, EmailProvider

# Initialize email service
email_service = EmailService.create(provider=EmailProvider.RESEND)

# In your webhook handler
async def handle_stripe_webhook(event: dict):
    event_type = event["type"]
    
    if event_type == "invoice.payment_succeeded":
        # Send payment receipt
        invoice = event["data"]["object"]
        customer_email = invoice["customer_email"]
        
        await email_service.send_payment_receipt_email(
            to=customer_email,
            amount=f"${invoice['amount_paid'] / 100:.2f}",
            invoice_url=invoice["hosted_invoice_url"],
            plan="Pro",
            period_start=format_date(invoice["period_start"]),
            period_end=format_date(invoice["period_end"]),
        )
    
    elif event_type == "customer.subscription.deleted":
        # Send cancellation email
        subscription = event["data"]["object"]
        customer_email = get_customer_email(subscription["customer"])
        
        await email_service.send_subscription_cancelled_email(
            to=customer_email,
            plan="Pro",
            cancel_date=format_date(subscription["current_period_end"]),
        )
```

---

## Usage Monitoring Integration

Send usage warnings when users approach their limit:

```python
from remembra.cloud.limits import LimitEnforcer
from remembra.cloud.email import EmailService, EmailProvider

email_service = EmailService.create(provider=EmailProvider.RESEND)
enforcer = LimitEnforcer(meter=meter)

async def check_and_notify_usage(user_id: str, email: str):
    """Check usage and send warning if needed."""
    usage = await enforcer.check_limits(user_id)
    
    if usage.usage_percent >= 80 and usage.usage_percent < 100:
        # Send 80% warning (once)
        await email_service.send_usage_warning_email(
            to=email,
            usage_percent=usage.usage_percent,
            current_usage=usage.current_usage,
            limit=usage.limit,
            plan=usage.plan,
        )
    
    elif usage.usage_percent >= 100:
        # Send limit exceeded notice
        await email_service.send_limit_exceeded_email(
            to=email,
            current_usage=usage.current_usage,
            limit=usage.limit,
            plan=usage.plan,
        )
```

---

## Email Templates

All templates are in: `/src/remembra/cloud/templates/email/`

### Customization

To customize templates:
1. Edit the HTML files directly
2. Use `{variable_name}` for dynamic content
3. Follow the Remembra brand colors (see `templates/email/README.md`)
4. Test with `scripts/test_email.py`

### Variables

Each template supports different variables. See individual template files for details.

Common variables:
- `{dashboard_url}` - https://app.remembra.dev
- `{docs_url}` - https://remembra.dev/docs
- `{upgrade_url}` - https://app.remembra.dev/billing

---

## Production Deployment

### Environment Variables (Coolify)

Add these to your Remembra API service in Coolify:

```
RESEND_API_KEY=re_your_production_key
```

### Domain Verification (Resend)

1. Go to Resend dashboard → Domains
2. Add domain: `remembra.dev`
3. Add DNS records to Cloudflare:
   - DKIM record
   - SPF record
   - DMARC record (recommended)
4. Wait for verification (usually < 5 minutes)

### Email Addresses

Configure these in code:
- **From**: `noreply@remembra.dev`
- **Reply-To**: `support@remembra.dev` (optional)

---

## Monitoring & Debugging

### Check Email Logs

Resend provides:
- Email delivery status
- Open/click tracking (optional)
- Bounce notifications
- API request logs

Access at: [resend.com/emails](https://resend.com/emails)

### Test Mode

Resend has a test mode for development:
```python
# Send test email (won't actually deliver)
await email_service.send_welcome_email(
    to="test@resend.dev",  # Special test address
    api_key="test_key",
    user_id="test_user",
)
```

---

## Troubleshooting

### Emails Not Sending

1. **Check API key**: Make sure `RESEND_API_KEY` is set
2. **Check domain**: Verify domain in Resend dashboard
3. **Check logs**: Look at Remembra logs for errors
4. **Test manually**: Use `scripts/test_email.py`

### Emails Going to Spam

1. **Verify domain**: Add DKIM, SPF, DMARC records
2. **Warm up**: Start with low volume, increase gradually
3. **Content**: Avoid spam trigger words
4. **Unsubscribe link**: Always include (required by law)

### Rate Limits

Resend free tier:
- 3,000 emails/month
- 10 emails/second

If you hit limits:
- Upgrade to paid plan
- Implement email queuing
- Batch notifications

---

## Cost Estimates

### Resend Pricing

| Emails/Month | Cost   |
|--------------|--------|
| 3,000        | FREE   |
| 50,000       | $20    |
| 100,000      | $35    |
| 500,000      | $350   |

### Expected Usage

Assuming 1,000 customers:
- Welcome emails: 1,000
- Usage warnings: ~200 (20%)
- Payment receipts: 1,000/month
- Cancellations: ~50

**Total: ~2,250 emails/month** (well within free tier)

---

## Support

- **Resend Docs**: [resend.com/docs](https://resend.com/docs)
- **Remembra Email Code**: `/src/remembra/cloud/email.py`
- **Templates**: `/src/remembra/cloud/templates/email/`
- **Test Script**: `/scripts/test_email.py`

Need help? Reply to any Remembra email or contact support.
