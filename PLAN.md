# WhisperX Transcriber — Marketing & Growth Implementation Plan

## Overview

This plan upgrades the repository from a developer-focused project into a
product-marketed open source tool. The goal is to drive installs, GitHub stars,
and community growth by improving how the project presents itself — without
changing any functionality.

---

## Phase 1 — Repository & README (Do First)

### 1.1 Rewrite README.md as a product landing page

The current README is excellent technically but written for developers.
Rewrite it so the **first screen** sells the product to non-technical users.

**New README structure:**

```
1. Hero section
   - Project name + one-line tagline
   - Three bold value props (badges/icons)
   - Screenshot (existing assets/screenshot.png)
   - Download button (link to Releases)

2. Why this exists (3-sentence narrative)
   - Who it's for and what problem it solves
   - The privacy/offline angle front and centre

3. Who is this for (keep existing section, move it up)

4. How it works (simple 3-step visual: Drop file → Choose model → Get transcript)

5. Feature highlights (icons + short lines, not walls of text)

6. Output formats table (keep existing)

7. Language support (keep existing)

8. Performance table CPU vs GPU (keep existing)

9. Models table (keep existing)

10. For Developers section (move to bottom — it's secondary)

11. Roadmap (keep, clean up)

12. Contributing (keep)

13. Sponsor / Support the project (NEW — see 1.4)

14. License
```

**Tone:** Confident, clear, user-first. Not "contribute to development" — that's
GitHub's auto-generated description. Lead with the user benefit.

---

### 1.2 Add GitHub repository metadata

In the GitHub repo Settings (Claude Code cannot do this — flag for manual action):

- **Description:** `Offline AI transcription for Windows. Word-level timestamps. No cloud. No subscription. Free forever.`
- **Website:** (add once landing page exists, or link to Releases for now)
- **Topics to add:**
  ```
  whisper whisperx speech-to-text transcription subtitles
  offline-ai privacy windows-app audio-transcription
  faster-whisper word-timestamps srt vtt
  ```

---

### 1.3 Add FUNDING.yml (GitHub Sponsors button)

Create `.github/FUNDING.yml`:

```yaml
github: ibrahimqureshae
```

This adds the ❤️ Sponsor button to the repo immediately. Also add a Sponsors
section at the bottom of the README with a brief "why sponsoring helps" message.

---

### 1.4 Add social preview image (OG image)

Create `assets/social-preview.png` — a 1280×640px image used when the repo
link is shared on Twitter/LinkedIn/Reddit. Should show:
- App name + tagline
- Key features in 3 bullet points
- Screenshot of the app UI

This can be created as an SVG and exported, or designed in Figma/Canva.
Claude Code should generate an HTML/SVG version that can be screenshotted.

---

### 1.5 Add a demo GIF to README

Record or generate a GIF showing:
1. User drags a file into the app (or clicks Files button)
2. Progress bar runs
3. SRT output appears

Place it near the top of the README, just below the tagline.
Name it `assets/demo.gif`.

If recording isn't possible now, add a placeholder comment in the README:
`<!-- TODO: Add demo GIF here -->`

---

## Phase 2 — GitHub Pages Landing Page

### 2.1 Create `docs/index.html`

Enable GitHub Pages (Settings → Pages → Source: `main` branch, `/docs` folder).

The landing page should be a single HTML file with:

```
Header:
  - Logo / app name
  - Tagline: "Offline AI transcription. No cloud. No subscription."
  - [Download for Windows] CTA button → links to latest release zip
  - Sub-text: "Free forever · Open source · Privacy-first"

Hero section:
  - Screenshot of the app

3 feature pillars (icon + heading + 2 sentences each):
  - 🔒 100% Private — audio never leaves your machine
  - ⚡ Word-level timestamps — every word precisely timed
  - 🌐 99 languages — including Arabic, Urdu, Persian, and more

How it works (3 steps):
  1. Download & extract (no installer needed)
  2. Run setup wizard (one-time, downloads AI engine)
  3. Transcribe anything — works offline forever

Who uses this:
  - Journalists  |  Content creators  |  Researchers
  - Translators  |  Students  |  Privacy-conscious users

Output formats:
  SRT · VTT · TXT · TSV · JSON · Word JSON

Footer:
  - GitHub link
  - License: MIT
  - Sponsor link
```

**Tech:** Plain HTML + CSS. No frameworks. Must load fast and look clean.
Use system fonts. Dark/light mode via `prefers-color-scheme`.

---

## Phase 3 — Community & Distribution Files

### 3.1 Add `.github/ISSUE_TEMPLATE/` directory

Create two templates:

**bug_report.md:**
```markdown
---
name: Bug report
about: Something isn't working
---

**Describe the bug**

**Steps to reproduce**

**Expected behavior**

**Log output** (click Log in the sidebar and paste here)

**System info**
- Windows version:
- GPU (if any):
- Model used:
- File format:
```

**feature_request.md:**
```markdown
---
name: Feature request
about: Suggest an improvement
---

**What problem does this solve?**

**Describe the feature**

**Who would benefit from this?**
```

---

### 3.2 Add CHANGELOG.md

Start a changelog to build trust and show active development:

```markdown
# Changelog

## v1.0.0 — 2026-06-07

### Added
- Full GUI desktop app for Windows
- Setup wizard with automatic GPU detection
- Support for 17 languages in GUI, 99 via CLI
- Word-level timestamp alignment
- Export to SRT, VTT, TXT, TSV, JSON, Word JSON
- CPU and GPU (CUDA) support
- Offline operation after one-time setup
- VAD (Voice Activity Detection) silence stripping
- Karaoke-style word-highlighted subtitles
```

---

### 3.3 Add CONTRIBUTING.md (expanded)

The current contributing section in README is good but should be its own file
for GitHub to surface it automatically on new issues and PRs.

Move the contributing section to `CONTRIBUTING.md` and expand with:
- Development environment setup (already in README, copy it)
- Coding style notes
- How to test changes
- PR checklist

---

### 3.4 Add a short SECURITY.md

```markdown
# Security

If you discover a security vulnerability, please open a GitHub issue
or email directly rather than disclosing publicly.

Note: WhisperX Transcriber runs entirely locally. It makes no network
requests during normal operation (only during first-run setup to download
the AI engine). There is no server, no API, and no telemetry.
```

---

## Phase 4 — README Polish Details

### 4.1 Badges to add at the top of README

```markdown
![License](https://img.shields.io/github/license/ibrahimqureshae/whisperx-transcriber)
![Release](https://img.shields.io/github/v/release/ibrahimqureshae/whisperx-transcriber)
![Platform](https://img.shields.io/badge/platform-Windows-blue)
![Offline](https://img.shields.io/badge/works-offline-green)
![No subscription](https://img.shields.io/badge/subscription-none-brightgreen)
```

### 4.2 Fix the repo description

Current GitHub auto-description: "Contribute to ibrahimqureshae/whisperx-transcriber
development by creating an account on GitHub." — this is the default and actively
hurts first impressions. Must be changed manually in repo Settings.

### 4.3 Add a "Used by" or "Built for" section

Even without real user data, list the intended audiences with icons:
```
🎙️ Journalists  📹 Content creators  🔬 Researchers
📚 Students     🌍 Translators       🔒 Privacy-conscious users
```

---

## Deliverables Checklist

| File | Action | Priority |
|------|--------|----------|
| `README.md` | Full rewrite (marketing-first) | 🔴 Critical |
| `.github/FUNDING.yml` | Create (Sponsors button) | 🔴 Critical |
| `docs/index.html` | Create (GitHub Pages landing page) | 🟠 High |
| `CHANGELOG.md` | Create | 🟠 High |
| `CONTRIBUTING.md` | Extract + expand from README | 🟡 Medium |
| `SECURITY.md` | Create | 🟡 Medium |
| `.github/ISSUE_TEMPLATE/bug_report.md` | Create | 🟡 Medium |
| `.github/ISSUE_TEMPLATE/feature_request.md` | Create | 🟡 Medium |
| `assets/social-preview.png` | Create or generate | 🟡 Medium |
| `assets/demo.gif` | Record or placeholder | 🟢 Low |

---

## Manual Actions Required (Claude Code Cannot Do These)

These require direct GitHub UI access:

1. **Repo description** — Settings → Edit → paste new description
2. **Topics** — Settings → Topics → add all listed topics
3. **GitHub Pages** — Settings → Pages → enable from `/docs` folder
4. **Social preview image** — Settings → Social preview → upload `assets/social-preview.png`
5. **GitHub Sponsors** — must be set up at github.com/sponsors/ibrahimqureshae

---

## Notes for Claude Code

- Do not modify `app.py`, `transcribe.py`, `setup_wizard.py`, or any Python files
- Do not modify `requirements-*.txt` files
- Only create/modify documentation, metadata, and web files
- Preserve all existing technical accuracy — do not change version numbers,
  model names, language codes, or feature descriptions
- The MIT license must remain unchanged
- Keep all existing content — this is a restructure and expansion, not a replacement
