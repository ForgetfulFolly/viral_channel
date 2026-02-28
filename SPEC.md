# Last SiX Hours -- Full Technical Specification

**Version:** 1.0
**Date:** February 28, 2026
**Status:** Draft

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture Overview](#2-architecture-overview)
3. [Infrastructure & Deployment](#3-infrastructure--deployment)
4. [Module Specifications](#4-module-specifications)
   - 4.1 Discovery Engine
   - 4.2 Video Acquisition
   - 4.3 Scene Analysis & Clip Extraction
   - 4.4 Script Generation
   - 4.5 Text-to-Speech Engine
   - 4.6 Video Assembly & Rendering
   - 4.7 Thumbnail Generation
   - 4.8 YouTube Upload & Metadata
   - 4.9 Shorts Generator
   - 4.10 Telegram Review Bot
   - 4.11 Scheduler & Orchestrator
   - 4.12 Analytics & Feedback Loop
5. [Data Flow & Pipeline](#5-data-flow--pipeline)
6. [Database Schema](#6-database-schema)
7. [Configuration System](#7-configuration-system)
8. [LLM Abstraction Layer](#8-llm-abstraction-layer)
9. [TTS Abstraction Layer](#9-tts-abstraction-layer)
10. [Multi-Channel Strategy](#10-multi-channel-strategy)
11. [Copyright & Monetization Compliance](#11-copyright--monetization-compliance)
12. [Error Handling & Monitoring](#12-error-handling--monitoring)
13. [File & Folder Structure](#13-file--folder-structure)
14. [API Keys & External Services](#14-api-keys--external-services)
15. [Implementation Phases](#15-implementation-phases)
16. [Design Principles](#16-design-principles)

---

## 1. Project Overview

### 1.1 Concept

"Last SiX Hours" is a fully automated YouTube content pipeline that discovers the most viral videos across YouTube within the prior 6-hour window, extracts peak moments, generates news-anchor-style narration, assembles polished compilation videos, and uploads them to YouTube -- all with human approval via Telegram before any upload goes live.

### 1.2 Goals

- Produce 8-10 minute long-form compilation videos, 4 times per day per niche channel
- Generate 3-5 YouTube Shorts per long-form video
- Operate across 2-4 niche-specific YouTube channels simultaneously
- Target 12-16 long-form uploads and 48-64 Shorts uploads per day total
- Achieve YouTube Partner Program eligibility on each channel
- Maintain near-zero monthly operating cost by running entirely on local infrastructure
- Every upload must be approved by a human via Telegram before publishing
- All components must be model-agnostic and configurable -- no hardcoded model names

### 1.3 Output Format

**Long-form video structure (8-10 minutes):**

```
[Branded Intro]              -- 3-5 seconds
[Anchor Introduction]        -- 15-20 seconds, sets the scene
[Clip #N + Commentary]       -- Countdown from N to 1 (N = 8-10 clips)
[Clip #N-1 + Commentary]
...
[Clip #1 + Commentary]       -- The most viral moment, saved for last
[Recap + Outro + CTA]        -- 15-20 seconds, subscribe prompt
```

Each clip segment consists of:
- Anchor narration introducing the clip (5-10 seconds)
- The clip itself (15-25 seconds)
- Brief anchor commentary after the clip (3-5 seconds)
- Transition graphic to next clip

**Shorts structure (30-60 seconds):**

```
[Hook text overlay]          -- First 1 second, grabs attention
[Clip with context overlay]  -- 20-40 seconds
[Channel branding + CTA]     -- 2-3 seconds
```

### 1.4 Constraints

- No emojis in any output, code, messages, metadata, or documentation
- No hardcoded model names anywhere in the codebase
- All LLM and TTS interactions go through abstraction layers
- All external API integrations must have configurable endpoints
- Human approval required before every YouTube upload
- Individual source clips must not exceed 25 seconds
- Narration must constitute at least 60% of total video audio duration
- Every source creator must be credited in the video description

---

## 2. Architecture Overview

### 2.1 High-Level Architecture

```
+-------------------+     +-------------------+     +-------------------+
|                   |     |                   |     |                   |
|  DISCOVERY ENGINE |---->| VIDEO ACQUISITION |---->|  SCENE ANALYSIS   |
|                   |     |                   |     |  & CLIP EXTRACT   |
+-------------------+     +-------------------+     +-------------------+
                                                            |
                                                            v
+-------------------+     +-------------------+     +-------------------+
|                   |     |                   |     |                   |
|   VIDEO ASSEMBLY  |<----|    TTS ENGINE     |<----|  SCRIPT GENERATOR |
|   & RENDERING     |     |                   |     |                   |
+-------------------+     +-------------------+     +-------------------+
        |
        v
+-------------------+     +-------------------+     +-------------------+
|                   |     |                   |     |                   |
| THUMBNAIL GEN     |---->| TELEGRAM REVIEW   |---->| YOUTUBE UPLOAD    |
|                   |     |    BOT            |     |                   |
+-------------------+     +-------------------+     +-------------------+
        |                                                   |
        v                                                   v
+-------------------+                             +-------------------+
|                   |                             |                   |
| SHORTS GENERATOR  |---------------------------->| ANALYTICS &       |
|                   |                             | FEEDBACK LOOP     |
+-------------------+                             +-------------------+
```

### 2.2 Component Communication

All modules communicate through:
- A shared SQLite database for state management
- A filesystem-based working directory for media artifacts
- An internal event/task queue (Python asyncio or Redis if scaling is needed later)

### 2.3 Execution Model

The pipeline runs as a single Python application with an async event loop. Each 6-hour cycle triggers a full pipeline run for each configured channel/niche. Multiple niche pipelines can run concurrently with resource limits enforced by the orchestrator.

---

## 3. Infrastructure & Deployment

### 3.1 Server

Host: Dell PowerEdge XC740XD (see XC740XD_Architecture_LLM_Analysis.md for full specs)

Key resources available:
- 52 cores / 104 threads (Dual Xeon Platinum 8270)
- 320GB RAM (upgradeable to 768GB)
- 4x NVIDIA RTX 4000 Ada (80GB VRAM total)
- 169TB usable storage (NVMe + ZFS)
- Dual 10GbE networking
- Proxmox VE hypervisor

### 3.2 VM Allocation

Create a dedicated Proxmox VM for this project:

```
VM Name:        viral-channel
vCPUs:          8 (expandable to 16 if needed)
RAM:            32GB
OS:             Ubuntu 24.04 LTS (or Debian 12)
Storage:
  - Boot:       50GB on Tier 0 (NVMe RAID1)
  - Working:    500GB on Tier 1 (Landing Zone NVMe)
  - Archive:    Mount Tier 2 Data Lake via NFS/CIFS
GPU:            1x RTX 4000 Ada passthrough (for TTS inference)
Network:        Bridged to 10GbE
```

The working storage on Tier 1 NVMe handles all active downloads, renders, and temporary files. Completed videos and source archives migrate to Tier 2 Data Lake.

### 3.3 Software Dependencies

**System packages:**
- Python 3.11+
- FFmpeg (built with libx264, libx265, libvpx, libfdk-aac)
- yt-dlp
- Git

**Python packages (core):**
- httpx or aiohttp -- async HTTP client
- yt-dlp -- video downloading (Python API)
- moviepy or ffmpeg-python -- video composition
- Pillow -- image generation (thumbnails)
- python-telegram-bot -- Telegram integration
- google-api-python-client -- YouTube Data API v3
- google-auth-oauthlib -- YouTube OAuth
- praw -- Reddit API
- openai -- LLM client (OpenAI-compatible, works with local endpoints)
- sqlalchemy -- database ORM
- pydantic -- configuration and data validation
- apscheduler -- job scheduling
- jinja2 -- script templating
- numpy -- audio analysis
- librosa -- audio feature extraction (optional, for scene analysis)

**Python packages (TTS):**
- TTS (Coqui TTS / XTTS v2)
- Additional TTS engines as configured

**Python packages (optional/future):**
- torch -- for local model inference
- transformers -- Hugging Face model loading
- faster-whisper -- speech-to-text for source video transcription

### 3.4 Container Strategy (Optional)

Each major component can optionally run in a Docker container for isolation:

```
viral-channel-core        -- Main pipeline, orchestrator, scheduler
viral-channel-tts         -- TTS inference server (GPU access)
viral-channel-telegram    -- Telegram bot (lightweight, always-on)
```

For MVP, a single Python process is sufficient. Containerize later if isolation or scaling is needed.

---

## 4. Module Specifications

### 4.1 Discovery Engine

**Purpose:** Find the most viral videos across YouTube in the last 6 hours.

**Sources (prioritized):**

1. **YouTube Data API -- Trending/Most Popular**
   - Endpoint: `videos.list` with `chart=mostPopular`
   - Regionalized (US, UK, etc.)
   - Returns up to 200 videos per region
   - Lightweight quota cost (1 unit per call)

2. **YouTube Data API -- Search by view velocity**
   - Search for recent uploads (last 6-12 hours)
   - Track view counts at T+0, T+1h, T+2h, T+3h
   - Compute velocity: `(views_now - views_earlier) / hours_elapsed`
   - Videos with velocity above threshold are candidates
   - Quota cost: 100 units per search call

3. **Reddit**
   - Subreddits: r/videos, r/popular, r/gaming, r/sports, r/funny, r/nextfuckinglevel, r/unexpected, plus niche-specific subs
   - Filter: posts with YouTube links, sorted by hot/rising
   - Score threshold: configurable per subreddit
   - Library: PRAW (Python Reddit API Wrapper)

4. **Social aggregators (future expansion)**
   - Twitter/X API (if cost-effective)
   - Google Trends
   - Custom RSS feeds

**Scoring algorithm:**

Each discovered video receives a composite score:

```
viral_score = (
    w1 * view_velocity_normalized +
    w2 * reddit_score_normalized +
    w3 * like_ratio +
    w4 * comment_velocity_normalized +
    w5 * recency_factor
)
```

Weights (w1-w5) are configurable and adjusted by the analytics feedback loop over time.

**Niche classification:**

Each video is classified into one or more niches using:
- YouTube category ID (from API metadata)
- Keyword matching on title/description/tags
- LLM classification (send title + description to LLM, get niche label)

**Deduplication:**

- Track all discovered video IDs in the database
- Never process the same video twice
- Similarity detection: flag videos that are reuploads/mirrors of the same content (title similarity, duration match, thumbnail hash)

**Output:** A ranked list of candidate videos per niche, each with:
- Video ID, URL, title, channel name, channel ID
- View count, like count, comment count at discovery time
- View velocity estimate
- Niche classification
- Viral score
- Discovery source (YouTube trending, Reddit, etc.)

**Rate limiting:**
- YouTube API: Stay within 10,000 quota units/day (free tier) or allocated quota
- Reddit API: 60 requests/minute (PRAW handles this)
- Stagger discovery runs across niches to spread API usage

---

### 4.2 Video Acquisition

**Purpose:** Download source videos for processing.

**Tool:** yt-dlp (Python API, not subprocess)

**Download configuration:**

```python
yt_dlp_options = {
    "format": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
    "merge_output_format": "mp4",
    "outtmpl": "{working_dir}/downloads/{video_id}.%(ext)s",
    "writesubtitles": True,
    "writeautomaticsub": True,
    "subtitleslangs": ["en"],
    "subtitlesformat": "json3",
    "socket_timeout": 30,
    "retries": 3,
    "noplaylist": True,
}
```

**Key behaviors:**
- Download up to 1080p (sufficient quality, manageable file sizes)
- Always fetch subtitles/captions (needed for scene analysis)
- Download to Tier 1 NVMe working directory for fast I/O
- Skip download if video already exists locally
- Respect rate limits -- max 3 concurrent downloads
- Timeout and retry logic for flaky connections
- Validate downloaded file (check duration, codec, resolution)

**Storage management:**
- Downloaded source videos are temporary
- Delete source files after clips are extracted and video is rendered
- Archive only the final output to Tier 2

**Output per video:**
- MP4 file at up to 1080p
- Subtitle/caption file (JSON3 format)
- Metadata JSON (title, channel, duration, resolution)

---

### 4.3 Scene Analysis & Clip Extraction

**Purpose:** Identify the most engaging 15-25 second segment from each source video.

**Methods (applied in priority order):**

**Method 1: YouTube Most Replayed Heatmap**
- Scrape the most-replayed data from the YouTube player page
- This data shows which segments viewers rewatch most
- Extract the peak segment (highest replay intensity)
- This is the single best signal for "what's the best part"
- Implementation: HTTP request to the video page, parse the `playerOverlayRenderer` JSON

**Method 2: Transcript/Caption Analysis**
- Parse the downloaded subtitle file
- Send transcript to the LLM with prompt:
  ```
  Given this video transcript, identify the single most dramatic,
  surprising, or entertaining moment. Return the start and end
  timestamps in seconds.
  
  Title: {title}
  Transcript: {transcript}
  ```
- LLM returns timestamp range

**Method 3: Audio Energy Analysis**
- Extract audio track from video
- Compute RMS energy over sliding windows
- Identify spikes (crowd reactions, shouting, music drops, laughter)
- Select the window around the highest energy spike
- Libraries: librosa or numpy on raw audio

**Method 4: Scene Change Detection (fallback)**
- Use FFmpeg scene detection filter
- Identify visually dynamic segments (lots of cuts = action)
- Combined with audio energy for better accuracy

**Clip extraction:**
- Once the target timestamp range is identified, use FFmpeg to extract the clip
- Re-encode to consistent format: H.264, 1080p, 30fps, AAC audio
- Normalize audio levels across all clips (FFmpeg loudnorm filter)
- Trim to 15-25 seconds maximum
- Add 0.5s fade-in and fade-out

**Output per clip:**
- MP4 clip file (15-25 seconds, normalized)
- Clip metadata: source video ID, start/end timestamps, extraction method used
- Transcript snippet for the clipped segment

---

### 4.4 Script Generation

**Purpose:** Generate news-anchor-style narration for the entire compilation video.

**LLM interaction:** All calls go through the LLM abstraction layer (Section 8).

**Script structure:**

The LLM receives a structured prompt with all clip metadata and generates a complete script:

```
System prompt:
You are a scriptwriter for a YouTube channel called "Last SiX Hours"
that covers the most viral videos from the past 6 hours. Write in the
style of a fast-paced, engaging news anchor. Be energetic but not
over-the-top. No emojis. No profanity. Keep sentences short and punchy.
Each clip introduction should hook the viewer and provide brief context.

User prompt:
Write a complete script for a video titled "{title}".
This is the {niche} edition covering the 6-hour window ending at {time}.

Here are the clips in countdown order (highest to 1):

Clip 10:
- Source: "{video_title}" by {channel_name}
- Views: {view_count} in {hours} hours
- Clip transcript: "{transcript_snippet}"
- Context: {brief_description}

Clip 9:
...

For each clip, write:
1. INTRO: A 2-3 sentence introduction (spoken before the clip plays)
2. OUTRO: A 1 sentence reaction/commentary (spoken after the clip)

Also write:
- OPENING: A 3-4 sentence channel introduction for the start of the video
- CLOSING: A 2-3 sentence closing with a call to subscribe

Format the output as JSON with this structure:
{
  "opening": "...",
  "clips": [
    {"number": 10, "intro": "...", "outro": "..."},
    ...
  ],
  "closing": "..."
}
```

**Script validation:**
- Parse JSON response
- Verify all clips have intro and outro (8-10 expected)
- Check character count per segment (intro: 150-400 chars, outro: 50-150 chars)
- Total script character count should target 3,500-5,500 characters (yields ~2.5-4 min narration at 150 words/min TTS speed)
- If validation fails, retry with corrective prompt (up to 3 attempts)

**Output:**
- Structured script JSON file
- Estimated narration duration per segment
- Total estimated narration duration

---

### 4.5 Text-to-Speech Engine

**Purpose:** Convert narration scripts to audio using configurable TTS engines.

**All TTS calls go through the TTS abstraction layer (Section 9).**

**Supported engines (at launch):**

1. **Coqui XTTS v2 (primary)**
   - Voice cloning from reference audio sample
   - GPU inference on RTX 4000 Ada (~2-4GB VRAM)
   - Speed: ~1.5x realtime
   - Quality: Near-human, consistent voice

2. **StyleTTS 2 (secondary/A-B testing)**
   - Reference audio style transfer
   - GPU inference (~2GB VRAM)
   - Speed: ~3x realtime
   - Quality: Excellent, slightly different character

3. **Piper (CPU fallback)**
   - Pretrained voices, no cloning
   - CPU-only, near-instant
   - Quality: Acceptable, robotic in comparison
   - Use when GPU is unavailable

**Voice configuration per channel:**

Each niche channel has its own voice profile:

```yaml
channels:
  gaming:
    tts_voice:
      engine: "xtts_v2"
      reference_audio: "voices/gaming_anchor.wav"
      speed: 1.05
      pitch_shift: 0
  sports:
    tts_voice:
      engine: "xtts_v2"
      reference_audio: "voices/sports_anchor.wav"
      speed: 1.0
      pitch_shift: 0
```

**Audio processing pipeline:**

```
Script text
  -> Sentence splitting (by period/question mark)
  -> TTS inference per sentence (batched)
  -> Concatenate sentences with natural pauses (200-400ms)
  -> Apply slight compression (reduce dynamic range)
  -> Normalize to -16 LUFS (YouTube broadcast standard)
  -> Export as WAV (for editing) and MP3 (for preview)
```

**Output per script:**
- Full narration WAV file
- Per-segment WAV files (opening, clip1_intro, clip1_outro, ..., closing)
- Duration measurements per segment (needed for video assembly timing)

---

### 4.6 Video Assembly & Rendering

**Purpose:** Combine clips, narration, graphics, and music into the final video.

**Tool:** FFmpeg (via ffmpeg-python or direct subprocess calls)

**Assembly timeline:**

```
Time ->
[Intro graphic + opening narration]
[Clip 10 label graphic]
[Clip 10 intro narration (over transition/background)]
[Clip 10 video + original audio (ducked)]
[Clip 10 outro narration]
[Transition to Clip 9]
...repeat for all 8-10 clips...
[Closing narration + subscribe graphic]
[Outro card]
```

**Visual elements:**

All graphics are generated programmatically using Pillow or FFmpeg drawtext:

1. **Branded intro** (3-5 seconds)
   - Channel logo
   - "LAST SIX HOURS" text
   - Niche label ("GAMING EDITION")
   - Date/time of the coverage window

2. **Clip number label** (shown during each transition)
   - Large "NUMBER 10", "NUMBER 9", etc.
   - Consistent style across all videos
   - 1.5 second duration

3. **Lower third** (shown during each clip)
   - Original video title (truncated if needed)
   - Original creator name
   - View count at discovery time
   - Positioned bottom-left, semi-transparent background

4. **Transition** (between clips)
   - 0.5-1.0 second crossfade or wipe
   - Consistent style across all videos

5. **Outro card** (last 5 seconds)
   - Subscribe prompt (text only, no emojis)
   - "See you in 6 hours"

**Audio mixing:**

```
Narration track:       -16 LUFS (primary)
Clip original audio:   -26 LUFS (ducked, audible but not dominant)
Background music:      -32 LUFS (subtle, royalty-free, from local library)
```

Audio ducking: when narration is playing, clip audio and background music are attenuated by 10-12 dB.

**Render settings:**

```
Container:     MP4
Video codec:   H.264 (libx264)
Resolution:    1920x1080 (16:9)
Frame rate:    30fps
Pixel format:  yuv420p
Bitrate:       8-12 Mbps (CRF 18-22)
Audio codec:   AAC
Audio bitrate: 192 kbps
Sample rate:   48000 Hz
```

**Background music library:**
- Store royalty-free music tracks locally in the working directory
- Categorize by mood (energetic, chill, dramatic, etc.)
- Each niche has a preferred mood mapping
- Music loops seamlessly under narration
- Sources: YouTube Audio Library, Free Music Archive, Pixabay Music (all free, royalty-free)

**Output:**
- Final MP4 file (8-10 minutes)
- Render metadata (duration, file size, clip timestamps in final video)

---

### 4.7 Thumbnail Generation

**Purpose:** Create an eye-catching thumbnail for each video.

**Approach:**

1. Select the most visually striking frame from the #1 clip (the most viral moment)
   - Use FFmpeg to extract frames at 1fps during the clip
   - Send frames to LLM vision endpoint (if available) or use contrast/saturation scoring to pick the best frame
   - Fallback: use the frame at the midpoint of clip #1

2. Compose the thumbnail using Pillow:
   - Background: selected frame, scaled to 1280x720
   - Slight zoom crop (105%) to remove letterboxing if present
   - Color boost: increase saturation by 15-20%
   - Overlay text: large, bold, 3-5 words maximum
   - Text generated by LLM: "Summarize this video in 3-5 words for a YouTube thumbnail. No emojis. Make it dramatic and clickable."
   - Text styling: white with black outline/drop shadow, positioned top or bottom
   - Channel branding: small "LAST SIX HOURS" watermark in corner
   - Optional: red circle or arrow pointing to key element (if LLM identifies one)

3. Generate 2-3 thumbnail variants for potential A/B testing in the future

**Output:**
- Thumbnail JPEG, 1280x720, <2MB
- Variant thumbnails for future testing

---

### 4.8 YouTube Upload & Metadata

**Purpose:** Upload the approved video and metadata to the correct YouTube channel.

**Authentication:**
- OAuth 2.0 flow (one-time setup per channel)
- Refresh tokens stored securely in config
- Separate credentials per niche channel

**Upload process:**
- Use YouTube Data API v3 resumable upload
- Send video file in chunks (5MB chunks, resumable on failure)
- Set processing status to "private" initially
- After successful upload, change to "public" (or "scheduled" if timing matters)

**Metadata generation (via LLM):**

```
Title: "Last SiX Hours: Gaming -- [date] [time] Edition"
       (LLM can suggest more engaging titles based on top clip)

Description:
  - 2-3 sentence summary of the video
  - Timestamps for each clip (auto-generated from assembly timeline)
  - Credits section: list of all 10 source videos with titles, creator names, and links
  - Channel links and social media
  - Hashtags

Tags:
  - Generated by LLM based on clip content
  - Always include: "last six hours", "viral", "trending", niche keywords
  - Max 500 characters total

Category:
  - Mapped per niche (Gaming = 20, Sports = 17, Entertainment = 24, Comedy = 23)

Thumbnail:
  - Upload generated thumbnail via API
```

**Quota management:**
- Each video upload costs ~1,600 quota units
- Monitor daily quota usage
- If approaching limit, queue uploads for next day
- Log all API calls and quota consumption

**Output:**
- YouTube video ID
- Upload status
- Public URL

---

### 4.9 Shorts Generator

**Purpose:** Extract 3-5 Shorts (vertical, 30-60 seconds) from each long-form video.

**Clip selection for Shorts:**
- Use clips ranked #1, #2, and #3 (most viral) as standalone Shorts
- Optionally include #4 and #5 if they score well

**Vertical conversion:**
- Crop source clip from 16:9 to 9:16 (1080x1920)
- Smart crop: detect the region of interest (center of action) using:
  - Face detection (OpenCV Haar cascades or MediaPipe)
  - Motion detection (frame differencing)
  - Center crop as fallback
- Add padding/blur behind if smart crop leaves gaps

**Short structure:**
- Hook text overlay in large font (first 1 second): "THIS GAMER JUST BROKE THE INTERNET"
  - Text generated by LLM for each clip
- Source clip plays (15-40 seconds)
- Brief narration overlay (optional, 5-10 seconds)
- Channel branding text at end: "LAST SIX HOURS" + "Subscribe for more"
- Total: 30-60 seconds

**Upload:**
- Upload as regular video but with #Shorts in title
- Vertical aspect ratio triggers YouTube Shorts classification
- Metadata optimized for Shorts discovery

**Output per long-form video:**
- 3-5 Short MP4 files (1080x1920)
- Metadata per Short (title, description, tags)

---

### 4.10 Telegram Review Bot

**Purpose:** Human review gateway. No video uploads to YouTube without explicit approval.

**Library:** python-telegram-bot (v20+, async)

**Bot setup:**
- Create bot via @BotFather
- Store bot token in config
- Webhook mode (preferred on server) or long-polling (simpler for development)
- Single authorized user (your Telegram user ID in config, reject all others)

**Review flow:**

When a video is ready for review, the bot sends:

```
VIDEO READY FOR REVIEW
--------------------------------------------------
Channel: Last SiX Hours: Gaming
Episode: #47
Coverage: Feb 28 2026, 12:00-18:00 UTC
Duration: 12:34
File size: 847 MB

Clip Summary:
 1. (rank 10) "Streamer rage quits on stream" by xQcOW -- 22s
 2. (rank 9) "Impossible Elden Ring no-hit run" by distortion2 -- 18s
 3. (rank 8) "Minecraft speedrun world record" by dream -- 25s
 4. (rank 7) ...
 ...
10. (rank 1) "Pro player clutches 1v5 at major" by s1mple -- 20s

Flags:
 - Clip #4: Music detected in background (low Content ID risk)
 - Clip #7: Source video is from a verified channel (medium risk)

Script preview (first 200 chars):
"Welcome back to Last SiX Hours, your source for everything viral
in gaming. In the last six hours, the internet has been losing its
collective mind over..."
```

Then sends:
- A 30-second video preview (the intro + first clip)
- A link to the full video on the local server (via simple HTTP file server or Telegram file if under 2GB)

**Inline keyboard buttons:**

```
[APPROVE]  [REJECT]  [HOLD]
[SKIP CLIPS]  [REDO SCRIPT]  [STATUS]
```

**Command reference:**

| Command | Action |
|---|---|
| /approve | Upload the pending video to YouTube |
| /reject | Discard the video entirely |
| /hold | Save for later review |
| /skip 4,7 | Remove clips 4 and 7, regenerate video |
| /redo_script | Keep clips, regenerate narration |
| /status | Show pipeline status across all channels |
| /pause [channel] | Pause a specific channel's pipeline |
| /resume [channel] | Resume a paused channel |
| /stats | Show upload counts, view counts, errors |
| /config [key] [value] | Update a runtime config value |
| /errors | Show recent errors |
| /queue | Show videos awaiting review |
| /force_upload [id] | Upload a held video immediately |
| /help | Show command reference |

**Timeout behavior:**
- If no response within a configurable window (default: 4 hours), the video is auto-held (not uploaded, not discarded)
- Bot sends a reminder at the 2-hour mark
- Held videos can be reviewed later via /queue

**Agent-initiated messages:**

The pipeline can ask questions via the bot:

```
QUESTION FROM PIPELINE
--------------------------------------------------
Context: Discovered a viral video with 5.2M views in 3 hours,
but it is 2 hours long and the most-replayed data is unavailable.

Question: Should I include the middle segment (32:15-32:40)
based on transcript analysis, or skip this video?

[INCLUDE]  [SKIP]  [LET ME WATCH: link]
```

The pipeline pauses that specific task until a response is received, while continuing other work.

**Notification management:**
- Configurable quiet hours (e.g., 23:00-07:00 local time)
- During quiet hours, videos are auto-held, notifications suppressed
- Batch notification sent when quiet hours end: "3 videos ready for review"

---

### 4.11 Scheduler & Orchestrator

**Purpose:** Coordinate all pipeline runs across all channels on a repeating 6-hour cycle.

**Scheduling:**

```
Channel: Gaming     -- 00:30, 06:30, 12:30, 18:30 UTC
Channel: Sports     -- 01:00, 07:00, 13:00, 19:00 UTC
Channel: Funny      -- 01:30, 07:30, 13:30, 19:30 UTC
Channel: Music/Ent  -- 02:00, 08:00, 14:00, 20:00 UTC
```

Staggered by 30 minutes to avoid resource contention and API quota spikes.

**Orchestrator responsibilities:**

1. **Trigger pipeline runs** on schedule
2. **Resource management:**
   - Max 2 concurrent pipeline runs (configurable)
   - Max 3 concurrent video downloads
   - Max 1 concurrent video render (CPU-intensive)
   - GPU access serialized for TTS inference
3. **Retry logic:**
   - If a pipeline stage fails, retry up to 3 times with exponential backoff
   - If a full pipeline run fails, skip and alert via Telegram
4. **State persistence:**
   - Track pipeline state in database
   - Resume interrupted pipelines after restart
5. **Quota tracking:**
   - Monitor YouTube API quota usage
   - Defer uploads if quota is exhausted
6. **Cleanup:**
   - Delete temporary files (downloads, intermediate renders) after pipeline completion
   - Archive final videos to Tier 2 storage
   - Prune archives older than configurable retention period (default: 30 days)

**Implementation:** APScheduler with persistent job store (SQLite-backed).

---

### 4.12 Analytics & Feedback Loop

**Purpose:** Track performance and automatically adjust pipeline parameters over time.

**Data collection:**
- YouTube Analytics API: views, watch time, retention curves, CTR, subscriber gains per video
- Poll every 6 hours for recent video performance
- Store all metrics in the database

**Feedback signals:**

| Metric | What It Tells Us | Adjustment |
|---|---|---|
| Average view duration | Are videos too long/short? | Adjust clip count or clip length |
| Retention curve drops | Where do viewers leave? | Improve transitions at those points |
| CTR (click-through rate) | Are thumbnails/titles effective? | Adjust thumbnail style, title format |
| Subscriber gain per video | Which niches grow fastest? | Prioritize high-growth niches |
| Content ID claims | Which clip types get flagged? | Adjust clip source filtering |
| Shorts views vs long-form | Which format performs better? | Adjust Shorts strategy |

**Automated adjustments (future phase):**
- LLM analyzes performance data weekly
- Generates recommendations: "Gaming videos with clips under 20 seconds retain 15% more viewers. Recommend reducing max clip length from 25s to 20s."
- Recommendations sent to Telegram for approval before applying

**Manual analysis:**
- /stats command in Telegram shows key metrics
- Weekly digest sent via Telegram: top performing videos, growth trends, issues

---

## 5. Data Flow & Pipeline

### 5.1 Single Pipeline Run (One Niche, One Cycle)

```
PHASE 1: DISCOVERY (5-10 minutes)
  |
  |-- Query YouTube trending API for niche
  |-- Query Reddit for niche-relevant subreddits
  |-- Score and rank all candidates
  |-- Deduplicate against database
  |-- Select top 12-15 candidates (buffer for failures)
  |
  v
PHASE 2: ACQUISITION (10-20 minutes)
  |
  |-- Download top 12-15 videos via yt-dlp
  |-- Fetch subtitles/captions
  |-- Validate downloads (duration, codec, integrity)
  |-- Drop any failed downloads
  |
  v
PHASE 3: ANALYSIS & EXTRACTION (5-15 minutes)
  |
  |-- For each video:
  |     |-- Attempt Most Replayed heatmap scrape
  |     |-- Fallback: transcript analysis via LLM
  |     |-- Fallback: audio energy analysis
  |     |-- Extract 15-25 second clip at identified timestamp
  |     |-- Normalize audio levels
  |-- Rank clips by viral score
  |-- Select top 8-10 for the video (configurable min_clips / max_clips)
  |
  v
PHASE 4: SCRIPT GENERATION (1-2 minutes)
  |
  |-- Send clip metadata to LLM
  |-- Generate full narration script
  |-- Validate script structure and length
  |-- Retry if validation fails
  |
  v
PHASE 5: TTS (3-5 minutes)
  |
  |-- Split script into segments
  |-- Generate audio per segment via TTS engine
  |-- Concatenate with natural pauses
  |-- Normalize to broadcast standard
  |
  v
PHASE 6: VIDEO ASSEMBLY (5-10 minutes)
  |
  |-- Generate graphics (intro, clip labels, lower thirds, outro)
  |-- Assemble timeline: narration + clips + graphics + music
  |-- Render final MP4 via FFmpeg
  |-- Generate thumbnail
  |-- Generate 3-5 Shorts
  |
  v
PHASE 7: REVIEW (human-dependent, 0 - 4 hours)
  |
  |-- Send preview and summary to Telegram
  |-- Wait for human response
  |-- If approved: proceed to upload
  |-- If rejected/modified: loop back to relevant phase
  |
  v
PHASE 8: UPLOAD (5-10 minutes)
  |
  |-- Upload long-form video to YouTube
  |-- Upload Shorts to YouTube
  |-- Set metadata (title, description, tags, thumbnail)
  |-- Set visibility to public
  |-- Log upload details to database
  |
  v
PHASE 9: CLEANUP
  |
  |-- Delete temporary downloads and intermediate files
  |-- Archive final video to Tier 2 storage
  |-- Update database with completion status
```

**Total estimated time per pipeline run: 30-60 minutes** (excluding human review wait time)

### 5.2 Parallel Execution

With 4 channels on staggered schedules:

```
Time (UTC)    Gaming    Sports    Funny    Music/Ent
00:00-00:30                                           (idle)
00:30-01:00   DISCOVER
01:00-01:30   ACQUIRE   DISCOVER
01:30-02:00   ANALYZE   ACQUIRE   DISCOVER
02:00-02:30   SCRIPT    ANALYZE   ACQUIRE   DISCOVER
02:30-03:00   TTS       SCRIPT    ANALYZE   ACQUIRE
03:00-03:30   RENDER    TTS       SCRIPT    ANALYZE
03:30-04:00   REVIEW    RENDER    TTS       SCRIPT
04:00-04:30   UPLOAD    REVIEW    RENDER    TTS
04:30-05:00             UPLOAD    REVIEW    RENDER
05:00-05:30                       UPLOAD    REVIEW
05:30-06:00                                 UPLOAD
06:00-06:30                                           (idle)
06:30-07:00   DISCOVER                                (next cycle)
...
```

Resource-intensive phases (RENDER, TTS) are naturally staggered, avoiding contention.

---

## 6. Database Schema

**Engine:** SQLite (single file, zero configuration, sufficient for this workload)

**Location:** `{working_dir}/data/viral_channel.db`

### Tables

```sql
-- Discovered videos (deduplication and tracking)
CREATE TABLE discovered_videos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT UNIQUE NOT NULL,           -- YouTube video ID
    title TEXT NOT NULL,
    channel_name TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    url TEXT NOT NULL,
    category_id INTEGER,
    duration_seconds INTEGER,
    view_count INTEGER,
    like_count INTEGER,
    comment_count INTEGER,
    view_velocity REAL,                      -- views per hour at discovery
    viral_score REAL,
    niche TEXT NOT NULL,                     -- gaming, sports, funny, music
    discovery_source TEXT,                   -- youtube_trending, reddit, etc.
    discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed INTEGER DEFAULT 0,            -- 0=pending, 1=used, 2=skipped, 3=rejected
    content_id_risk TEXT DEFAULT 'unknown'   -- low, medium, high, unknown
);

-- Pipeline runs
CREATE TABLE pipeline_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    niche TEXT NOT NULL,
    cycle_start TIMESTAMP NOT NULL,          -- start of the 6-hour window
    cycle_end TIMESTAMP NOT NULL,            -- end of the 6-hour window
    status TEXT DEFAULT 'pending',           -- pending, running, review, approved, uploaded, failed
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    video_file_path TEXT,
    video_duration_seconds REAL,
    video_file_size_bytes INTEGER,
    youtube_video_id TEXT,                   -- set after upload
    youtube_url TEXT,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0
);

-- Clips used in each pipeline run
CREATE TABLE clips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pipeline_run_id INTEGER NOT NULL REFERENCES pipeline_runs(id),
    discovered_video_id INTEGER NOT NULL REFERENCES discovered_videos(id),
    rank_position INTEGER NOT NULL,          -- 1-10 (1 = most viral)
    start_time_seconds REAL NOT NULL,
    end_time_seconds REAL NOT NULL,
    clip_duration_seconds REAL NOT NULL,
    extraction_method TEXT,                  -- most_replayed, transcript, audio_energy, scene_detection
    clip_file_path TEXT,
    content_id_risk TEXT DEFAULT 'unknown'
);

-- Generated scripts
CREATE TABLE scripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pipeline_run_id INTEGER NOT NULL REFERENCES pipeline_runs(id),
    opening_text TEXT,
    closing_text TEXT,
    full_script_json TEXT,                   -- complete script as JSON
    total_char_count INTEGER,
    estimated_duration_seconds REAL,
    llm_model_used TEXT,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- TTS audio files
CREATE TABLE tts_audio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pipeline_run_id INTEGER NOT NULL REFERENCES pipeline_runs(id),
    engine_used TEXT NOT NULL,               -- xtts_v2, styletts2, piper
    voice_profile TEXT,
    audio_file_path TEXT,
    duration_seconds REAL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Shorts generated from long-form videos
CREATE TABLE shorts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pipeline_run_id INTEGER NOT NULL REFERENCES pipeline_runs(id),
    clip_id INTEGER REFERENCES clips(id),
    file_path TEXT,
    duration_seconds REAL,
    title TEXT,
    description TEXT,
    youtube_video_id TEXT,
    youtube_url TEXT,
    status TEXT DEFAULT 'pending',           -- pending, review, uploaded, failed
    uploaded_at TIMESTAMP
);

-- YouTube analytics snapshots
CREATE TABLE analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    youtube_video_id TEXT NOT NULL,
    measured_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    view_count INTEGER,
    like_count INTEGER,
    comment_count INTEGER,
    average_view_duration_seconds REAL,
    click_through_rate REAL,
    subscriber_gain INTEGER,
    estimated_revenue_usd REAL
);

-- Telegram review log
CREATE TABLE review_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pipeline_run_id INTEGER NOT NULL REFERENCES pipeline_runs(id),
    sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    responded_at TIMESTAMP,
    action TEXT,                              -- approve, reject, hold, skip, redo_script
    response_detail TEXT,                     -- e.g., "skip 4,7"
    auto_held INTEGER DEFAULT 0              -- 1 if auto-held due to timeout
);

-- Configuration overrides (runtime-adjustable via Telegram)
CREATE TABLE config_overrides (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_by TEXT DEFAULT 'system'
);

-- Error log
CREATE TABLE error_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pipeline_run_id INTEGER,
    module TEXT NOT NULL,
    error_type TEXT NOT NULL,
    error_message TEXT NOT NULL,
    stack_trace TEXT,
    occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved INTEGER DEFAULT 0
);

-- Indexes for common queries
CREATE INDEX idx_discovered_videos_niche ON discovered_videos(niche, discovered_at);
CREATE INDEX idx_discovered_videos_processed ON discovered_videos(processed);
CREATE INDEX idx_pipeline_runs_status ON pipeline_runs(status);
CREATE INDEX idx_pipeline_runs_niche ON pipeline_runs(niche, cycle_start);
CREATE INDEX idx_clips_pipeline ON clips(pipeline_run_id);
CREATE INDEX idx_analytics_video ON analytics(youtube_video_id, measured_at);
CREATE INDEX idx_error_log_module ON error_log(module, occurred_at);
```

---

## 7. Configuration System

### 7.1 Configuration File

All configuration is stored in a single YAML file with environment variable overrides.

**File:** `config/config.yaml`

```yaml
# ============================================================
# Last SiX Hours -- Pipeline Configuration
# ============================================================

general:
  project_name: "Last SiX Hours"
  working_dir: "/data/viral_channel/working"
  archive_dir: "/data/viral_channel/archive"
  database_path: "/data/viral_channel/data/viral_channel.db"
  log_level: "INFO"                     # DEBUG, INFO, WARNING, ERROR
  log_dir: "/data/viral_channel/logs"
  timezone: "UTC"

# ============================================================
# LLM Configuration (model-agnostic)
# ============================================================
llm:
  primary:
    provider: "openai_compatible"
    base_url: "http://localhost:8080/v1"   # local DeepSeek / vLLM / Ollama
    model: "deepseek-r1"
    api_key: ""                            # empty for local
    max_tokens: 4096
    temperature: 0.7
    timeout_seconds: 120
  fallback:
    provider: "openai_compatible"
    base_url: "https://api.openai.com/v1"
    model: "gpt-4o"
    api_key: "${OPENAI_API_KEY}"
    max_tokens: 4096
    temperature: 0.7
    timeout_seconds: 60
  retry:
    max_attempts: 3
    backoff_seconds: 5

# ============================================================
# TTS Configuration
# ============================================================
tts:
  primary:
    engine: "xtts_v2"
    model_path: "/data/viral_channel/models/xtts_v2"
    device: "cuda:0"                       # GPU device
    sample_rate: 24000
  fallback:
    engine: "piper"
    model_path: "/data/viral_channel/models/piper/en_US-lessac-high"
    device: "cpu"
    sample_rate: 22050
  audio:
    target_lufs: -16
    pause_between_sentences_ms: 300
    output_format: "wav"

# ============================================================
# Channel Definitions
# ============================================================
channels:
  gaming:
    enabled: true
    youtube_channel_id: ""                 # set after channel creation
    credentials_file: "config/youtube_gaming_creds.json"
    schedule_utc: ["00:30", "06:30", "12:30", "18:30"]
    category_id: 20                        # YouTube Gaming category
    voice:
      reference_audio: "voices/gaming_anchor.wav"
      speed: 1.05
    discovery:
      youtube_regions: ["US", "GB"]
      reddit_subreddits: ["gaming", "pcgaming", "leagueoflegends", "valorant", "minecraft", "apexlegends"]
      keywords: ["gaming", "streamer", "esports", "speedrun", "gameplay"]
      min_viral_score: 0.6
    video:
      min_clips: 8
      max_clips: 10
      clip_duration_min: 12
      clip_duration_max: 25
      target_duration_min: 480             # 8 minutes
      target_duration_max: 600             # 10 minutes

  sports:
    enabled: true
    youtube_channel_id: ""
    credentials_file: "config/youtube_sports_creds.json"
    schedule_utc: ["01:00", "07:00", "13:00", "19:00"]
    category_id: 17
    voice:
      reference_audio: "voices/sports_anchor.wav"
      speed: 1.0
    discovery:
      youtube_regions: ["US", "GB"]
      reddit_subreddits: ["sports", "soccer", "nba", "nfl", "mma", "boxing", "tennis"]
      keywords: ["sports", "goal", "knockout", "dunk", "touchdown", "highlight"]
      min_viral_score: 0.6
    video:
      min_clips: 8
      max_clips: 10
      clip_duration_min: 12
      clip_duration_max: 25
      target_duration_min: 480
      target_duration_max: 600

  funny:
    enabled: true
    youtube_channel_id: ""
    credentials_file: "config/youtube_funny_creds.json"
    schedule_utc: ["01:30", "07:30", "13:30", "19:30"]
    category_id: 23
    voice:
      reference_audio: "voices/funny_anchor.wav"
      speed: 1.0
    discovery:
      youtube_regions: ["US", "GB"]
      reddit_subreddits: ["funny", "unexpected", "whatcouldgowrong", "ContagiousLaughter", "therewasanattempt"]
      keywords: ["funny", "fail", "unexpected", "prank", "reaction"]
      min_viral_score: 0.5
    video:
      min_clips: 8
      max_clips: 10
      clip_duration_min: 12
      clip_duration_max: 25
      target_duration_min: 480
      target_duration_max: 600

  entertainment:
    enabled: false                          # enable when ready
    youtube_channel_id: ""
    credentials_file: "config/youtube_entertainment_creds.json"
    schedule_utc: ["02:00", "08:00", "14:00", "20:00"]
    category_id: 24
    voice:
      reference_audio: "voices/entertainment_anchor.wav"
      speed: 1.0
    discovery:
      youtube_regions: ["US", "GB"]
      reddit_subreddits: ["videos", "nextfuckinglevel", "interestingasfuck", "BeAmazed"]
      keywords: ["viral", "amazing", "incredible", "talent", "performance"]
      min_viral_score: 0.5
    video:
      min_clips: 8
      max_clips: 10
      clip_duration_min: 12
      clip_duration_max: 25
      target_duration_min: 480
      target_duration_max: 600

# ============================================================
# Discovery Engine
# ============================================================
discovery:
  youtube:
    api_key: "${YOUTUBE_API_KEY}"
    daily_quota_limit: 10000
    max_results_per_search: 50
    lookback_hours: 6
    velocity_sample_interval_minutes: 30
    min_views_for_consideration: 10000
  reddit:
    client_id: "${REDDIT_CLIENT_ID}"
    client_secret: "${REDDIT_CLIENT_SECRET}"
    user_agent: "LastSiXHours/1.0"
    min_score: 100
    max_age_hours: 8                       # slightly wider than 6 to catch rising posts
  scoring:
    weight_view_velocity: 0.35
    weight_reddit_score: 0.25
    weight_like_ratio: 0.15
    weight_comment_velocity: 0.15
    weight_recency: 0.10
  max_candidates_per_niche: 15             # download buffer

# ============================================================
# Video Processing
# ============================================================
video:
  download:
    max_concurrent: 3
    max_resolution: 1080
    format: "mp4"
    timeout_seconds: 300
    max_source_duration_seconds: 3600      # skip videos over 1 hour
  clip_extraction:
    methods_priority: ["most_replayed", "transcript", "audio_energy", "scene_detection"]
    fade_duration_seconds: 0.5
    audio_normalization: true
  rendering:
    codec: "libx264"
    crf: 20
    preset: "medium"                       # ultrafast, fast, medium, slow
    resolution: "1920x1080"
    fps: 30
    audio_codec: "aac"
    audio_bitrate: "192k"
    pixel_format: "yuv420p"
  shorts:
    count_per_video: 3
    min_duration: 30
    max_duration: 60
    resolution: "1080x1920"
    crop_method: "smart"                   # smart, center

# ============================================================
# Audio
# ============================================================
audio:
  narration_lufs: -16
  clip_audio_lufs: -26
  background_music_lufs: -32
  ducking_db: -12
  music_dir: "assets/music"
  music_fade_seconds: 2.0

# ============================================================
# Telegram Bot
# ============================================================
telegram:
  bot_token: "${TELEGRAM_BOT_TOKEN}"
  authorized_user_ids: []                  # list of Telegram user IDs authorized to control the bot
  review_timeout_hours: 4
  reminder_after_hours: 2
  quiet_hours:
    enabled: true
    start_utc: "23:00"
    end_utc: "07:00"
  preview_clip_duration_seconds: 30
  file_server:
    enabled: true
    host: "0.0.0.0"
    port: 8888
    base_url: "http://your-server-ip:8888"

# ============================================================
# YouTube Upload
# ============================================================
youtube:
  upload_chunk_size_bytes: 5242880         # 5 MB
  default_privacy: "private"               # uploaded as private, changed to public after confirmation
  publish_delay_seconds: 10                # delay between setting public and moving on
  max_uploads_per_day: 20
  shorts_in_title: true                    # include #Shorts in Short titles

# ============================================================
# Scheduler
# ============================================================
scheduler:
  max_concurrent_pipelines: 2
  max_concurrent_downloads: 3
  max_concurrent_renders: 1
  retry_max_attempts: 3
  retry_backoff_base_seconds: 30
  cleanup_after_days: 30                   # delete archived videos older than this

# ============================================================
# Branding Assets
# ============================================================
branding:
  intro_template: "assets/templates/intro.png"
  outro_template: "assets/templates/outro.png"
  clip_label_template: "assets/templates/clip_label.png"
  lower_third_template: "assets/templates/lower_third.png"
  thumbnail_font: "assets/fonts/impact.ttf"
  thumbnail_font_size: 72
  watermark_text: "LAST SIX HOURS"
  colors:
    primary: "#FF0000"
    secondary: "#FFFFFF"
    background: "#000000"
    text: "#FFFFFF"
    accent: "#FFD700"
```

### 7.2 Environment Variables

Secrets are never stored in the YAML file. They are loaded from environment variables or a `.env` file:

```
YOUTUBE_API_KEY=...
REDDIT_CLIENT_ID=...
REDDIT_CLIENT_SECRET=...
OPENAI_API_KEY=...
TELEGRAM_BOT_TOKEN=...
```

### 7.3 Runtime Overrides

The `config_overrides` database table allows runtime changes via Telegram commands without restarting the pipeline. These override YAML values.

**Merge order:** YAML defaults < environment variables < database overrides

---

## 8. LLM Abstraction Layer

### 8.1 Design

All LLM interactions go through a single `LLMClient` class. No module directly calls any LLM API.

```
Interface:

class LLMClient:
    async def complete(prompt: str, system_prompt: str = None, **kwargs) -> str
    async def complete_json(prompt: str, system_prompt: str = None, schema: dict = None, **kwargs) -> dict
    async def classify(text: str, categories: list[str], **kwargs) -> str
    async def summarize(text: str, max_length: int = 200, **kwargs) -> str
```

### 8.2 Provider Compatibility

The client uses the OpenAI Python SDK (`openai.AsyncOpenAI`) with configurable `base_url`. This works with:

- OpenAI API (GPT-4o, GPT-4, etc.)
- DeepSeek API (local or cloud)
- vLLM server
- Ollama (with OpenAI-compatible mode)
- LM Studio
- text-generation-webui (with OpenAI extension)
- llama.cpp server
- Any OpenAI-compatible endpoint

### 8.3 Fallback Chain

```
1. Try primary provider (e.g., local DeepSeek)
2. If timeout or error -> retry up to max_attempts
3. If all retries fail -> try fallback provider (e.g., OpenAI)
4. If fallback fails -> log error, alert via Telegram, skip this LLM task
```

### 8.4 Prompt Management

All prompts are stored as Jinja2 templates in `config/prompts/`:

```
config/prompts/
  script_generation.j2
  niche_classification.j2
  title_generation.j2
  description_generation.j2
  tag_generation.j2
  thumbnail_text.j2
  clip_analysis.j2
  performance_analysis.j2
  telegram_question.j2
```

This allows prompt iteration without code changes. The agent can modify prompts to improve output quality over time.

---

## 9. TTS Abstraction Layer

### 9.1 Design

All TTS interactions go through a single `TTSEngine` class.

```
Interface:

class TTSEngine:
    async def synthesize(text: str, voice_config: dict) -> AudioSegment
    async def synthesize_batch(segments: list[str], voice_config: dict) -> list[AudioSegment]
    def get_available_voices() -> list[str]
    def estimate_duration(text: str) -> float
```

### 9.2 Engine Registration

Engines are registered as plugins. Adding a new TTS engine requires:

1. Create a class that implements the `TTSEngine` interface
2. Register it in the engine registry
3. Reference it by name in config

```
Registered engines:
  "xtts_v2"     -> CoquiXTTSEngine
  "styletts2"   -> StyleTTS2Engine
  "piper"       -> PiperEngine
  # Future:
  "fish_speech" -> FishSpeechEngine
  "openvoice"   -> OpenVoiceEngine
  "bark"        -> BarkEngine
```

### 9.3 Fallback Chain

```
1. Try primary engine (e.g., xtts_v2 on GPU)
2. If GPU unavailable or error -> try fallback engine (e.g., piper on CPU)
3. If all engines fail -> log error, alert via Telegram, hold pipeline
```

### 9.4 Voice Management

Voice reference files are stored in `voices/` directory. Each channel has a dedicated voice profile. New voices can be added by:

1. Place a 10-30 second WAV file of the target voice in `voices/`
2. Update the channel config to reference it
3. The TTS engine clones the voice from the reference

---

## 10. Multi-Channel Strategy

### 10.1 Channel Structure

Each niche operates as an independent YouTube channel:

| Channel | Name Format | Focus |
|---|---|---|
| Gaming | Last SiX Hours: Gaming | Game clips, streamer moments, esports |
| Sports | Last SiX Hours: Sports | Athletic highlights, reactions, records |
| Funny | Last SiX Hours: Funny | Fails, pranks, unexpected moments |
| Entertainment | Last SiX Hours: Entertainment | Talent, performances, viral general content |

### 10.2 Why Separate Channels

- YouTube's recommendation algorithm favors niche consistency
- Each channel builds its own subscriber base with aligned interests
- Different CPM rates per niche (sports/finance highest)
- A single combined channel confuses the algorithm and reduces recommendations
- Can shut down underperforming channels without affecting others
- Cross-promotion between channels ("Check out our Gaming channel")

### 10.3 Channel Rollout

Start with 1-2 channels, add more once the pipeline is stable:

- Phase 1: Gaming + Funny (highest volume of viral content, easiest to source)
- Phase 2: Add Sports (after proving the pipeline works)
- Phase 3: Add Entertainment (or replace an underperformer)

### 10.4 Per-Channel Independence

Each channel has:
- Its own YouTube credentials (OAuth tokens)
- Its own voice profile
- Its own discovery parameters (subreddits, keywords, score thresholds)
- Its own schedule
- Its own analytics tracking
- Shared infrastructure (same server, same database, same codebase)

---

## 11. Copyright & Monetization Compliance

### 11.1 Fair Use Positioning

The channel is positioned as **news commentary and reporting** -- one of the strongest fair use categories. Every video:

- Reports on trending content (newsworthy)
- Adds substantial original narration (transformative)
- Uses only brief clips (limited portion of original)
- Does not substitute for the original (different purpose)
- Credits original creators (good faith)

### 11.2 Clip Rules (Enforced by Pipeline)

| Rule | Limit | Enforcement |
|---|---|---|
| Max clip duration | 25 seconds | Hard limit in clip extraction |
| Max clip vs. original ratio | Clip must be < 10% of source video duration | Calculated and enforced |
| Narration ratio | Narration audio >= 60% of total video duration | Validated before review |
| Creator credit | Every source video credited in description | Auto-generated |
| Link to original | Every source video linked in description | Auto-generated |

### 11.3 Content ID Risk Mitigation

**Pre-upload checks:**
- Music detection: analyze clip audio for music signatures using basic spectral analysis
- Flag clips from known aggressive copyright holders (configurable blocklist)
- Mark risk level on each clip (low/medium/high)
- Report risk levels in Telegram review message

**Post-upload handling:**
- Monitor for Content ID claims via YouTube API
- If a claim is received: log it, notify via Telegram, do not dispute automatically
- Track which source channels/types generate claims -- feed back into discovery scoring to avoid repeat issues

### 11.4 Blocklist

Maintain a configurable list of channels/content types to avoid:

```yaml
copyright_blocklist:
  channels: []                             # YouTube channel IDs to never clip from
  keywords: ["official music video", "full episode", "movie trailer"]
  categories_avoid: [10]                   # category 10 = Music
```

### 11.5 Monetization Path

**YouTube Partner Program requirements per channel:**
- 1,000 subscribers
- 4,000 watch hours in last 12 months OR 10M Shorts views in 90 days

**Projected timeline to eligibility (per channel):**
- At 4 uploads/day with 1,000-5,000 views/video: eligible within 30-60 days
- Shorts can accelerate this significantly (10M views across 90 days = ~110K views/day across all Shorts)

**Revenue optimization:**
- Videos at 8+ minutes enable mid-roll ads (critical revenue threshold)
- Consistent upload schedule trains the algorithm
- End screens and cards drive cross-channel traffic
- Community posts keep engagement between uploads
- Avoid Content ID claims to keep full revenue

---

## 12. Error Handling & Monitoring

### 12.1 Error Categories

| Category | Example | Response |
|---|---|---|
| Transient | API timeout, rate limit | Retry with exponential backoff |
| Recoverable | Download failed for 1 video | Skip that video, use next candidate |
| Pipeline failure | FFmpeg render crash | Retry full render, alert if repeated |
| Critical | Database corruption, disk full | Halt pipeline, alert immediately |
| External | YouTube API quota exhausted | Queue uploads, defer to next day |

### 12.2 Retry Policy

```
Attempt 1: Immediate
Attempt 2: Wait 30 seconds
Attempt 3: Wait 90 seconds
After 3 failures: Mark as failed, alert via Telegram, move on
```

### 12.3 Monitoring

**Telegram alerts (immediate):**
- Pipeline failure after all retries
- Critical errors (disk full, database error)
- Content ID claim received
- YouTube API quota approaching limit

**Telegram digest (every 6 hours):**
- Pipelines completed / failed
- Videos uploaded
- Videos pending review
- Top performing video of the period

**Log files:**
- Rotating log files in `logs/` directory
- Structured JSON logging for machine parsing
- Separate logs per module (discovery, acquisition, rendering, upload, etc.)

### 12.4 Health Checks

The orchestrator runs periodic health checks:
- Disk space: alert if working directory < 50GB free
- GPU availability: verify CUDA device is accessible
- Database integrity: SQLite PRAGMA integrity_check
- Network: verify YouTube API, Reddit API, Telegram API reachable
- TTS engine: verify model is loaded and responsive

---

## 13. File & Folder Structure

```
viral_channel/
|
|-- config/
|   |-- config.yaml                    # Main configuration
|   |-- .env                           # Secrets (gitignored)
|   |-- youtube_gaming_creds.json      # YouTube OAuth (gitignored)
|   |-- youtube_sports_creds.json
|   |-- youtube_funny_creds.json
|   |-- youtube_entertainment_creds.json
|   |-- prompts/                       # LLM prompt templates
|   |   |-- script_generation.j2
|   |   |-- niche_classification.j2
|   |   |-- title_generation.j2
|   |   |-- description_generation.j2
|   |   |-- tag_generation.j2
|   |   |-- thumbnail_text.j2
|   |   |-- clip_analysis.j2
|   |   |-- performance_analysis.j2
|   |   |-- telegram_question.j2
|
|-- src/
|   |-- __init__.py
|   |-- main.py                        # Entry point
|   |-- config.py                      # Configuration loading and validation
|   |-- database.py                    # SQLAlchemy models and DB setup
|   |
|   |-- discovery/
|   |   |-- __init__.py
|   |   |-- engine.py                  # Discovery orchestrator
|   |   |-- youtube_source.py          # YouTube trending/search
|   |   |-- reddit_source.py           # Reddit viral detection
|   |   |-- scorer.py                  # Viral score calculation
|   |   |-- classifier.py             # Niche classification
|   |   |-- dedup.py                   # Deduplication logic
|   |
|   |-- acquisition/
|   |   |-- __init__.py
|   |   |-- downloader.py             # yt-dlp wrapper
|   |   |-- validator.py              # Download validation
|   |
|   |-- analysis/
|   |   |-- __init__.py
|   |   |-- scene_analyzer.py         # Orchestrates all analysis methods
|   |   |-- most_replayed.py          # YouTube most-replayed scraper
|   |   |-- transcript_analyzer.py    # LLM-based transcript analysis
|   |   |-- audio_analyzer.py         # Audio energy analysis
|   |   |-- scene_detection.py        # FFmpeg scene detection
|   |   |-- clip_extractor.py         # FFmpeg clip extraction
|   |
|   |-- scriptgen/
|   |   |-- __init__.py
|   |   |-- generator.py              # Script generation orchestrator
|   |   |-- validator.py              # Script validation
|   |
|   |-- tts/
|   |   |-- __init__.py
|   |   |-- engine.py                 # TTS abstraction layer
|   |   |-- xtts_engine.py            # Coqui XTTS v2 implementation
|   |   |-- styletts_engine.py        # StyleTTS 2 implementation
|   |   |-- piper_engine.py           # Piper implementation
|   |   |-- audio_processor.py        # Audio normalization, concatenation
|   |
|   |-- assembly/
|   |   |-- __init__.py
|   |   |-- renderer.py               # Video assembly orchestrator
|   |   |-- graphics.py               # Intro, outro, lower thirds, labels
|   |   |-- timeline.py               # Timeline construction
|   |   |-- audio_mixer.py            # Audio ducking and mixing
|   |
|   |-- thumbnails/
|   |   |-- __init__.py
|   |   |-- generator.py              # Thumbnail generation
|   |   |-- frame_selector.py         # Best frame selection
|   |
|   |-- shorts/
|   |   |-- __init__.py
|   |   |-- generator.py              # Shorts creation
|   |   |-- cropper.py                # Smart vertical crop
|   |
|   |-- upload/
|   |   |-- __init__.py
|   |   |-- youtube_uploader.py       # YouTube Data API upload
|   |   |-- metadata.py               # Title, description, tags generation
|   |
|   |-- telegram_bot/
|   |   |-- __init__.py
|   |   |-- bot.py                    # Bot setup and handlers
|   |   |-- review.py                 # Review flow logic
|   |   |-- commands.py               # Command handlers
|   |   |-- notifications.py          # Outbound message formatting
|   |   |-- file_server.py            # Simple HTTP server for video previews
|   |
|   |-- llm/
|   |   |-- __init__.py
|   |   |-- client.py                 # LLM abstraction layer
|   |   |-- prompts.py                # Prompt template loading
|   |
|   |-- analytics/
|   |   |-- __init__.py
|   |   |-- collector.py              # YouTube Analytics data collection
|   |   |-- analyzer.py               # Performance analysis
|   |   |-- feedback.py               # Automated parameter adjustment
|   |
|   |-- orchestrator/
|   |   |-- __init__.py
|   |   |-- scheduler.py              # APScheduler setup
|   |   |-- pipeline.py               # Single pipeline run logic
|   |   |-- resource_manager.py       # Concurrency and resource limits
|   |   |-- cleanup.py                # Temp file and archive management
|   |
|   |-- utils/
|   |   |-- __init__.py
|   |   |-- ffmpeg.py                 # FFmpeg command builders
|   |   |-- filesystem.py             # File path management
|   |   |-- logging.py                # Logging setup
|   |   |-- validators.py             # Common validation functions
|
|-- assets/
|   |-- music/                         # Royalty-free background tracks
|   |   |-- energetic/
|   |   |-- chill/
|   |   |-- dramatic/
|   |-- templates/                     # Graphic templates (PNG)
|   |   |-- intro.png
|   |   |-- outro.png
|   |   |-- clip_label.png
|   |   |-- lower_third.png
|   |-- fonts/
|   |   |-- impact.ttf
|   |   |-- roboto-bold.ttf
|
|-- voices/                            # TTS voice reference audio
|   |-- gaming_anchor.wav
|   |-- sports_anchor.wav
|   |-- funny_anchor.wav
|   |-- entertainment_anchor.wav
|
|-- models/                            # Local TTS/ML model files
|   |-- xtts_v2/
|   |-- piper/
|   |-- styletts2/
|
|-- tests/
|   |-- __init__.py
|   |-- test_discovery.py
|   |-- test_acquisition.py
|   |-- test_analysis.py
|   |-- test_scriptgen.py
|   |-- test_tts.py
|   |-- test_assembly.py
|   |-- test_upload.py
|   |-- test_telegram.py
|   |-- test_llm_client.py
|   |-- test_pipeline.py
|   |-- conftest.py                    # Shared test fixtures
|
|-- scripts/
|   |-- setup_youtube_oauth.py         # One-time OAuth setup per channel
|   |-- setup_telegram_bot.py          # Telegram bot registration helper
|   |-- download_tts_models.py         # Download and setup TTS models
|   |-- init_database.py               # Initialize SQLite database
|   |-- run_single_pipeline.py         # Manual single pipeline run (testing)
|   |-- check_health.py               # Health check script
|
|-- docs/
|   |-- SPEC.md                        # This document (symlinked or copied)
|   |-- SETUP.md                       # Setup and installation guide
|   |-- PROMPTS.md                     # Prompt engineering notes
|   |-- CHANGELOG.md                   # Version history
|
|-- XC740XD_Architecture_LLM_Analysis.md  # Server specs reference
|-- SPEC.md                            # This document
|-- requirements.txt                   # Python dependencies
|-- pyproject.toml                     # Project metadata
|-- .gitignore
|-- .env.example                       # Template for secrets
|-- README.md
```

---

## 14. API Keys & External Services

### 14.1 Required Services

| Service | Purpose | Cost | Setup |
|---|---|---|---|
| YouTube Data API v3 | Video discovery, upload, analytics | Free (10K quota/day, request increase) | Google Cloud Console project |
| Reddit API | Viral content discovery | Free | Create app at reddit.com/prefs/apps |
| Telegram Bot API | Human review communication | Free | Message @BotFather on Telegram |

### 14.2 Optional Services

| Service | Purpose | Cost | When Needed |
|---|---|---|---|
| OpenAI API | Fallback LLM | Pay per use (~$5-10/mo) | Only if local LLM is down |
| Twitter/X API | Additional discovery source | $100/mo (Basic) | Phase 2+ if needed |

### 14.3 YouTube API Quota Planning

Daily budget at free tier (10,000 units):

| Operation | Cost | Calls/Day | Total |
|---|---|---|---|
| videos.list (trending) | 1 | 8 (4 niches x 2 regions) | 8 |
| search.list (velocity) | 100 | 16 (4 niches x 4 cycles) | 1,600 |
| videos.list (metadata) | 1 | 240 (60 videos x 4 cycles) | 240 |
| videos.insert (upload) | 1,600 | 16 (4 niches x 4 cycles) | 25,600 |
| thumbnails.set | 50 | 16 | 800 |
| **Total** | | | **~28,248** |

This exceeds the free tier. Solutions:
- **Apply for quota increase** (free, Google reviews use case, typically approved for legitimate projects)
- Use multiple Google Cloud projects (each gets 10K units)
- Reduce search calls by caching and batching
- Upload Shorts via a separate project's quota

### 14.4 Setup Checklist

```
[ ] Create Google Cloud project
[ ] Enable YouTube Data API v3
[ ] Create OAuth 2.0 credentials (one per channel)
[ ] Run setup_youtube_oauth.py for each channel
[ ] Apply for YouTube API quota increase
[ ] Create Reddit application (script type)
[ ] Note client_id and client_secret
[ ] Create Telegram bot via @BotFather
[ ] Note bot token
[ ] Get your Telegram user ID (message @userinfobot)
[ ] Set up .env file with all secrets
[ ] Download TTS models (run download_tts_models.py)
[ ] Create voice reference recordings for each channel
[ ] Source and download royalty-free background music
[ ] Source and download fonts for graphics
[ ] Initialize database (run init_database.py)
```

---

## 15. Implementation Phases

### Phase 0: Infrastructure Setup (1-2 days)

- Create Proxmox VM with specified resources
- Install OS, Python, FFmpeg, yt-dlp, CUDA drivers
- Clone repository, install Python dependencies
- Set up API keys and OAuth credentials
- Download TTS models
- Initialize database
- Verify all services are accessible

### Phase 1: MVP -- Single Channel, Manual Triggers (1-2 weeks)

**Goal:** End-to-end pipeline works for one niche, triggered manually.

Build in order:
1. Configuration system (config.py, config.yaml)
2. Database setup (database.py, init_database.py)
3. LLM abstraction layer (llm/client.py)
4. Discovery engine (YouTube trending + Reddit for Gaming)
5. Video acquisition (downloader.py)
6. Scene analysis (transcript analysis via LLM -- simplest method first)
7. Clip extraction (clip_extractor.py)
8. Script generation (generator.py)
9. TTS engine (XTTS v2 integration)
10. Video assembly (basic: intro + clips + narration + outro)
11. Manual review (preview output, approve/reject from terminal)
12. YouTube upload (single channel)

**Milestone:** Run `python scripts/run_single_pipeline.py --niche gaming` and get a valid video uploaded to YouTube.

### Phase 2: Telegram Bot + Automation (1 week)

- Build Telegram bot with review flow
- Add inline keyboard buttons for approve/reject/hold
- Add file server for video previews
- Implement scheduler with APScheduler
- Add orchestrator with concurrency management
- Add cleanup and archive logic

**Milestone:** Pipeline runs every 6 hours automatically, sends review requests to Telegram, uploads on approval.

### Phase 3: Quality & Polish (1-2 weeks)

- Add Most Replayed heatmap scraping
- Add audio energy analysis
- Improve graphics (better lower thirds, transitions)
- Add background music mixing
- Implement Shorts generation
- Generate thumbnails
- Improve script quality (iterate on prompts)
- Implement narration ratio validation
- Add content ID risk detection

**Milestone:** Videos look professional and are competitive with manual compilation channels.

### Phase 4: Multi-Channel Scaling (1 week)

- Enable second and third niche channels
- Per-channel voice profiles
- Per-channel discovery parameters
- Staggered scheduling
- Quota management across channels

**Milestone:** 3 channels running simultaneously, 12 videos/day + Shorts.

### Phase 5: Analytics & Feedback Loop (1-2 weeks)

- YouTube Analytics integration
- Performance tracking per video
- Automated parameter adjustment recommendations
- Weekly digest via Telegram
- A/B testing for TTS engines
- Thumbnail variant testing (future)

**Milestone:** Pipeline improves its own output quality based on viewer data.

### Phase 6: Continuous Enhancement (Ongoing)

- Agent iterates on prompt quality
- Agent optimizes based on analytics data
- Add new TTS engines as they become available
- Add new discovery sources
- Refine copyright risk detection
- Scale to 4th channel if warranted

---

## 16. Design Principles

1. **No hardcoded models.** Every LLM and TTS model reference is in config, never in code.

2. **No emojis.** In any output -- code, Telegram messages, video text, metadata, logs, documentation.

3. **Fail gracefully.** Every module handles errors locally, retries when appropriate, and degrades rather than crashing. A failed clip does not kill an entire video. A failed video does not kill an entire cycle.

4. **Human in the loop.** Nothing is published to YouTube without explicit human approval via Telegram.

5. **Config over code.** Behavior changes should be possible through configuration changes, not code edits. Prompts are templates. Weights are parameters. Thresholds are configurable.

6. **Abstraction layers.** LLM and TTS engines are behind interfaces. Swap implementations without touching consumer code.

7. **Idempotency.** Pipeline runs can be safely retried. Re-running a cycle does not produce duplicates (deduplication by video ID and cycle window).

8. **Observability.** Every pipeline run is logged in the database. Every error is recorded with context. Status is always available via Telegram.

9. **Minimal cost.** Prefer local inference over API calls. Prefer free tools over paid services. The monthly operating cost target is under $10.

10. **Incremental delivery.** Build the simplest version that works end-to-end first, then layer on quality improvements. A working ugly video is better than a perfect pipeline that never finishes.

---

## Appendix A: Telegram Message Format Reference

All Telegram messages use plain text with basic Markdown formatting (bold, code blocks). No emojis.

**Review notification:**

```
VIDEO READY FOR REVIEW
--------------------------------------------------
Channel: Last SiX Hours: Gaming
Episode: #[number]
Coverage: [date], [start]-[end] UTC
Duration: [mm:ss]
File size: [size] MB

Clip Summary:
[rank]. "[title]" by [creator] -- [duration]s
...

Flags:
- [flag description]

Script preview (first 200 chars):
"[preview text]..."

Commands: /approve /reject /hold /skip [numbers] /redo_script
```

**Status response:**

```
PIPELINE STATUS
--------------------------------------------------
Gaming:      [status] | Last upload: [time ago]
Sports:      [status] | Last upload: [time ago]
Funny:       [status] | Last upload: [time ago]
Entertainment: [status] | Last upload: [time ago]

Queue: [n] videos pending review
Errors (24h): [n]
GPU utilization: [n]%
Disk free: [n] GB
```

---

## Appendix B: Video Description Template

```
[LLM-generated 2-3 sentence summary]

TIMESTAMPS:
00:00 - Introduction
00:18 - #10: [clip title]
01:45 - #9: [clip title]
...
[auto-generated from assembly timeline]

CREDITS:
All clips belong to their original creators. This video is a
commentary and news report on trending content.

#10: "[title]" by [creator] - [link]
#9: "[title]" by [creator] - [link]
...

---

Last SiX Hours brings you the most viral moments from the past
6 hours. New videos every 6 hours.

Subscribe: [channel link]
Gaming: [link]
Sports: [link]
Funny: [link]

#LastSiXHours #Viral #Trending #[niche]
```

---

## Appendix C: Glossary

| Term | Definition |
|---|---|
| Cycle | A single 6-hour coverage window |
| Pipeline run | One full execution of the pipeline for one niche in one cycle |
| Viral score | Composite score (0-1) measuring how viral a video is |
| View velocity | Rate of view accumulation (views per hour) |
| Clip | A 15-25 second extract from a source video |
| Niche | A content category (gaming, sports, funny, entertainment) |
| Most Replayed | YouTube's heatmap showing which segments viewers rewatch |
| Content ID | YouTube's automated copyright detection system |
| Lower third | Text overlay at the bottom of the screen showing clip info |
| CTA | Call to action (e.g., "Subscribe for more") |
| CPM | Cost per mille (revenue per 1,000 ad impressions) |
| LUFS | Loudness Units Full Scale (audio loudness measurement) |
| Ducking | Lowering background audio volume when narration plays |

---

**End of Specification**
