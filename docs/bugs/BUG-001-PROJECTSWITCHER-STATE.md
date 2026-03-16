# BUG-001: ProjectSwitcher Persists space.id Instead of project_id

**Type:** UI/State Bug  
**Severity:** Medium  
**Discovered:** 2026-03-16  
**Status:** Partially Fixed (commit b5a1a46)  

---

## Summary

The ProjectSwitcher component was persisting `space.id` (a UUID) to localStorage instead of `project_id` (the namespace). This caused the dashboard to query for a non-existent project namespace, making it appear empty.

---

## Root Cause

In `ProjectSwitcher.tsx`, when switching projects:
- The code saved `space.id` (UUID like `space_9fbfbc569932459b`)
- Should have saved `project_id` (namespace like `clawdbot` or `default`)

When the page reloaded, it tried to query memories for the UUID namespace, which doesn't exist.

---

## Fix Applied (b5a1a46)

Added UUID detection and reset logic:

```typescript
const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
if (savedProjectId && uuidPattern.test(savedProjectId)) {
  const matchesKnownProject = projectList.some((p) => p.namespace === savedProjectId);
  if (!matchesKnownProject) {
    console.warn(`Corrupted project ID detected (${savedProjectId}), resetting to 'default'`);
    savedProjectId = 'default';
    api.setProjectId('default');
  }
}
```

---

## Remaining Risk

The fix resets to `default`, but if the user's memories are in a different namespace (e.g., `clawdbot`), this still results in an empty dashboard. This is addressed by BUG-002.

---

## Acceptance Criteria

- [x] ProjectSwitcher detects corrupted UUID in localStorage
- [x] Corrupted values are reset (currently to `default`)
- [ ] Should reset to user's **active namespace**, not hardcoded `default` (see BUG-002)
- [ ] Switcher always persists `namespace`, never `space.id`

---

## Files

- `dashboard/src/components/ProjectSwitcher.tsx`
- `dashboard/src/lib/api.ts` (setProjectId/getProjectId)
