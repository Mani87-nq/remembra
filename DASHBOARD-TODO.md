# Remembra Dashboard - SaaS Features TODO

## Overview
Building out the full SaaS dashboard at app.remembra.dev

## Features to Build

### 1. API Key Management (Priority: HIGH)
- [ ] List all API keys for user
- [ ] Create new API key with name/description
- [ ] Copy key to clipboard (show once on creation)
- [ ] Revoke/delete API keys
- [ ] Set permissions per key (admin/editor/viewer)
- [ ] Show last used timestamp
- [ ] Rate limit info per key

### 2. User Authentication (Priority: HIGH)
- [ ] Sign up page (email + password)
- [ ] Login page
- [ ] Password reset flow
- [ ] Email verification
- [ ] OAuth (GitHub, Google) - optional
- [ ] Session management

### 3. Billing & Subscription (Priority: HIGH)
- [ ] Stripe integration
- [ ] Display current plan (Free/Pro/Enterprise)
- [ ] Usage meters (memories, API calls)
- [ ] Upgrade/downgrade flows
- [ ] Invoice history
- [ ] Payment method management

### 4. Settings Panel (Priority: MEDIUM)
- [ ] Account settings (name, email)
- [ ] Change password
- [ ] Delete account
- [ ] Notification preferences
- [ ] Webhook configuration

### 5. Team Management (Priority: LOW)
- [ ] Invite team members
- [ ] Role assignment
- [ ] Remove members
- [ ] Organization settings

## Tech Stack
- Frontend: React + TypeScript + Tailwind (existing)
- Backend: FastAPI (existing)
- Auth: FastAPI + JWT or Auth0
- Billing: Stripe

## API Endpoints Needed
- POST /api/v1/auth/signup
- POST /api/v1/auth/login
- POST /api/v1/auth/logout
- POST /api/v1/auth/reset-password
- GET /api/v1/keys - List API keys
- POST /api/v1/keys - Create API key
- DELETE /api/v1/keys/{id} - Revoke key
- GET /api/v1/billing/subscription
- POST /api/v1/billing/checkout
- GET /api/v1/billing/usage

## Stripe Config
- Publishable Key: (see environment variables)
- Secret Key: (see environment variables)
- Product: Remembra Pro Cloud ($49/mo)
