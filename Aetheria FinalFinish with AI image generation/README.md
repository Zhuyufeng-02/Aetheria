# AI Fortune Teller (Flask + ComfyUI)

This is a demo Flask app that provides an interactive AI fortune-telling experience. Users can pick a crystal, draw tarot-like cards, chat with a fortune-teller chatbot, and generate mystical images using a local ComfyUI instance.

## Features
- **Crystal Selection**: Choose a crystal to guide your reading.
- **Tarot Readings**: Single, Three, or Five card readings.
- **AI Chat**: Chat endpoint with optional OpenAI integration (uses `OPENAI_API_KEY`).
- **AI Image Generation**: Generates high-quality, custom fortune-telling images using a local ComfyUI server (Stable Diffusion).
  - Automatically handles prompt queuing and result retrieval.
  - Supports dynamic image dimensions (default 512x1080).

## Prerequisites

### 1. ComfyUI
This project relies on [ComfyUI](https://github.com/comfyanonymous/ComfyUI) for image generation.
1. Install and set up ComfyUI locally.
2. Ensure you have a Stable Diffusion checkpoint loaded (e.g., `v1-5-pruned-emaonly-fp16.safetensors` as referenced in `base_workflow.json`).
3. Start ComfyUI. It usually runs on `http://127.0.0.1:8188`.

### 2. Python Environment
1. Create a virtualenv and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Quick Start

1. **Start ComfyUI**: Make sure your ComfyUI server is running on port 8188.

2. **Run the Flask App**:

```bash
export FLASK_APP=app.py
# The app runs on port 5001 by default in the code, or set PORT env var
python app.py
```

3. **Open the App**: Visit `http://127.0.0.1:5001` in your browser.

## Configuration

- **OpenAI Integration**: Set the environment variable `OPENAI_API_KEY` to enable richer chat responses. If not present, the app uses local fallback responses.
- **ComfyUI Workflow**: The generation workflow is defined in `base_workflow.json`. You can modify this file to change the model, sampler, or other generation parameters.
  - The app dynamically updates the `Empty Latent Image` node (ID 5) with the requested width/height.
  - The app updates the `CLIP Text Encode` node (ID 6) with the user's prompt.

## Project Structure
- `app.py`: Main Flask application and logic.
- `comfyui_run.py`: Helper script to interact with the ComfyUI API (queue prompt, wait for result).
- `base_workflow.json`: The ComfyUI workflow configuration exported in API format.
- `static/generated/`: Stores the generated images.
- `generated.db`: SQLite database tracking generated image metadata.

## Troubleshooting
- **Image Generation Failed (500 Error)**:
  - Check if ComfyUI is running at `127.0.0.1:8188`.
  - Check the ComfyUI console for errors (e.g., missing models).
  - Ensure `base_workflow.json` matches your ComfyUI nodes (specifically Node IDs 5 for Latent and 6 for Prompt).
