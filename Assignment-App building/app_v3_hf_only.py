"""
app_v3_hf_only.py
-----------------
HuggingFace-only version. Users provide their own HF token.
Only safe modalities included (rate-limited, no credit consumption):
  - Text  → Text   (Mistral, Zephyr, Phi-3)
  - Image → Text   (BLIP Large / Base)
  - Audio → Text   (Whisper Large v3 / Medium)

Image Generation is intentionally excluded — FLUX / SDXL consume HF credits.
"""

import gradio as gr
from huggingface_hub import InferenceClient

# ---------------------------------------------------------------------------
# Model Registries
# ---------------------------------------------------------------------------
T2T_MODELS = {
    "Mistral 7B Instruct":  "mistralai/Mistral-7B-Instruct-v0.3",
    "Zephyr 7B Beta":       "HuggingFaceH4/zephyr-7b-beta",
    "Phi-3 Mini":           "microsoft/Phi-3-mini-4k-instruct",
}

I2T_MODELS = {
    "BLIP Large  (image captioning)": "Salesforce/blip-image-captioning-large",
    "BLIP Base   (image captioning)": "Salesforce/blip-image-captioning-base",
}

A2T_MODELS = {
    "Whisper Large v3": "openai/whisper-large-v3",
    "Whisper Medium":   "openai/whisper-medium",
}

# ---------------------------------------------------------------------------
# Helper — build a client from the user's token
# ---------------------------------------------------------------------------
def _client(token: str) -> InferenceClient:
    t = token.strip()
    if not t:
        raise ValueError("Please enter your HuggingFace token above and click Save.")
    return InferenceClient(token=t)

# ---------------------------------------------------------------------------
# Save token handler
# ---------------------------------------------------------------------------
def save_token(token: str):
    t = token.strip()
    if not t:
        return "", "⚠️  No token entered. Paste your HF token and click Save."
    if not t.startswith("hf_"):
        return t, "⚠️  Token looks unusual — HF tokens start with 'hf_'. Double-check it."
    return t, f"✅  Token saved ({t[:8]}...{t[-4:]}). You can now use all tabs."

# ---------------------------------------------------------------------------
# Modality 1 — Text → Text
# ---------------------------------------------------------------------------
def run_text_to_text(prompt: str, model_label: str, token: str) -> str:
    if not prompt.strip():
        return "Please enter a prompt."
    try:
        client = _client(token)
        result = client.chat.completions.create(
            model=T2T_MODELS[model_label],
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024,
        )
        return result.choices[0].message.content
    except Exception as e:
        return f"Error: {e}"

# ---------------------------------------------------------------------------
# Modality 2 — Image → Text
# ---------------------------------------------------------------------------
def run_image_to_text(image, model_label: str, token: str) -> str:
    if image is None:
        return "Please upload an image."
    try:
        client = _client(token)
        return client.image_to_text(image, model=I2T_MODELS[model_label])
    except Exception as e:
        return f"Error: {e}"

# ---------------------------------------------------------------------------
# Modality 3 — Audio → Text
# ---------------------------------------------------------------------------
def run_audio_to_text(audio_path: str, model_label: str, token: str) -> str:
    if audio_path is None:
        return "Please upload or record audio."
    try:
        client = _client(token)
        result = client.automatic_speech_recognition(
            audio_path,
            model=A2T_MODELS[model_label],
        )
        return result.text
    except Exception as e:
        return f"Error: {e}"

# ---------------------------------------------------------------------------
# Gradio UI
# ---------------------------------------------------------------------------
with gr.Blocks(title="Multimodal AI — HuggingFace Edition") as demo:

    # Per-session token state
    session_token = gr.State("")

    gr.Markdown("""
    # Multimodal AI Explorer — HuggingFace Edition
    **100% free.** All models run via the HuggingFace Inference API (rate-limited, no billing).
    Enter your own HF token below — it lives only in your session and is never stored.

    Get a free token at [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens) → **New token → Role: Read**
    """)

    # ── Token Panel ──────────────────────────────────────────────────────────
    with gr.Accordion("🔑 HuggingFace Token — expand to configure", open=True):
        with gr.Row():
            token_input  = gr.Textbox(
                label="HuggingFace Token",
                type="password",
                placeholder="hf_...",
                scale=3,
            )
            save_btn     = gr.Button("Save Token", variant="primary", scale=1)
        token_status = gr.Textbox(
            label="Status",
            interactive=False,
            value="Paste your HF token above and click Save to begin.",
        )

    save_btn.click(save_token, inputs=token_input, outputs=[session_token, token_status])

    gr.Markdown("---")
    gr.Markdown("""
    > **Why no Text → Image tab?**
    > Image generation models (FLUX, Stable Diffusion) consume HuggingFace credits.
    > This version only uses rate-limited models so it stays completely free.
    """)

    with gr.Tabs():

        # ── Tab 1: Text → Text ───────────────────────────────────────────────
        with gr.Tab("Text → Text"):
            gr.Markdown("**Free models:** Mistral 7B · Zephyr 7B · Phi-3 Mini")
            with gr.Row():
                with gr.Column(scale=1):
                    t2t_model = gr.Dropdown(
                        choices=list(T2T_MODELS.keys()),
                        value=list(T2T_MODELS.keys())[0],
                        label="Model",
                    )
                    t2t_in  = gr.Textbox(
                        label="Prompt", lines=5,
                        placeholder="Explain the difference between machine learning and deep learning...",
                    )
                    t2t_btn = gr.Button("Generate", variant="primary")
                with gr.Column(scale=1):
                    t2t_out = gr.Textbox(label="Response", lines=12)
            t2t_btn.click(
                run_text_to_text,
                inputs=[t2t_in, t2t_model, session_token],
                outputs=t2t_out,
            )

        # ── Tab 2: Image → Text ──────────────────────────────────────────────
        with gr.Tab("Image → Text"):
            gr.Markdown("**Free models:** BLIP Large · BLIP Base — image captioning")
            with gr.Row():
                with gr.Column(scale=1):
                    i2t_model = gr.Dropdown(
                        choices=list(I2T_MODELS.keys()),
                        value=list(I2T_MODELS.keys())[0],
                        label="Model",
                    )
                    i2t_in  = gr.Image(label="Upload Image", type="pil")
                    i2t_btn = gr.Button("Describe Image", variant="primary")
                with gr.Column(scale=1):
                    i2t_out = gr.Textbox(label="Caption / Description", lines=12)
            i2t_btn.click(
                run_image_to_text,
                inputs=[i2t_in, i2t_model, session_token],
                outputs=i2t_out,
            )

        # ── Tab 3: Audio → Text ──────────────────────────────────────────────
        with gr.Tab("Audio → Text"):
            gr.Markdown("**Free models:** Whisper Large v3 · Whisper Medium — speech transcription")
            with gr.Row():
                with gr.Column(scale=1):
                    a2t_model = gr.Dropdown(
                        choices=list(A2T_MODELS.keys()),
                        value=list(A2T_MODELS.keys())[0],
                        label="Model",
                    )
                    a2t_in  = gr.Audio(label="Upload or Record Audio", type="filepath")
                    a2t_btn = gr.Button("Transcribe", variant="primary")
                with gr.Column(scale=1):
                    a2t_out = gr.Textbox(label="Transcription", lines=12)
            a2t_btn.click(
                run_audio_to_text,
                inputs=[a2t_in, a2t_model, session_token],
                outputs=a2t_out,
            )

if __name__ == "__main__":
    demo.launch(theme=gr.themes.Soft())
