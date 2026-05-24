---
title: Multimodal AI Explorer
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 6.14.0
app_file: app.py
pinned: false
---

# Multimodal AI Explorer

A web application exploring **7 AI modalities** with **selectable models** across multiple providers — OpenAI, Google Gemini, HuggingFace, OpenRouter, Groq, and Ollama.

---

## App Versions

Three versions are available — pick based on your use case:

| File | API Keys | Modalities | Best for |
|---|---|---|---|
| `app.py` | Your `.env` / HF Secrets | All 7 | Local dev with your own keys |
| `app_v2.py` | User enters in UI | All 7 | Public Space — users bring all keys |
| `app_v3_hf_only.py` | User enters HF token only | 3 (free) | Public Space — fully free, no billing risk |

To switch which version runs on HF Spaces, change one line in this README:
```
app_file: app_v3_hf_only.py   ← current
app_file: app_v2.py
app_file: app.py
```

---

## Modalities & Models

### app.py / app_v2.py — Full Version (All 7 Modalities)

#### 1. Text → Text
| Model | Provider |
|---|---|
| GPT-4o-mini, GPT-4o | OpenAI |
| Gemini 1.5 Flash, Gemini 1.5 Pro | Google |
| Grok Beta | xAI via OpenRouter |
| Llama 3.1 8B (free) | OpenRouter |
| Llama 3.2, Qwen 2.5, DeepSeek R1, Nemotron Super | Ollama (local) |
| Mistral 7B Instruct, Zephyr 7B Beta, Phi-3 Mini | HuggingFace |

#### 2. Text → Image
| Model | Provider |
|---|---|
| DALL-E 3, DALL-E 2 | OpenAI |
| FLUX.1-schnell, Stable Diffusion XL, SD v1.5 | HuggingFace |

#### 3. Image → Text
| Model | Provider |
|---|---|
| Gemini 1.5 Flash, Gemini 1.5 Pro | Google |
| GPT-4o, GPT-4o-mini (vision) | OpenAI |
| Llama 3.2 Vision, Qwen 2.5 VL | Ollama (local) |
| BLIP Large, BLIP Base | HuggingFace |

#### 4. Text → Audio
| Model / Voice | Provider |
|---|---|
| TTS-1 & TTS-1-HD · Nova / Alloy / Shimmer / Echo / Fable / Onyx | OpenAI |

#### 5. Audio → Text
| Model | Provider |
|---|---|
| Whisper-1 | OpenAI |
| Whisper Large v3, Whisper Large v3 Turbo | Groq |
| Whisper Large v3, Whisper Medium | HuggingFace |

#### 6. Text → Video
| Model | Provider |
|---|---|
| minimax/video-01 | OpenRouter |

#### 7. Video → Text
| Model | Provider |
|---|---|
| Gemini 1.5 Pro, Gemini 1.5 Flash | Google |

---

### app_v3_hf_only.py — HuggingFace Free Version (3 Modalities)

> Only rate-limited models — no HF credits consumed, safe to make fully public.

| Modality | Models |
|---|---|
| Text → Text | Mistral 7B Instruct, Zephyr 7B Beta, Phi-3 Mini |
| Image → Text | BLIP Large, BLIP Base |
| Audio → Text | Whisper Large v3, Whisper Medium |

---

## Requirements

### Python
Python 3.11 or higher recommended.

### Install packages
```bash
pip install -r requirements.txt
```

```
gradio>=6.0.0
openai>=1.0.0
google-genai>=1.0.0
python-dotenv>=1.0.0
requests>=2.31.0
Pillow>=10.0.0
groq>=0.9.0
ollama>=0.6.0
huggingface_hub>=0.20.0
```

### Ollama (local models only)
Download from [ollama.com/download](https://ollama.com/download), then pull models:
```bash
ollama pull llama3.2
ollama pull qwen2.5
ollama pull deepseek-r1
ollama pull llama3.2-vision
ollama pull qwen2.5vl
```

---

## API Keys

For `app.py`, create a `.env` file one level above this folder:

```env
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=AIza...
OPENROUTER_API_KEY=sk-or-...
HUGGINGFACE_API_KEY=hf_...
GROQ_API_KEY=gsk_...
```

| Key | Get it from | Cost |
|---|---|---|
| `OPENAI_API_KEY` | platform.openai.com | Pay per use |
| `GEMINI_API_KEY` | aistudio.google.com | Free tier available |
| `OPENROUTER_API_KEY` | openrouter.ai | Pay per use |
| `HUGGINGFACE_API_KEY` | huggingface.co/settings/tokens | Free tier |
| `GROQ_API_KEY` | console.groq.com | Free |

> `app_v2.py` and `app_v3_hf_only.py` don't use `.env` — users enter keys in the UI.

---

## Run Locally

```bash
# 1. Clone the repo
git clone https://github.com/VenkataraoKakarla/Full-Stack-GenAI-Bootcamp-1.0.git
cd "Full-Stack-GenAI-Bootcamp-1.0/Assignment-App building"

# 2. Install dependencies
pip install -r requirements.txt

# 3. Add your API keys to .env (one level up) — only needed for app.py

# 4. Start Ollama if using local models (runs in system tray)

# 5. Launch whichever version you want
python app.py                # v1 — uses .env keys, all 7 modalities
python app_v2.py             # v2 — user enters all keys in UI
python app_v3_hf_only.py     # v3 — HF token only, 3 free modalities
```

App opens at **http://localhost:7860**

---

## Deploy on HuggingFace Spaces

### First-time setup

```bash
# Navigate to the app folder
cd "D:\Full-Stack-GenAI-Bootcamp-1.0\Assignment-App building"

# Initialise git (only needed once)
git init

# Stage the app files
git add app.py app_v2.py app_v3_hf_only.py requirements.txt README.md

# Commit
git commit -m "Initial deployment"

# Add HF Space as a remote (only needed once)
git remote add space https://huggingface.co/spaces/VenkataraoKakarla/multimodal-ai-explorer

# Push  (use HF write token as password when prompted)
git push space master:main --force
```

> Get a **write token** at huggingface.co/settings/tokens → New token → Role: Write

---

### Push updates (after any code or README change)

```bash
# Stage changed files
git add app_v3_hf_only.py          # or whichever file changed
git add README.md                   # if README changed

# Commit with a message
git commit -m "describe your change"

# Push to HF Spaces
git push space master:main
```

**Full one-liner for quick updates:**
```bash
git -C "D:\Full-Stack-GenAI-Bootcamp-1.0\Assignment-App building" add -A && git -C "D:\Full-Stack-GenAI-Bootcamp-1.0\Assignment-App building" commit -m "update" && git -C "D:\Full-Stack-GenAI-Bootcamp-1.0\Assignment-App building" push space master:main
```

---

### Switch active version on HF Spaces

Edit line 8 of this README, then push:
```bash
# To switch to v2
sed -i 's/app_file: .*/app_file: app_v2.py/' README.md
git add README.md && git commit -m "Switch to app_v2" && git push space master:main

# To switch to v3 (HF free)
sed -i 's/app_file: .*/app_file: app_v3_hf_only.py/' README.md
git add README.md && git commit -m "Switch to app_v3" && git push space master:main
```

Or just edit `app_file:` in this README manually and push.

---

### Add Secrets (for app.py only)

In your Space → **Settings → Variables and Secrets → New Secret**:

| Secret | Value |
|---|---|
| `OPENAI_API_KEY` | your OpenAI key |
| `GEMINI_API_KEY` | your Gemini key |
| `OPENROUTER_API_KEY` | your OpenRouter key |
| `HUGGINGFACE_API_KEY` | your HF token |
| `GROQ_API_KEY` | your Groq key |
| `APP_USERNAME` | login username (optional auth) |
| `APP_PASSWORD` | login password (optional auth) |

> `app_v2.py` and `app_v3_hf_only.py` do not need Secrets — users enter keys in the UI.

---

## Project Structure

```
Assignment-App building/
├── app.py                  # v1 — full app, reads keys from .env
├── app_v2.py               # v2 — full app, user enters all keys in UI
├── app_v3_hf_only.py       # v3 — HF-only, free, 3 modalities
├── requirements.txt        # Python dependencies
├── README.md               # This file (also HF Space config)
└── Assignment.pdf          # Original assignment brief
```

---

## Provider Summary

| Provider | Modalities | Key Required | Cost |
|---|---|---|---|
| OpenAI | Text↔Text, Text→Image, Image→Text, Text→Audio, Audio→Text | Yes | Pay per use |
| Google Gemini | Text→Text, Image→Text, Video→Text | Yes | Free tier |
| OpenRouter | Text→Text (Grok/Llama), Text→Video | Yes | Pay per use |
| HuggingFace | Text→Text, Image→Text, Audio→Text | Yes | Free (rate limited) |
| Groq | Audio→Text (fast Whisper) | Yes | Free |
| Ollama | Text→Text, Image→Text | No | Local only |
