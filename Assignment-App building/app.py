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
import google.generativeai as genai

# ---------------------------------------------------------------------------
# Load API keys from root .env
# ---------------------------------------------------------------------------
load_dotenv(dotenv_path=Path(__file__).parent.parent / ".env")

openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
OPENROUTER_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

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
        model = genai.GenerativeModel("gemini-1.5-flash")
        resp = model.generate_content(["Describe this image in detail.", image])
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
        resp.stream_to_file(tmp.name)
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
        model = genai.GenerativeModel("gemini-1.5-pro")
        video_file = genai.upload_file(video_path)

        # Wait for Gemini to finish processing the video
        for _ in range(30):
            if video_file.state.name != "PROCESSING":
                break
            time.sleep(3)
            video_file = genai.get_file(video_file.name)

        if video_file.state.name == "FAILED":
            return "Video processing failed. Please try a shorter or smaller video."

        resp = model.generate_content([
            "Summarize this video. Describe what is happening, key details, and any notable moments.",
            video_file,
        ])
        return resp.text
    except Exception as e:
        return f"Error: {e}"


# ---------------------------------------------------------------------------
# Gradio UI
# ---------------------------------------------------------------------------
with gr.Blocks(title="Multimodal AI Explorer", theme=gr.themes.Soft()) as demo:

    gr.Markdown("""
    # Multimodal AI Explorer
    Explore **7 AI modalities** powered by **OpenAI**, **Google Gemini**, and **OpenRouter**.
    | Modality | Model | Provider |
    |---|---|---|
    | Text → Text | GPT-4o-mini | OpenAI |
    | Text → Image | DALL-E 3 | OpenAI |
    | Image → Text | Gemini 1.5 Flash | Google |
    | Text → Audio | TTS-1 (Nova) | OpenAI |
    | Audio → Text | Whisper-1 | OpenAI |
    | Text → Video | minimax/video-01 | OpenRouter |
    | Video → Text | Gemini 1.5 Pro | Google |
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

if __name__ == "__main__":
    demo.launch(share=False)
