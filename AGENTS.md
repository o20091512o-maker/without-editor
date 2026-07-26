# AGENTS.md — Sticker Video Generator Project Rules

## ⚠️ TIME-CRITICAL MODE — 11-HOUR DEADLINE
This build is for a hackathon submission with a hard deadline today. Scope is
intentionally minimal. Do NOT add anything beyond what is listed below, even
if it seems like a quick improvement. Working end-to-end beats polished but broken.

## GENERAL PHILOSOPHY
1. Backend-first. Get one scene rendering end-to-end before touching styling.
2. Frontend is minimal from the start — clean but simple, no design system, no animations.
3. All project content (code, comments, UI text, error messages) is in English.
   The AI agent communicates with the developer in Arabic but never writes Arabic into the codebase.
4. On any unexpected error or ambiguous decision point: STOP and propose solutions.
   Do not silently "fix and continue" — always surface the issue first.

## COMMUNICATION STYLE
Speak like a caveman: minimum words, maximum useful signal. No filler, no
pleasantries, no restating the task back. Every reply should be short and
action-oriented. Example: "Image upload done. Testing now." not "Great, I've
successfully implemented the image upload endpoint and I'm now moving on to
testing it thoroughly." Maximize actual execution time, minimize talk time.

## MODULARITY RULE
- One feature = one file. Never merge logic from two different features into one file.
- Hard limit: no file exceeds 900 lines. If a file approaches this limit, split it
  into sub-modules before adding new code.
- Folder structure is fixed (see below) — do not introduce new top-level folders
  without flagging it first.

## FIXED FILE STRUCTURE
```
backend/
├── app.py
├── .env
├── services/
│   ├── tts.py              # edge-tts generation only
│   ├── alignment.py         # WhisperX calls (via Colab) only
│   ├── video_render.py       # Remotion subprocess calls only
│   └── job_manager.py         # in-memory job state only (no DB)
├── static/
│   ├── index.html
│   ├── app.js
│   └── style.css
├── remotion/
│   ├── Composition.tsx
│   └── Scene.tsx
├── temp/            # cleared/regenerated per session, never persisted long-term
└── outputs/
```

## BUILD ORDER — SINGLE TRACK, NO PHASES

### Step 1: One scene, end-to-end (highest priority — do this first, nothing else)
- [ ] Image upload endpoint (PNG/JPG, 10MB max — basic extension check is enough)
- [ ] Text input field only — NO audio file upload UI or endpoint of any kind
- [ ] edge-tts generation function: text → MP3
- [ ] WhisperX call to Colab endpoint → returns word-level JSON timestamps
- [ ] Remotion composition: gradient background + sticker image + glowing caption
      synced to word timings
- [ ] Single subprocess call: `npx remotion render` with props JSON → output MP4
- [ ] /api/generate endpoint wired for exactly ONE scene, /api/status, /api/download
- [ ] Minimal HTML page: image upload, text box, submit button, video result
- [ ] TEST THIS FULLY WORKING BEFORE ADDING ANYTHING ELSE

### Step 2: Multiple scenes (only after Step 1 works end-to-end)
- [ ] Allow adding 2–5 scenes (skip the 30-scene limit — not needed for the demo)
- [ ] Loop the Step 1 logic per scene, concatenate into one video
- [ ] Basic "add scene" / "remove scene" buttons on the page

### Step 3: Light polish (only if time remains — SKIP if deadline is close)
- [ ] Basic CSS: dark background, readable spacing, one accent color
- [ ] Progress text while rendering ("Generating audio...", "Rendering video...")

### Step 4 (STRETCH — only if Steps 1-3 are fully done with time to spare):
Second style: "Aged Paper" — a style selector lets the user pick Style 1
(sticker/gradient) or Style 2 (aged paper) per project.
- [ ] Static aged-paper background image (one fixed asset)
- [ ] Text renders letter-by-letter (not word-by-word) in a handwritten-style font
- [ ] Approximate per-letter timing: split each word's duration evenly across
      its character count (do not attempt precise per-letter alignment —
      word-level WhisperX timing is enough, just subdivide it)
- [ ] Typewriter sound effect plays per letter (use a free asset from
      Pixabay/Mixkit — do not generate this)
- [ ] Between scenes: insert a 1-2 second paper-crumple-then-unfold video clip
      (free stock asset — do not generate this)
- [ ] If this step is not finished in time, Style 1 alone is a complete,
      submittable product. Do not let Step 4 risk Steps 1-3.

## EXPLICITLY CUT FOR THIS DEADLINE (do not build, do not suggest)
- No MP3 upload / manual word-picker — text input only, always auto-generate audio
- No password gate, no rate limiting, no magic-number validation
- No 30-scene limit, no 10-minute cap, no drag-and-drop reordering
- No aspect ratio selector — hardcode 9:16
- No mobile-responsive design pass

## TESTING RULE
Test Step 1 manually (or via Playwright MCP if fast) the moment it's wired —
do not proceed to Step 2 until one real video has been generated successfully.

## COLAB / WHISPERX CONNECTION
- The Colab notebook is started manually by the developer once per work session
  (no fully-unattended "forever" uptime exists on the free tier — do not attempt
  to build automation that assumes otherwise).
- On every request to the alignment service: retry up to 3 times before
  returning a failure message to the user.
- Implement GET /api/health-colab: pings the stored ngrok URL, returns online/offline.
  Frontend checks this on page load and shows a clear banner if offline.

## AUDIO / WORD-TIMING LOGIC (CORE FEATURE — ONLY PATH)
1. User types the text for each scene (no audio upload option)
2. Generate audio for that scene's text via edge-tts → MP3
3. Send that audio to WhisperX (via Colab) → get word_timings JSON for that scene
4. Pass image + audio + word_timings to the Remotion composition for that scene
5. Scene duration = audio duration (from the word timings' last end_ms)

## SECURITY (MINIMAL — DEADLINE MODE)
- Enforce image size limit at the endpoint level: 10MB max
- Sanitize filenames before storage (strip path traversal characters, use
  UUID-based stored names)
- That's it for now — password gate, rate limiting, and magic-number
  validation are explicitly deferred (see EXPLICITLY CUT section above)

## LOGGING
- Temporary log file during active build/debug sessions only
- Not persisted long-term (cleared and regenerated), to avoid consuming
  storage on the free-tier host
- No permanent audit log required for this phase

## DEPLOYMENT TARGET
- Hugging Face Spaces (free tier)
- Flag immediately if Remotion's Node.js + headless Chromium rendering proves
  too resource-heavy on this tier — do not silently degrade quality or
  silently switch hosting without flagging it first

## OUT OF SCOPE FOR THIS BUILD (documented, not built)
- MP3 upload / manual word-picker (see EXPLICITLY CUT section)
- User accounts / auth / password gate
- Persistent database (in-memory job state is sufficient)
- Additional editing styles beyond the sticker-gradient template
- Automatic Colab session management beyond manual start + keep-alive loop
- Long-term log retention or analytics
- Rate limiting, magic-number file validation
