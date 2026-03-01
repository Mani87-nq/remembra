# Release Checklist

**MANDATORY before ANY PyPI deployment**

## Pre-Release Verification

- [ ] All tests pass locally (`pytest tests/ -v`)
- [ ] No test failures or errors
- [ ] Server starts without errors (`uv run remembra`)
- [ ] Health check passes (`curl localhost:8787/health`)
- [ ] Core features tested manually:
  - [ ] Store a memory
  - [ ] Recall memories
  - [ ] Forget works
- [ ] New features tested manually (whatever was added this version)
- [ ] CHANGELOG.md updated
- [ ] Version bumped in pyproject.toml

## Deploy Only After ALL Checks Pass

```bash
# 1. Run tests
pytest tests/ -v

# 2. Start server and test
uv run remembra &
curl localhost:8787/health

# 3. Manual smoke test
./scripts/mem store "test memory"
./scripts/mem recall "test"

# 4. Only then build and deploy
python -m build
twine upload dist/*
```

## Post-Deploy Verification

- [ ] PyPI page shows correct version
- [ ] Fresh install works (`pip install remembra==X.Y.Z`)
- [ ] Server runs with fresh install

---

**NO SHORTCUTS. Test before deploy.**
