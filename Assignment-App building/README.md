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

Explore **10 AI modalities** with selectable models across **OpenAI, Google Gemini, HuggingFace, OpenRouter, xAI Grok, Groq, and Ollama**.

| # | Modality | Models Available |
|---|---|---|
| 1 | Text → Text | GPT-4o, Gemini, Grok, Llama, Mistral, Phi-3, Zephyr |
| 2 | Text → Image | DALL-E 3, FLUX.1, Stable Diffusion XL |
| 3 | Image → Text | GPT-4o, Gemini, BLIP |
| 4 | Text → Audio | OpenAI TTS-1 / TTS-1-HD (6 voices) |
| 5 | Audio → Text | Whisper (OpenAI · Groq · HuggingFace) |
| 6 | Text → Video | minimax/video-01 via OpenRouter |
| 7 | Video → Text | Gemini 1.5 Pro / Flash |

## Setup (Secrets required)

Add the following as **Secrets** in your Space settings:

| Secret Name | Where to get it |
|---|---|
| `OPENAI_API_KEY` | platform.openai.com |
| `GEMINI_API_KEY` | aistudio.google.com |
| `OPENROUTER_API_KEY` | openrouter.ai |
| `HUGGINGFACE_API_KEY` | huggingface.co/settings/tokens |
| `GROQ_API_KEY` | console.groq.com (free) |

> Note: Ollama tabs require a local Ollama server and will not work on HuggingFace Spaces.

cd "D:\Full-Stack-GenAI-Bootcamp-1.0\Assignment-App building"
git init
git add app.py requirements.txt README.md
git commit -m "Initial deployment"
git remote add space https://huggingface.co/spaces/VenkataraoKakarla/multimodal-ai-explorer
git push space main

