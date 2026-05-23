# Multimodal AI Model Exploration & Web Application Development

A hands-on assignment exploring different AI model providers across multiple input-output modalities, culminating in a working multimodal web application.

---

## Overview

This project demonstrates how modern AI models handle text, image, audio, and video-based tasks. It consists of two deliverables:

1. **Jupyter/Colab Notebook** — model exploration across modalities using different providers
2. **Web Application** — an interactive UI where users can provide inputs in multiple modalities and receive AI-generated outputs

---

## AI Platforms Used

| Platform | Website |
|---|---|
| OpenAI | platform.openai.com |
| Claude (Anthropic) | console.anthropic.com |
| Google Gemini | ai.google.dev |
| Groq | console.groq.com |
| OpenRouter | openrouter.ai |
| Hugging Face | huggingface.co |

---

## Supported Modalities

| Input | Output | Description |
|---|---|---|
| Text | Text | Chat / instruction-following / summarization |
| Text | Image | AI image generation from text prompts |
| Image | Text | Image captioning / visual question answering |
| Text | Audio | Text-to-speech synthesis |
| Audio | Text | Speech-to-text transcription |
| Text | Video | AI video generation from text prompts |
| Video | Text | Video understanding / summarization |

**Optional (not required):**
- Image → Image
- Audio → Audio

---

## Models Used

| Modality | Model | Provider |
|---|---|---|
| Text → Text | *(add model name)* | *(add provider)* |
| Text → Image | *(add model name)* | *(add provider)* |
| Image → Text | *(add model name)* | *(add provider)* |
| Text → Audio | *(add model name)* | *(add provider)* |
| Audio → Text | *(add model name)* | *(add provider)* |
| Text → Video | *(add model name)* | *(add provider)* |
| Video → Text | *(add model name)* | *(add provider)* |

> Fill in the table above with the specific models you selected for each modality.

---

## Project Structure

```
Assignment-App building/
├── notebook/
│   └── multimodal_exploration.ipynb   # Task 1: Model exploration notebook
├── webapp/
│   ├── app.py                         # Main web application (Flask/Streamlit/Gradio)
│   ├── requirements.txt               # Python dependencies
│   └── ...
├── screenshots/                       # Screenshots or demo video
├── Assignment.pdf                     # Original assignment brief
└── README.md
```

---

## Task 1: Notebook

The notebook covers each modality end-to-end:

- Model selection (different from live class examples)
- API setup and model loading
- Sample input provided for each modality
- Output generated and displayed clearly

**To run the notebook:**

```bash
pip install -r notebook/requirements.txt
jupyter notebook notebook/multimodal_exploration.ipynb
```

Or open directly in [Google Colab](https://colab.research.google.com/).

---

## Task 2: Web Application

The web app provides a unified interface for all modalities.

**Supported Inputs:**
- Text input (prompt / question)
- Image upload
- Audio upload or live recording
- Video upload

**Supported Outputs:**
- Text response
- Generated image
- Generated audio
- Transcribed text
- Generated video
- Video summary / description

**To run the web app:**

```bash
cd webapp
pip install -r requirements.txt
python app.py
```

Then open `http://localhost:7860` (or the port shown in your terminal).

---

## Setup & API Keys

Create a `.env` file in the `webapp/` directory with your API keys:

```env
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
GOOGLE_API_KEY=your_key_here
GROQ_API_KEY=your_key_here
OPENROUTER_API_KEY=your_key_here
HF_TOKEN=your_key_here
```

> Never commit your `.env` file. It is listed in `.gitignore`.

---

## Screenshots / Demo

> Add screenshots or a link to a demo video here.

---

## Evaluation Criteria

- [ ] Correct model selection for each modality
- [ ] Successful notebook execution with visible outputs
- [ ] Coverage of all required modalities (7 required)
- [ ] Working web application with multi-modal support
- [ ] Clean, readable code quality
- [ ] Complete README documentation
- [ ] Creativity and presentation

---

## Final Goal

Build a working multimodal AI system that accepts text, image, audio, or video input and generates meaningful AI-powered outputs using state-of-the-art models from multiple providers.
