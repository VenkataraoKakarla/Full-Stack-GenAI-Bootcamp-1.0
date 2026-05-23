import os
import re
import time
import base64
import tempfile
import requests
from io import BytesIO
from pathlib import Path

import gradio as gr
from dotenv import load_dotenv
from PIL import Image
import openai
from google import genai
import ollama as ollama_client

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = openai.OpenAI(
    api_key=GROQ_API_KEY or "not-set",
    base_url="https://api.groq.com/openai/v1",
) if GROQ_API_KEY else None

# ---------------------------------------------------------------------------
# Model Registries  {display label: (provider, model_id)}
# ---------------------------------------------------------------------------
T2T_MODELS = {
    "GPT-4o-mini  (OpenAI)":                ("openai",      "gpt-4o-mini"),
    "GPT-4o  (OpenAI)":                      ("openai",      "gpt-4o"),
    "Gemini 1.5 Flash  (Google)":            ("gemini",      "gemini-1.5-flash"),
    "Gemini 1.5 Pro  (Google)":              ("gemini",      "gemini-1.5-pro"),
    "Grok Beta  (xAI via OpenRouter)":       ("openrouter",  "x-ai/grok-beta"),
    "Llama 3.1 8B free  (OpenRouter)":       ("openrouter",  "meta-llama/llama-3.1-8b-instruct:free"),
    "Llama 3.2  (Ollama — local)":           ("ollama",      "llama3.2"),
    "Qwen 2.5  (Ollama — local)":            ("ollama",      "qwen2.5"),
    "DeepSeek R1  (Ollama — local)":         ("ollama",      "deepseek-r1"),
    "Nemotron Super  (Ollama — cloud)":      ("ollama",      "nemotron-3-super:cloud"),
}

T2I_MODELS = {
    "DALL-E 3  (OpenAI)":   ("openai", "dall-e-3"),
    "DALL-E 2  (OpenAI)":   ("openai", "dall-e-2"),
}

I2T_MODELS = {
    "Gemini 1.5 Flash  (Google)":          ("gemini", "gemini-1.5-flash"),
    "Gemini 1.5 Pro  (Google)":            ("gemini", "gemini-1.5-pro"),
    "GPT-4o  (OpenAI vision)":             ("openai", "gpt-4o"),
    "GPT-4o-mini  (OpenAI vision)":        ("openai", "gpt-4o-mini"),
    "Llama 3.2 Vision  (Ollama — local)":  ("ollama", "llama3.2-vision"),
    "Qwen 2.5 VL  (Ollama — local)":       ("ollama", "qwen2.5vl"),
}

# value format  "tts_model:voice"
T2A_MODELS = {
    "TTS-1 · Nova  (OpenAI)":       ("openai", "tts-1:nova"),
    "TTS-1 · Alloy  (OpenAI)":      ("openai", "tts-1:alloy"),
    "TTS-1 · Shimmer  (OpenAI)":    ("openai", "tts-1:shimmer"),
    "TTS-1 · Echo  (OpenAI)":       ("openai", "tts-1:echo"),
    "TTS-1 · Fable  (OpenAI)":      ("openai", "tts-1:fable"),
    "TTS-1 · Onyx  (OpenAI)":       ("openai", "tts-1:onyx"),
    "TTS-1-HD · Nova  (OpenAI)":    ("openai", "tts-1-hd:nova"),
    "TTS-1-HD · Alloy  (OpenAI)":   ("openai", "tts-1-hd:alloy"),
}

A2T_MODELS = {
    "Whisper-1  (OpenAI)":                      ("openai", "whisper-1"),
    "Whisper Large v3  (Groq — fast)":           ("groq",   "whisper-large-v3"),
    "Whisper Large v3 Turbo  (Groq — fastest)":  ("groq",   "whisper-large-v3-turbo"),
}

T2V_MODELS = {
    "minimax/video-01  (OpenRouter)": ("openrouter", "minimax/video-01"),
}

V2T_MODELS = {
    "Gemini 1.5 Pro  (Google)":   ("gemini", "gemini-1.5-pro"),
    "Gemini 1.5 Flash  (Google)": ("gemini", "gemini-1.5-flash"),
}

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def _pil_to_b64(image: Image.Image) -> str:
    buf = BytesIO()
    image.save(buf, format="JPEG")
    return base64.b64encode(buf.getvalue()).decode()

# ---------------------------------------------------------------------------
# Modality 1 — Text → Text
# ---------------------------------------------------------------------------
def run_text_to_text(prompt: str, model_label: str) -> str:
    if not prompt.strip():
        return "Please enter a prompt."
    provider, model_id = T2T_MODELS[model_label]
    try:
        if provider == "openai":
            resp = openai_client.chat.completions.create(
                model=model_id,
                messages=[{"role": "user", "content": prompt}],
            )
            return resp.choices[0].message.content

        elif provider == "gemini":
            resp = gemini_client.models.generate_content(model=model_id, contents=prompt)
            return resp.text

        elif provider == "openrouter":
            r = requests.post(OPENROUTER_URL, headers={
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "Content-Type": "application/json",
            }, json={"model": model_id, "messages": [{"role": "user", "content": prompt}]}, timeout=60)
            data = r.json()
            if "choices" not in data:
                return f"Error: {data}"
            return data["choices"][0]["message"]["content"]

        elif provider == "ollama":
            resp = ollama_client.chat(
                model=model_id,
                messages=[{"role": "user", "content": prompt}],
            )
            return resp.message.content

    except Exception as e:
        return f"Error ({model_label}): {e}"


# ---------------------------------------------------------------------------
# Modality 2 — Text → Image
# ---------------------------------------------------------------------------
def run_text_to_image(prompt: str, model_label: str):
    if not prompt.strip():
        return None
    provider, model_id = T2I_MODELS[model_label]
    try:
        if provider == "openai":
            size = "1024x1024" if model_id == "dall-e-3" else "512x512"
            resp = openai_client.images.generate(model=model_id, prompt=prompt, size=size, n=1)
            img_bytes = requests.get(resp.data[0].url).content
            return Image.open(BytesIO(img_bytes))
    except Exception as e:
        print(f"Error: {e}")
        return None


# ---------------------------------------------------------------------------
# Modality 3 — Image → Text
# ---------------------------------------------------------------------------
def run_image_to_text(image, model_label: str) -> str:
    if image is None:
        return "Please upload an image."
    provider, model_id = I2T_MODELS[model_label]
    try:
        if provider == "gemini":
            resp = gemini_client.models.generate_content(
                model=model_id,
                contents=["Describe this image in detail.", image],
            )
            return resp.text

        elif provider == "openai":
            b64 = _pil_to_b64(image)
            resp = openai_client.chat.completions.create(
                model=model_id,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Describe this image in detail."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}},
                    ],
                }],
            )
            return resp.choices[0].message.content

        elif provider == "ollama":
            buf = BytesIO()
            image.save(buf, format="JPEG")
            resp = ollama_client.chat(
                model=model_id,
                messages=[{
                    "role": "user",
                    "content": "Describe this image in detail.",
                    "images": [buf.getvalue()],
                }],
            )
            return resp.message.content

    except Exception as e:
        return f"Error ({model_label}): {e}"


# ---------------------------------------------------------------------------
# Modality 4 — Text → Audio
# ---------------------------------------------------------------------------
def run_text_to_audio(text: str, model_label: str):
    if not text.strip():
        return None
    provider, model_voice = T2A_MODELS[model_label]
    tts_model, voice = model_voice.split(":")
    try:
        if provider == "openai":
            resp = openai_client.audio.speech.create(model=tts_model, voice=voice, input=text)
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            tmp.write(resp.content)
            return tmp.name
    except Exception as e:
        print(f"Error: {e}")
        return None


# ---------------------------------------------------------------------------
# Modality 5 — Audio → Text
# ---------------------------------------------------------------------------
def run_audio_to_text(audio_path: str, model_label: str) -> str:
    if audio_path is None:
        return "Please upload or record audio."
    provider, model_id = A2T_MODELS[model_label]
    try:
        if provider == "openai":
            with open(audio_path, "rb") as f:
                t = openai_client.audio.transcriptions.create(model=model_id, file=f)
            return t.text

        elif provider == "groq":
            if groq_client is None:
                return "GROQ_API_KEY not set — get a free key at https://console.groq.com and add it to .env"
            with open(audio_path, "rb") as f:
                t = groq_client.audio.transcriptions.create(model=model_id, file=f)
            return t.text

    except Exception as e:
        return f"Error ({model_label}): {e}"


# ---------------------------------------------------------------------------
# Modality 6 — Text → Video
# ---------------------------------------------------------------------------
def run_text_to_video(prompt: str, model_label: str):
    if not prompt.strip():
        return None
    provider, model_id = T2V_MODELS[model_label]
    try:
        if provider == "openrouter":
            r = requests.post(OPENROUTER_URL, headers={
                "Authorization": f"Bearer {OPENROUTER_KEY}",
                "Content-Type": "application/json",
            }, json={"model": model_id, "messages": [{"role": "user", "content": prompt}]}, timeout=120)
            data = r.json()
            if "choices" not in data:
                print(f"Unexpected response: {data}")
                return None
            content = data["choices"][0]["message"]["content"]
            if isinstance(content, str) and content.startswith("http"):
                vb = requests.get(content, timeout=60).content
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                tmp.write(vb)
                return tmp.name
            urls = re.findall(r'https?://\S+\.mp4', content)
            if urls:
                vb = requests.get(urls[0], timeout=60).content
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                tmp.write(vb)
                return tmp.name
            print(f"No video URL in response: {content}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None


# ---------------------------------------------------------------------------
# Modality 7 — Video → Text
# ---------------------------------------------------------------------------
def run_video_to_text(video_path: str, model_label: str) -> str:
    if video_path is None:
        return "Please upload a video."
    provider, model_id = V2T_MODELS[model_label]
    try:
        if provider == "gemini":
            video_file = gemini_client.files.upload(file=video_path)
            for _ in range(30):
                state = getattr(video_file.state, "name", str(video_file.state))
                if state != "PROCESSING":
                    break
                time.sleep(3)
                video_file = gemini_client.files.get(name=video_file.name)
            if getattr(video_file.state, "name", str(video_file.state)) == "FAILED":
                return "Video processing failed. Try a shorter/smaller file."
            resp = gemini_client.models.generate_content(
                model=model_id,
                contents=[
                    "Summarize this video. Describe what is happening, key details, and any notable moments.",
                    video_file,
                ],
            )
            return resp.text
    except Exception as e:
        return f"Error ({model_label}): {e}"


# ---------------------------------------------------------------------------
# Gradio UI
# ---------------------------------------------------------------------------
with gr.Blocks(title="Multimodal AI Explorer", theme=gr.themes.Soft()) as demo:

    gr.Markdown("""
    # Multimodal AI Explorer
    Select a **model** from the dropdown in each tab, then run the modality.
    Providers: **OpenAI · Google Gemini · OpenRouter · xAI Grok · Groq · Ollama (local)**
    """)

    with gr.Tabs():

        # ── Tab 1: Text → Text ──────────────────────────────────────────────
        with gr.Tab("Text → Text"):
            with gr.Row():
                with gr.Column(scale=1):
                    t2t_model = gr.Dropdown(
                        choices=list(T2T_MODELS.keys()),
                        value=list(T2T_MODELS.keys())[0],
                        label="Model",
                    )
                    t2t_in = gr.Textbox(label="Prompt", lines=5,
                                        placeholder="Explain quantum computing in simple terms...")
                    t2t_btn = gr.Button("Generate", variant="primary")
                with gr.Column(scale=1):
                    t2t_out = gr.Textbox(label="Response", lines=12)
            t2t_btn.click(run_text_to_text, inputs=[t2t_in, t2t_model], outputs=t2t_out)

        # ── Tab 2: Text → Image ─────────────────────────────────────────────
        with gr.Tab("Text → Image"):
            with gr.Row():
                with gr.Column(scale=1):
                    t2i_model = gr.Dropdown(
                        choices=list(T2I_MODELS.keys()),
                        value=list(T2I_MODELS.keys())[0],
                        label="Model",
                    )
                    t2i_in = gr.Textbox(label="Image prompt", lines=4,
                                        placeholder="A futuristic city at sunset, digital art style...")
                    t2i_btn = gr.Button("Generate Image", variant="primary")
                with gr.Column(scale=1):
                    t2i_out = gr.Image(label="Generated Image", type="pil")
            t2i_btn.click(run_text_to_image, inputs=[t2i_in, t2i_model], outputs=t2i_out)

        # ── Tab 3: Image → Text ─────────────────────────────────────────────
        with gr.Tab("Image → Text"):
            with gr.Row():
                with gr.Column(scale=1):
                    i2t_model = gr.Dropdown(
                        choices=list(I2T_MODELS.keys()),
                        value=list(I2T_MODELS.keys())[0],
                        label="Model",
                    )
                    i2t_in = gr.Image(label="Upload Image", type="pil")
                    i2t_btn = gr.Button("Describe Image", variant="primary")
                with gr.Column(scale=1):
                    i2t_out = gr.Textbox(label="Description", lines=12)
            i2t_btn.click(run_image_to_text, inputs=[i2t_in, i2t_model], outputs=i2t_out)

        # ── Tab 4: Text → Audio ─────────────────────────────────────────────
        with gr.Tab("Text → Audio"):
            with gr.Row():
                with gr.Column(scale=1):
                    t2a_model = gr.Dropdown(
                        choices=list(T2A_MODELS.keys()),
                        value=list(T2A_MODELS.keys())[0],
                        label="Model / Voice",
                    )
                    t2a_in = gr.Textbox(label="Text to speak", lines=4,
                                        placeholder="Hello! Welcome to the multimodal AI explorer...")
                    t2a_btn = gr.Button("Generate Audio", variant="primary")
                with gr.Column(scale=1):
                    t2a_out = gr.Audio(label="Generated Audio")
            t2a_btn.click(run_text_to_audio, inputs=[t2a_in, t2a_model], outputs=t2a_out)

        # ── Tab 5: Audio → Text ─────────────────────────────────────────────
        with gr.Tab("Audio → Text"):
            with gr.Row():
                with gr.Column(scale=1):
                    a2t_model = gr.Dropdown(
                        choices=list(A2T_MODELS.keys()),
                        value=list(A2T_MODELS.keys())[0],
                        label="Model",
                    )
                    a2t_in = gr.Audio(label="Upload or Record Audio", type="filepath")
                    a2t_btn = gr.Button("Transcribe", variant="primary")
                with gr.Column(scale=1):
                    a2t_out = gr.Textbox(label="Transcription", lines=12)
            a2t_btn.click(run_audio_to_text, inputs=[a2t_in, a2t_model], outputs=a2t_out)

        # ── Tab 6: Text → Video ─────────────────────────────────────────────
        with gr.Tab("Text → Video"):
            with gr.Row():
                with gr.Column(scale=1):
                    t2v_model = gr.Dropdown(
                        choices=list(T2V_MODELS.keys()),
                        value=list(T2V_MODELS.keys())[0],
                        label="Model",
                    )
                    t2v_in = gr.Textbox(label="Video prompt", lines=4,
                                        placeholder="A golden retriever running on a sunny beach...")
                    t2v_btn = gr.Button("Generate Video", variant="primary")
                    gr.Markdown("_Video generation may take 1–2 minutes._")
                with gr.Column(scale=1):
                    t2v_out = gr.Video(label="Generated Video")
            t2v_btn.click(run_text_to_video, inputs=[t2v_in, t2v_model], outputs=t2v_out)

        # ── Tab 7: Video → Text ─────────────────────────────────────────────
        with gr.Tab("Video → Text"):
            with gr.Row():
                with gr.Column(scale=1):
                    v2t_model = gr.Dropdown(
                        choices=list(V2T_MODELS.keys()),
                        value=list(V2T_MODELS.keys())[0],
                        label="Model",
                    )
                    v2t_in = gr.Video(label="Upload Video")
                    v2t_btn = gr.Button("Summarize Video", variant="primary")
                    gr.Markdown("_Larger videos may take a moment to process._")
                with gr.Column(scale=1):
                    v2t_out = gr.Textbox(label="Video Summary", lines=12)
            v2t_btn.click(run_video_to_text, inputs=[v2t_in, v2t_model], outputs=v2t_out)

if __name__ == "__main__":
    demo.launch(share=False)
