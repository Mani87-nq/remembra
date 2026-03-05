# Remembra Dashboard - Fix Report

**Date:** March 5, 2026  
**Analyst:** Dashboard Doctor Subagent  
**Dashboard URL:** https://app.remembra.dev  
**API URL:** https://api.remembra.dev

---

## Executive Summary

The Remembra dashboard at `app.remembra.dev` is **largely functional** with all major features working. One **critical pricing bug** was identified that needs immediate attention.

### Overall Status: ✅ MOSTLY WORKING

| Feature | Status | Notes |
|---------|--------|-------|
| Login | ✅ Working | JWT authentication functional |
| Signup | ✅ Working | Account creation successful |
| Dashboard UI | ✅ Working | All tabs render correctly |
| API Keys | ✅ Working | Create, view, delete working |
| Billing Page | ✅ Working | Usage stats display correctly |
| Stripe Checkout | ⚠️ Price Mismatch | See Critical Bug #1 |
| Settings | ✅ Working | Profile editing works |
| API Communication | ✅ Working | CORS configured correctly |

---

## Critical Bug #1: Stripe Price Mismatch 🚨

### Problem
The billing page displays **$49/month for Pro** plan, but the actual Stripe checkout shows **$29/month**.

### Evidence
- Dashboard Billing.tsx hardcodes: `<span>$49</span>/month`
- Stripe price ID in `plans.py`: `price_1T6ZDAQ3CqXwAZA7jUWCVVF0`
- Actual Stripe checkout shows: $29.00/month

### Impact
- **Customer confusion** - they expect $49, get charged $29
- **Revenue impact** - Either undercharging or displaying wrong price
- **Trust issue** - Price inconsistency looks unprofessional

### Root Cause
The `stripe_price_id` in `/src/remembra/cloud/plans.py` points to a $29 price, but the frontend displays $49.

### Fix Options

**Option A: Update Stripe to match dashboard (charge $49)**
1. Create new Stripe price at $49/month in Stripe Dashboard
2. Update `plans.py`:
```python
# Pro plan
stripe_price_id="price_NEW_49_DOLLAR_PRICE_ID",  # $49/mo
```

**Option B: Update dashboard to match Stripe (charge $29)**
1. Update `Billing.tsx` line ~92:
```tsx
price="$29"
```
2. Update the feature comparison table header

### Recommended: Option A
Keep the $49 pricing as intended in the product spec.

---

## Test Results

### 1. Authentication Flow ✅

| Test | Result |
|------|--------|
| New user signup | ✅ Pass |
| Login with email/password | ✅ Pass |
| JWT token validation | ✅ Pass |
| Logout | ✅ Pass |
| Session persistence | ✅ Pass |

### 2. API Communication ✅

| Test | Result |
|------|--------|
| CORS headers | ✅ Configured for app.remembra.dev |
| /api/v1/auth/me | ✅ Returns user data |
| /api/v1/cloud/plan | ✅ Returns plan info |
| /api/v1/keys | ✅ CRUD operations work |

### 3. Billing Flow ⚠️

| Test | Result |
|------|--------|
| Usage display | ✅ Correct counters |
| Plan comparison table | ✅ Renders correctly |
| "Upgrade to Pro" button | ✅ Creates Stripe session |
| Stripe redirect | ⚠️ Redirects but wrong price |
| Payment options | ✅ Card, Cash App, Klarna, Link |

### 4. API Key Management ✅

| Test | Result |
|------|--------|
| View keys (empty state) | ✅ Pass |
| Create new key | ✅ Pass |
| Key appears in list | ✅ Pass |
| Permission levels | ✅ Admin/Editor/Viewer |

### 5. Settings ✅

| Test | Result |
|------|--------|
| View profile | ✅ Pass |
| Edit display name | ✅ Pass |
| Email (read-only) | ✅ Correctly disabled |

---

## Architecture Review

### Frontend (dashboard/)
- **Framework:** React 19 + TypeScript + Vite
- **Styling:** Tailwind CSS 4
- **Build:** Vite with Docker/nginx for production
- **API URL:** Correctly configured via `VITE_API_URL=https://api.remembra.dev`

### Backend (src/remembra/)
- **Framework:** FastAPI
- **Auth:** JWT tokens + API keys
- **Billing:** Stripe integration
- **Deployed:** Coolify on 178.156.226.84

### Configuration Files
- `dashboard/src/config.ts` - API URL configuration ✅
- `dashboard/src/lib/api.ts` - API client ✅
- `src/remembra/cloud/plans.py` - Plan definitions (price mismatch here)
- `src/remembra/cloud/billing.py` - Stripe integration ✅

---

## No Issues Found

The following previously suspected issues were **NOT present**:

1. ❌ **API URL pointing to wrong endpoint** - WORKING
   - Dashboard correctly hits `api.remembra.dev/api/v1/*`
   - No evidence of `app.remembra.dev/api` misrouting

2. ❌ **CORS errors** - WORKING
   - `app.remembra.dev` is in CORS allowed origins
   - No browser console errors

3. ❌ **Authentication broken** - WORKING
   - Both signup and login functional
   - JWT tokens properly validated

4. ❌ **Stripe keys not configured** - WORKING
   - Checkout sessions created successfully
   - Redirect to Stripe works

---

## Recommendations

### Immediate (P0)
1. **Fix Stripe price mismatch** - Create $49 price in Stripe Dashboard and update `plans.py`

### Short-term (P1)
2. **Add Stripe webhook secret** - Currently commented out in .env
3. **Test webhook flow** - Ensure plan upgrades persist after payment

### Nice-to-have (P2)
4. **Add loading states** - Some buttons could use better loading feedback
5. **Add error toasts** - Show user-friendly error messages

---

## Files Changed/Reviewed

### Reviewed (No Changes Needed)
- `/dashboard/src/config.ts` ✅
- `/dashboard/src/lib/api.ts` ✅
- `/dashboard/src/components/Billing.tsx` ✅
- `/dashboard/src/pages/Login.tsx` ✅
- `/dashboard/src/pages/Signup.tsx` ✅
- `/dashboard/src/App.tsx` ✅

### Needs Update
- `/src/remembra/cloud/plans.py` - Update `stripe_price_id` for Pro plan

---

## Test User Created

For future testing:
- **Email:** test-dashboard-doctor@dolphytech.com
- **Password:** TestPass123!
- **API Key:** Created "Test Key for Dashboard Doctor" (Editor permission)

---

## Conclusion

The Remembra dashboard is production-ready with one critical fix needed: **update the Stripe price ID to match the $49/month displayed price**. All other functionality (auth, API keys, settings, usage tracking) is working correctly.

The dashboard correctly communicates with `api.remembra.dev` and there are no API routing issues. The previous concern about hitting `app.remembra.dev/api` instead of `api.remembra.dev` is not present in the current deployment.
