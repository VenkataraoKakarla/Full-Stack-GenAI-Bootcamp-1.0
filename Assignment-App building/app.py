import os
import time
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
# Load API keys from root .env
# ---------------------------------------------------------------------------
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Groq — free key from console.groq.com, add GROQ_API_KEY to .env
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
groq_client = openai.OpenAI(
    api_key=GROQ_API_KEY or "not-set",
    base_url="https://api.groq.com/openai/v1",
) if GROQ_API_KEY else None

# ---------------------------------------------------------------------------
# Modality 1 — Text → Text  (OpenAI GPT-4o-mini)
# ---------------------------------------------------------------------------
def text_to_text(prompt: str) -> str:
    if not prompt.strip():
        return "Please enter a prompt."
    try:
        resp = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Modality 2 — Text → Image  (OpenAI DALL-E 3)
# ---------------------------------------------------------------------------
def text_to_image(prompt: str):
    if not prompt.strip():
        return None
    try:
        resp = openai_client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            n=1,
        )
        img_bytes = requests.get(resp.data[0].url).content
        return Image.open(BytesIO(img_bytes))
    except Exception as e:
        print(f"Error: {e}")
        return None


# ---------------------------------------------------------------------------
# Modality 3 — Image → Text  (Google Gemini 1.5 Flash)
# ---------------------------------------------------------------------------
def image_to_text(image) -> str:
    if image is None:
        return "Please upload an image."
    try:
        resp = gemini_client.models.generate_content(
            model="gemini-1.5-flash",
            contents=["Describe this image in detail.", image],
        )
        return resp.text
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Modality 4 — Text → Audio  (OpenAI TTS-1, Nova voice)
# ---------------------------------------------------------------------------
def text_to_audio(text: str):
    if not text.strip():
        return None
    try:
        resp = openai_client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=text,
        )
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
        tmp.write(resp.content)
        return tmp.name
    except Exception as e:
        print(f"Error: {e}")
        return None


# ---------------------------------------------------------------------------
# Modality 5 — Audio → Text  (OpenAI Whisper-1)
# ---------------------------------------------------------------------------
def audio_to_text(audio_path: str) -> str:
    if audio_path is None:
        return "Please upload or record audio."
    try:
        with open(audio_path, "rb") as f:
            transcript = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
            )
        return transcript.text
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Modality 6 — Text → Video  (OpenRouter → minimax/video-01)
# ---------------------------------------------------------------------------
def text_to_video(prompt: str):
    if not prompt.strip():
        return None
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "minimax/video-01",
            "messages": [{"role": "user", "content": prompt}],
        }
        resp = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=120)
        data = resp.json()

        if "choices" not in data:
            print(f"Unexpected response: {data}")
            return None

        content = data["choices"][0]["message"]["content"]

        # If the model returns a direct video URL, download it
        if isinstance(content, str) and content.startswith("http"):
            video_bytes = requests.get(content, timeout=60).content
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            tmp.write(video_bytes)
            return tmp.name

        # Some models embed the URL in JSON or markdown — try to extract it
        import re
        urls = re.findall(r'https?://\S+\.mp4', content)
        if urls:
            video_bytes = requests.get(urls[0], timeout=60).content
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
            tmp.write(video_bytes)
            return tmp.name

        print(f"No video URL found in response: {content}")
        return None

    except Exception as e:
        print(f"Error: {e}")
        return None


# ---------------------------------------------------------------------------
# Modality 7 — Video → Text  (Google Gemini 1.5 Pro)
# ---------------------------------------------------------------------------
def video_to_text(video_path: str) -> str:
    if video_path is None:
        return "Please upload a video."
    try:
        video_file = gemini_client.files.upload(file=video_path)

        # Wait for Gemini to finish processing the video
        for _ in range(30):
            state = getattr(video_file.state, "name", str(video_file.state))
            if state != "PROCESSING":
                break
            time.sleep(3)
            video_file = gemini_client.files.get(name=video_file.name)

        state = getattr(video_file.state, "name", str(video_file.state))
        if state == "FAILED":
            return "Video processing failed. Please try a shorter or smaller video."

        resp = gemini_client.models.generate_content(
            model="gemini-1.5-pro",
            contents=[
                "Summarize this video. Describe what is happening, key details, and any notable moments.",
                video_file,
            ],
        )
        return resp.text
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Modality 8 — Text → Text  (xAI Grok via OpenRouter)
# ---------------------------------------------------------------------------
def text_to_text_grok(prompt: str) -> str:
    if not prompt.strip():
        return "Please enter a prompt."
    try:
        headers = {
            "Authorization": f"Bearer {OPENROUTER_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "x-ai/grok-beta",
            "messages": [{"role": "user", "content": prompt}],
        }
        resp = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
        data = resp.json()
        if "choices" not in data:
            return f"Error: {data}"
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Modality 9 — Audio → Text  (Groq Whisper-large-v3 — faster than OpenAI)
# ---------------------------------------------------------------------------
def audio_to_text_groq(audio_path: str) -> str:
    if audio_path is None:
        return "Please upload or record audio."
    if groq_client is None:
        return "GROQ_API_KEY not set. Get a free key at https://console.groq.com and add it to your .env file."
    try:
        with open(audio_path, "rb") as f:
            transcript = groq_client.audio.transcriptions.create(
                model="whisper-large-v3",
                file=f,
            )
        return transcript.text
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Modality 10 — Text → Text  (Ollama local — llama3.2)
# ---------------------------------------------------------------------------
def text_to_text_ollama(prompt: str) -> str:
    if not prompt.strip():
        return "Please enter a prompt."
    try:
        resp = ollama_client.chat(
            model="llama3.2",
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.message.content
    except Exception as e:
        return f"Error: {e}\n\nMake sure Ollama is running (check system tray) and llama3.2 is pulled."


# ---------------------------------------------------------------------------
# Gradio UI
# ---------------------------------------------------------------------------
with gr.Blocks(title="Multimodal AI Explorer", theme=gr.themes.Soft()) as demo:

    gr.Markdown("""
    # Multimodal AI Explorer
    Explore **10 AI modalities** powered by **OpenAI**, **Google Gemini**, **OpenRouter**, **xAI Grok**, **Groq**, and **Ollama (local)**.
    | # | Modality | Model | Provider |
    |---|---|---|---|
    | 1 | Text → Text | GPT-4o-mini | OpenAI |
    | 2 | Text → Image | DALL-E 3 | OpenAI |
    | 3 | Image → Text | Gemini 1.5 Flash | Google |
    | 4 | Text → Audio | TTS-1 (Nova) | OpenAI |
    | 5 | Audio → Text | Whisper-1 | OpenAI |
    | 6 | Text → Video | minimax/video-01 | OpenRouter |
    | 7 | Video → Text | Gemini 1.5 Pro | Google |
    | 8 | Text → Text (Grok) | grok-beta | xAI via OpenRouter |
    | 9 | Audio → Text (Groq) | whisper-large-v3 | Groq |
    | 10 | Text → Text (Ollama) | llama3.2 | Local / Ollama |
    """)

    with gr.Tabs():

        # --- Tab 1: Text → Text ---
        with gr.Tab("Text → Text"):
            gr.Markdown("### GPT-4o-mini — Chat / Q&A / Summarization")
            with gr.Row():
                with gr.Column():
                    t2t_in = gr.Textbox(label="Your prompt", lines=4,
                                        placeholder="Explain quantum computing in simple terms...")
                    t2t_btn = gr.Button("Generate", variant="primary")
                with gr.Column():
                    t2t_out = gr.Textbox(label="Response", lines=10)
            t2t_btn.click(text_to_text, inputs=t2t_in, outputs=t2t_out)

        # --- Tab 2: Text → Image ---
        with gr.Tab("Text → Image"):
            gr.Markdown("### DALL-E 3 — AI Image Generation")
            with gr.Row():
                with gr.Column():
                    t2i_in = gr.Textbox(label="Image prompt", lines=3,
                                        placeholder="A futuristic city skyline at sunset, digital art style...")
                    t2i_btn = gr.Button("Generate Image", variant="primary")
                with gr.Column():
                    t2i_out = gr.Image(label="Generated Image", type="pil")
            t2i_btn.click(text_to_image, inputs=t2i_in, outputs=t2i_out)

        # --- Tab 3: Image → Text ---
        with gr.Tab("Image → Text"):
            gr.Markdown("### Gemini 1.5 Flash — Image Captioning & Visual Analysis")
            with gr.Row():
                with gr.Column():
                    i2t_in = gr.Image(label="Upload Image", type="pil")
                    i2t_btn = gr.Button("Describe Image", variant="primary")
                with gr.Column():
                    i2t_out = gr.Textbox(label="Description", lines=10)
            i2t_btn.click(image_to_text, inputs=i2t_in, outputs=i2t_out)

        # --- Tab 4: Text → Audio ---
        with gr.Tab("Text → Audio"):
            gr.Markdown("### TTS-1 (Nova voice) — Text-to-Speech Synthesis")
            with gr.Row():
                with gr.Column():
                    t2a_in = gr.Textbox(label="Text to convert", lines=4,
                                        placeholder="Hello! Welcome to the multimodal AI explorer...")
                    t2a_btn = gr.Button("Generate Audio", variant="primary")
                with gr.Column():
                    t2a_out = gr.Audio(label="Generated Audio")
            t2a_btn.click(text_to_audio, inputs=t2a_in, outputs=t2a_out)

        # --- Tab 5: Audio → Text ---
        with gr.Tab("Audio → Text"):
            gr.Markdown("### Whisper-1 — Speech-to-Text Transcription")
            with gr.Row():
                with gr.Column():
                    a2t_in = gr.Audio(label="Upload or Record Audio", type="filepath")
                    a2t_btn = gr.Button("Transcribe", variant="primary")
                with gr.Column():
                    a2t_out = gr.Textbox(label="Transcription", lines=10)
            a2t_btn.click(audio_to_text, inputs=a2t_in, outputs=a2t_out)

        # --- Tab 6: Text → Video ---
        with gr.Tab("Text → Video"):
            gr.Markdown("### minimax/video-01 (via OpenRouter) — AI Video Generation")
            with gr.Row():
                with gr.Column():
                    t2v_in = gr.Textbox(label="Video prompt", lines=3,
                                        placeholder="A golden retriever running on a sunny beach...")
                    t2v_btn = gr.Button("Generate Video", variant="primary")
                    gr.Markdown("_Note: Video generation may take 1–2 minutes._")
                with gr.Column():
                    t2v_out = gr.Video(label="Generated Video")
            t2v_btn.click(text_to_video, inputs=t2v_in, outputs=t2v_out)

        # --- Tab 7: Video → Text ---
        with gr.Tab("Video → Text"):
            gr.Markdown("### Gemini 1.5 Pro — Video Understanding & Summarization")
            with gr.Row():
                with gr.Column():
                    v2t_in = gr.Video(label="Upload Video")
                    v2t_btn = gr.Button("Summarize Video", variant="primary")
                    gr.Markdown("_Note: Larger videos may take a moment to process._")
                with gr.Column():
                    v2t_out = gr.Textbox(label="Video Summary", lines=12)
            v2t_btn.click(video_to_text, inputs=v2t_in, outputs=v2t_out)

        # --- Tab 8: Text → Text (Grok via OpenRouter) ---
        with gr.Tab("Text → Text (Grok)"):
            gr.Markdown("### xAI Grok-beta (via OpenRouter) — Reasoning & Chat\n_Uses your existing OpenRouter key — no extra signup needed._")
            with gr.Row():
                with gr.Column():
                    grok_in = gr.Textbox(label="Your prompt", lines=4,
                                         placeholder="What's the difference between Grok and GPT-4o?")
                    grok_btn = gr.Button("Ask Grok", variant="primary")
                with gr.Column():
                    grok_out = gr.Textbox(label="Grok Response", lines=10)
            grok_btn.click(text_to_text_grok, inputs=grok_in, outputs=grok_out)

        # --- Tab 9: Audio → Text (Groq fast Whisper) ---
        with gr.Tab("Audio → Text (Groq)"):
            gr.Markdown("""### Groq — whisper-large-v3 (Ultra-fast Transcription)
_Requires a free `GROQ_API_KEY` from [console.groq.com](https://console.groq.com) — add it to your `.env` file._""")
            with gr.Row():
                with gr.Column():
                    groq_audio_in = gr.Audio(label="Upload or Record Audio", type="filepath")
                    groq_audio_btn = gr.Button("Transcribe with Groq", variant="primary")
                with gr.Column():
                    groq_audio_out = gr.Textbox(label="Transcription", lines=10)
            groq_audio_btn.click(audio_to_text_groq, inputs=groq_audio_in, outputs=groq_audio_out)

        # --- Tab 10: Text → Text (Ollama local) ---
        with gr.Tab("Text → Text (Ollama)"):
            gr.Markdown("### llama3.2 — Local Inference via Ollama (no API key needed)\n_Runs entirely on your machine. Make sure Ollama is running in the system tray._")
            with gr.Row():
                with gr.Column():
                    ollama_in = gr.Textbox(label="Your prompt", lines=4,
                                           placeholder="Tell me a fun fact about space...")
                    ollama_btn = gr.Button("Ask Llama 3.2", variant="primary")
                with gr.Column():
                    ollama_out = gr.Textbox(label="Response", lines=10)
            ollama_btn.click(text_to_text_ollama, inputs=ollama_in, outputs=ollama_out)

if __name__ == "__main__":
    demo.launch(share=False)
