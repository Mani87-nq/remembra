# Remembra Demo Video — Full Production Guide

## Overview
- **Length:** 60 seconds
- **Format:** Terminal recording + voiceover
- **Style:** Clean, developer-focused, fast-paced
- **Music:** Lo-fi or minimal electronic (low volume)

---

## TIMELINE + SHOT LIST

### 0:00-0:05 — HOOK
**VISUAL:** Black screen → fade in text: "Your AI forgets everything."
**VOICEOVER:** "Your AI forgets everything between sessions. Let's fix that."
**MUSIC:** Starts soft

---

### 0:05-0:12 — SETUP  
**VISUAL:** Terminal appears, clean dark theme
```
$ pip install remembra
```
Then:
```python
>>> from remembra import Memory
>>> memory = Memory(base_url="...", user_id="demo")
✓ Connected
```
**VOICEOVER:** "Remembra gives your AI persistent memory. Install in seconds."

---

### 0:12-0:28 — STORE MEMORIES
**VISUAL:** Terminal showing stores with checkmarks
```python
>>> memory.store("John is the CEO of Acme Corp")
    ✓ Stored | Facts: ['John is the CEO of Acme Corp']

>>> memory.store("John started in January 2024")
    ✓ Stored | Facts: ['John started in January 2024']

>>> memory.store("Acme Corp is in San Francisco")
    ✓ Stored | Facts extracted ✓
```
**VOICEOVER:** "Store information in plain English. Remembra automatically extracts entities, facts, and relationships. No schemas. No setup."

---

### 0:28-0:45 — SEMANTIC RECALL (THE MONEY SHOT)
**VISUAL:** 
```python
>>> memory.recall("What do I know about John?")
```
Pause for effect, then result appears:
```
┌────────────────────────────────────────────────┐
│ John is the CEO of Acme Corp since January    │
│ 2024. Acme Corp is headquartered in San       │
│ Francisco.                                     │
└────────────────────────────────────────────────┘

📊 Found 3 relevant memories
    [95%] John is the CEO of Acme Corp
    [88%] John started in January 2024
    [82%] Acme Corp is in San Francisco
```
**VOICEOVER:** "Ask anything in natural language. Semantic search finds relevant memories and synthesizes context. Your AI finally has long-term memory."

---

### 0:45-0:52 — MCP INTEGRATION
**VISUAL:** Quick cut to Claude Desktop with Remembra in the MCP tools list
Or show config snippet:
```json
{
  "mcpServers": {
    "remembra": {
      "command": "uvx",
      "args": ["remembra-mcp"]
    }
  }
}
```
**VOICEOVER:** "Works natively with Claude Desktop via MCP. One line config."

---

### 0:52-0:60 — CTA
**VISUAL:** Clean slide with:
```
⭐ github.com/[ORG]/remembra

pip install remembra

Memory for AI. Finally.
```
**VOICEOVER:** "Star us on GitHub. Ship memory today."
**MUSIC:** Fades out

---

## RECORDING INSTRUCTIONS

### Terminal Recording
```bash
# Option 1: asciinema (best for terminal)
brew install asciinema
cd /Users/dolphy/Projects/remembra
asciinema rec demo.cast --cols 80 --rows 24
uv run python demo/demo_recording.py
# Ctrl+D when done
# Convert to video: 
asciinema-agg demo.cast demo.gif

# Option 2: Screen record with OBS/QuickTime
# - Set terminal to 80x24
# - Use 24pt font minimum
# - Dark theme (Dracula, One Dark, etc.)
```

### Voiceover Recording
- Quiet room, close to mic
- Confident, slightly fast pace
- Technical but friendly
- Record each section separately for easy editing

### Editing
- Use CapCut, DaVinci Resolve, or Final Cut
- Sync voiceover to terminal actions
- Add subtle zoom on key moments (recall result)
- Music at 10-15% volume

---

## VOICEOVER SCRIPT (FULL)

[Read naturally, ~150 words per minute]

---

**[0:00]** Your AI forgets everything between sessions. Let's fix that.

**[0:06]** Remembra gives your AI persistent memory. Install in seconds.

**[0:12]** Store information in plain English. Remembra automatically extracts entities, facts, and relationships. No schemas. No setup.

**[0:28]** Ask anything in natural language. Semantic search finds relevant memories and synthesizes context. Your AI finally has long-term memory.

**[0:45]** Works natively with Claude Desktop via MCP. One line config.

**[0:52]** Star us on GitHub. Ship memory today.

---

## FILES IN THIS FOLDER
- `PRODUCTION_GUIDE.md` — This file
- `demo_recording.py` — Live terminal demo script
- `voiceover.mp3` — Generated voiceover (if created)
- `demo.cast` — asciinema recording (after recording)
- `final_video.mp4` — Final output (after editing)

---

## CHECKLIST
- [ ] Terminal theme set (dark)
- [ ] Font size 24pt+
- [ ] asciinema installed
- [ ] Voiceover recorded
- [ ] Music track selected
- [ ] Video edited
- [ ] Uploaded to YouTube/Twitter
