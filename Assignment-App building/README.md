---
title: Multimodal AI Explorer
emoji: 🤖
colorFrom: blue
colorTo: purple
sdk: gradio
sdk_version: 6.14.0
app_file: app_v2.py
pinned: false
---

# Multimodal AI Explorer

A web application that lets you explore **7 AI modalities** with **selectable models** across multiple providers — all from one UI.

---

## Modalities & Models

### 1. Text → Text
| Model | Provider |
|---|---|
| GPT-4o-mini | OpenAI |
| GPT-4o | OpenAI |
| Gemini 1.5 Flash | Google |
| Gemini 1.5 Pro | Google |
| Grok Beta | xAI via OpenRouter |
| Llama 3.1 8B (free) | OpenRouter |
| Llama 3.2 | Ollama (local) |
| Qwen 2.5 | Ollama (local) |
| DeepSeek R1 | Ollama (local) |
| Nemotron Super | Ollama (cloud) |
| Mistral 7B Instruct | HuggingFace |
| Zephyr 7B Beta | HuggingFace |
| Phi-3 Mini | HuggingFace |

### 2. Text → Image
| Model | Provider |
|---|---|
| DALL-E 3 | OpenAI |
| DALL-E 2 | OpenAI |
| FLUX.1-schnell | HuggingFace |
| Stable Diffusion XL | HuggingFace |
| Stable Diffusion v1.5 | HuggingFace |

### 3. Image → Text
| Model | Provider |
|---|---|
| Gemini 1.5 Flash | Google |
| Gemini 1.5 Pro | Google |
| GPT-4o (vision) | OpenAI |
| GPT-4o-mini (vision) | OpenAI |
| Llama 3.2 Vision | Ollama (local) |
| Qwen 2.5 VL | Ollama (local) |
| BLIP Large | HuggingFace |
| BLIP Base | HuggingFace |

### 4. Text → Audio
| Model / Voice | Provider |
|---|---|
| TTS-1 · Nova | OpenAI |
| TTS-1 · Alloy | OpenAI |
| TTS-1 · Shimmer | OpenAI |
| TTS-1 · Echo | OpenAI |
| TTS-1 · Fable | OpenAI |
| TTS-1 · Onyx | OpenAI |
| TTS-1-HD · Nova | OpenAI |
| TTS-1-HD · Alloy | OpenAI |

### 5. Audio → Text
| Model | Provider |
|---|---|
| Whisper-1 | OpenAI |
| Whisper Large v3 | Groq (fast) |
| Whisper Large v3 Turbo | Groq (fastest) |
| Whisper Large v3 | HuggingFace |
| Whisper Medium | HuggingFace |

### 6. Text → Video
| Model | Provider |
|---|---|
| minimax/video-01 | OpenRouter |

### 7. Video → Text
| Model | Provider |
|---|---|
| Gemini 1.5 Pro | Google |
| Gemini 1.5 Flash | Google |

---

## Requirements

### Python
Python 3.11 or higher recommended.

### Packages
Install all dependencies:
```bash
pip install -r requirements.txt
```

`requirements.txt` contents:
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

### Ollama (for local models only)
Download and install from [ollama.com/download](https://ollama.com/download), then pull the models you want:
```bash
ollama pull llama3.2
ollama pull qwen2.5
ollama pull deepseek-r1
ollama pull llama3.2-vision
ollama pull qwen2.5vl
```

---

## API Keys

You need API keys for the cloud providers. Create a `.env` file in the **project root** (one level above this folder):

```env
OPENAI_API_KEY=sk-...
GEMINI_API_KEY=AIza...
OPENROUTER_API_KEY=sk-or-...
HUGGINGFACE_API_KEY=hf_...
GROQ_API_KEY=gsk_...        # optional — free at console.groq.com
```

| Key | Get it from | Cost |
|---|---|---|
| `OPENAI_API_KEY` | platform.openai.com | Pay per use |
| `GEMINI_API_KEY` | aistudio.google.com | Free tier available |
| `OPENROUTER_API_KEY` | openrouter.ai | Pay per use |
| `HUGGINGFACE_API_KEY` | huggingface.co/settings/tokens | Free tier available |
| `GROQ_API_KEY` | console.groq.com | Free |

> Missing keys don't crash the app — those models will return an error message when called.

---

## Run Locally

```bash
# 1. Clone the repo
git clone https://github.com/VenkataraoKakarla/Full-Stack-GenAI-Bootcamp-1.0.git
cd "Full-Stack-GenAI-Bootcamp-1.0/Assignment-App building"

# 2. Create and activate a virtual environment (optional but recommended)
python -m venv env
env\Scripts\activate        # Windows
# source env/bin/activate   # Mac/Linux

# 3. Install dependencies
pip install -r requirements.txt

# 4. Add your API keys to .env (one level up — see API Keys section above)

# 5. Start Ollama (for local models) — runs in system tray after install

# 6. Launch the app
python app.py
```

The app opens at **http://localhost:7860**

---

## Deploy on HuggingFace Spaces

### Step 1 — Create a Space
Go to [huggingface.co/new-space](https://huggingface.co/new-space):
- SDK: **Gradio**
- Visibility: Public or Private

### Step 2 — Push files
```bash
cd "Assignment-App building"
git init
git add app.py requirements.txt README.md
git commit -m "Initial deployment"
git remote add space https://huggingface.co/spaces/YOUR_USERNAME/YOUR_SPACE_NAME
git push space master:main --force
```

Use your HF **write token** as the password when prompted
(generate at huggingface.co/settings/tokens).

### Step 3 — Add Secrets
In your Space → **Settings → Variables and Secrets → New Secret**:

| Secret Name | Value |
|---|---|
| `OPENAI_API_KEY` | your OpenAI key |
| `GEMINI_API_KEY` | your Gemini key |
| `OPENROUTER_API_KEY` | your OpenRouter key |
| `HUGGINGFACE_API_KEY` | your HF token |
| `GROQ_API_KEY` | your Groq key (optional) |
| `APP_USERNAME` | login username for the app |
| `APP_PASSWORD` | login password for the app |

> The app shows a login screen on HF Spaces if `APP_USERNAME` and `APP_PASSWORD` are set.
> Locally it runs without a login.

### Step 4 — Future updates
After any code change:
```bash
git add app.py
git commit -m "your message"
git push space master:main
```

> **Note:** Ollama models require a local Ollama server and will not work on HuggingFace Spaces. All other providers (OpenAI, Gemini, OpenRouter, HuggingFace, Groq) work on Spaces.

---

## Project Structure

```
Assignment-App building/
├── app.py              # Main Gradio application
├── requirements.txt    # Python dependencies
├── README.md           # This file
└── Assignment.pdf      # Original assignment brief
```

---

## Providers Summary

| Provider | Modalities Supported | API Key Required |
|---|---|---|
| OpenAI | Text→Text, Text→Image, Image→Text, Text→Audio, Audio→Text | Yes |
| Google Gemini | Text→Text, Image→Text, Video→Text | Yes |
| OpenRouter | Text→Text (Grok, Llama), Text→Video | Yes |
| HuggingFace | Text→Text, Text→Image, Image→Text, Audio→Text | Yes (free tier) |
| Groq | Audio→Text (fast Whisper) | Yes (free) |
| Ollama | Text→Text, Image→Text | No — runs locally |
