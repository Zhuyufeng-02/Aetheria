import requests
import json
import time
import logging

# ComfyUI server address
server_address = "127.0.0.1:8188"
base_url = f"http://{server_address}"

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Load the API-formatted workflow
with open("base_workflow.json", "r") as f:
    workflow_prompt = json.load(f)


def queue_workflow_and_wait(prompt: str, width: int = 512, height: int = 512, max_attempts: int = 30, sleep_s: float = 1.0) -> str:
    """Post a workflow to ComfyUI and wait until an output image is available.

    Returns the generated image URL on success. Raises Exception on failure or timeout.
    """
    print(workflow_prompt)
    workflow_prompt["6"]["inputs"]["text"] = prompt
    
    # Update latent image dimensions (Node 5 is EmptyLatentImage)
    if "5" in workflow_prompt and "inputs" in workflow_prompt["5"]:
        workflow_prompt["5"]["inputs"]["width"] = width
        workflow_prompt["5"]["inputs"]["height"] = height
        
    resp = requests.post(f"{base_url}/prompt", json={"prompt": workflow_prompt})
    if resp.status_code != 200:
        raise Exception(f"Error sending prompt: {resp.status_code} - {resp.text}")

    data = resp.json()
    prompt_id = data.get("prompt_id")
    if not prompt_id:
        raise Exception(f"No prompt_id returned from server: {data}")

    logger.info(f"Queued workflow with prompt_id: {prompt_id}")
    print(max_attempts)

    for attempt in range(max_attempts):
        history = requests.get(f"{base_url}/history/{prompt_id}")
        # Some servers may return non-200 during processing; raise or continue accordingly
        if history.status_code != 200:
            logger.debug(f"History check returned status {history.status_code}: {history.text}")
            time.sleep(sleep_s)
            continue

        history_json = history.json()
        if history_json.get(prompt_id):
            outputs = history_json[prompt_id].get("outputs", {})
            logger.info("Workflow outputs: %s", json.dumps(outputs, indent=2))
            image_node = next((nid for nid, out in outputs.items() if "images" in out), None)
            if not image_node:
                raise Exception(f"No output node with images found: {outputs}")
            image_filename = outputs[image_node]["images"][0]["filename"]
            image_url = f"{base_url}/view?filename={image_filename}&subfolder=&type=output"
            logger.info(f"Generated image URL: {image_url}")
            return image_url

        time.sleep(sleep_s)

    raise Exception(f"Workflow {prompt_id} didn't complete within {max_attempts * sleep_s} seconds")


if __name__ == "__main__":
    try:
        image_url = queue_workflow_and_wait(workflow_prompt)
        print(f"Generated image URL: {image_url}")
    except Exception as e:
        logger.error("Failed: %s", e)
        raise