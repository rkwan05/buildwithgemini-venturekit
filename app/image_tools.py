"""Image generation, artifact saving, and Cloud Storage upload tools for VentureKit."""
import uuid
from typing import Any
from google import genai
from google.cloud import storage
from google.genai import types
from google.adk.tools import ToolContext

# Hardcoded GCP Project ID and Bucket Name as strings.
PROJECT_ID = "qwiklabs-gcp-04-c8fa96deb89c"
BUCKET_NAME = "venturekit-assets-qwiklabs-gcp-04-c8fa96deb89c"
IMAGE_MODEL = "gemini-3.1-flash-lite-image"


async def generate_growth_play_image(
    play_title: str,
    visual_description: str,
    tool_context: ToolContext,
) -> dict[str, Any]:
    """Generates a marketing or strategic visual for a growth play using gemini-3.1-flash-lite-image.

    Performs two actions with the generated image bytes:
    1. Saves the image with tool_context.save_artifact so it displays in the Playground Artifacts panel.
    2. Uploads the image bytes directly to the public Cloud Storage bucket and returns the public https URL.

    Args:
        play_title: Title or name of the growth play (e.g. 'One-Time to Monthly Retainer Conversion').
        visual_description: Visual prompt describing the graphic to create (e.g. 'Modern minimalist strategic infographic card illustrating a 3-tier client retainer package with navy and gold accents').
        tool_context: ADK ToolContext injected by the framework to save artifacts.

    Returns:
        A dictionary containing the title, public Cloud Storage https URL, artifact filename, and status.
    """
    try:
        # Generate image using Vertex AI global endpoint
        client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
        response = client.models.generate_content(
            model=IMAGE_MODEL,
            contents=visual_description,
            config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
        )

        part = response.candidates[0].content.parts[0]
        image_bytes = part.inline_data.data
        mime_type = part.inline_data.mime_type or "image/jpeg"
        file_ext = "png" if "png" in mime_type else "jpg"

        clean_slug = "".join(c if c.isalnum() else "_" for c in play_title.lower())[:24]
        unique_suffix = uuid.uuid4().hex[:6]
        filename = f"{clean_slug}_{unique_suffix}.{file_ext}"

        # 1. Save with tool_context.save_artifact for the Playground's Artifacts panel
        artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        artifact_version = await tool_context.save_artifact(
            filename=filename,
            artifact=artifact_part,
            custom_metadata={"play_title": play_title, "model": IMAGE_MODEL},
        )

        # 2. Upload same bytes to public Cloud Storage bucket
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        gcs_blob_name = f"growth_plays/{filename}"
        blob = bucket.blob(gcs_blob_name)
        blob.upload_from_string(image_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{gcs_blob_name}"

        return {
            "status": "success",
            "play_title": play_title,
            "artifact_filename": filename,
            "artifact_version": artifact_version,
            "image_url": public_url,
            "message": f"Successfully generated and published image for '{play_title}'.",
        }
    except Exception as e:
        return {
            "status": "error",
            "play_title": play_title,
            "error": str(e),
        }
