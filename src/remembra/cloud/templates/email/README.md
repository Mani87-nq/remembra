# Remembra Email Templates

Professional HTML email templates for Remembra Cloud transactional emails.

## Templates

### 1. **welcome.html** - Welcome Email
Sent after new user signs up or subscribes.
- Displays API key (copy-paste friendly)
- Quick start guide
- Links to dashboard and docs

Variables:
- `{api_key}` - The user's API key
- `{user_id}` - The user's ID
- `{plan}` - Plan tier name (e.g., "Free", "Pro")
- `{dashboard_url}` - Link to dashboard
- `{docs_url}` - Link to documentation

---

### 2. **usage_warning.html** - 80% Usage Warning
Sent when user reaches 80% of their plan limit.
- Warning banner with usage percentage
- Visual progress bar
- Call to action to upgrade

Variables:
- `{usage_percent}` - Current usage percentage (e.g., 85)
- `{current_usage}` - Current memory count (e.g., 850)
- `{limit}` - Plan memory limit (e.g., 1000)
- `{plan}` - Plan tier name
- `{upgrade_url}` - Link to billing/upgrade page
- `{dashboard_url}` - Link to dashboard

---

### 3. **limit_exceeded.html** - Limit Reached
Sent when user hits 100% of their plan limit.
- Alert banner with red styling
- Explanation of what happens next
- Upgrade CTA

Variables:
- `{current_usage}` - Current memory count
- `{limit}` - Plan memory limit
- `{plan}` - Plan tier name
- `{upgrade_url}` - Link to billing/upgrade page
- `{dashboard_url}` - Link to dashboard

---

### 4. **payment_receipt.html** - Payment Confirmation
Sent after successful payment/subscription renewal.
- Payment details table
- Plan features list
- Link to invoice

Variables:
- `{amount}` - Payment amount (e.g., "$49.00")
- `{invoice_url}` - Stripe invoice URL
- `{plan}` - Plan tier name
- `{period_start}` - Billing period start date
- `{period_end}` - Billing period end date
- `{dashboard_url}` - Link to dashboard

---

### 5. **subscription_cancelled.html** - Subscription Cancelled
Sent when user cancels their subscription.
- Timeline of what happens
- Feedback request
- Reactivation CTA

Variables:
- `{plan}` - Cancelled plan tier name
- `{cancel_date}` - Date subscription ends
- `{dashboard_url}` - Link to dashboard
- `{resubscribe_url}` - Link to reactivate subscription

---

## Design System

All templates follow Remembra's dark theme brand identity:

### Colors
- **Background**: `#0F0F0F` (Dark black)
- **Card**: `#1A1A1A` (Lighter black)
- **Secondary BG**: `#252525` (Medium gray)
- **Primary (Purple)**: `#8B5CF6`
- **Primary Dark**: `#6D28D9`
- **Text**: `#FFFFFF` (White)
- **Text Secondary**: `#D0D0D0` (Light gray)
- **Text Tertiary**: `#A0A0A0` (Medium gray)
- **Success**: `#10B981` (Green)
- **Warning**: `#F59E0B` (Amber)
- **Error**: `#EF4444` (Red)

### Typography
- **Headlines**: 26-32px, font-weight 700
- **Body**: 16px, line-height 1.7-1.8
- **Small**: 13-14px
- **Code**: Courier New, monospace

### Layout
- **Max Width**: 600px
- **Padding**: 40px (desktop), 20px (mobile)
- **Border Radius**: 8-12px
- **Box Shadow**: `0 4px 20px rgba(0, 0, 0, 0.5)`

### Components
- **Header**: Purple brand name with 3px bottom border
- **Buttons**: Purple gradient with shadow, 16px padding, rounded
- **Info Boxes**: Colored left border with light background
- **Code Blocks**: Dark background with purple text
- **Footer**: Dark with unsubscribe link (CAN-SPAM compliance)

---

## Testing

Use the test script to preview emails:

```bash
# Test all templates
RESEND_API_KEY=your_key python scripts/test_email.py --all --email test@example.com

# Test specific template
python scripts/test_email.py --template welcome --email test@example.com
```

---

## Compliance

All templates include:
- ✅ Unsubscribe link (footer)
- ✅ Physical address (footer)
- ✅ Clear sender identity
- ✅ Professional design
- ✅ Mobile responsive (email clients)
- ✅ Dark mode optimized

CAN-SPAM Act compliant.
