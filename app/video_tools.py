"""Video generation, artifact saving, and Cloud Storage upload tools for VentureKit."""
import base64
import uuid
from typing import Any
from google import genai
from google.cloud import storage
from google.genai import types
from google.adk.tools import ToolContext

# Hardcoded GCP Project ID and Bucket Name as strings
PROJECT_ID = "qwiklabs-gcp-04-c8fa96deb89c"
BUCKET_NAME = "venturekit-assets-qwiklabs-gcp-04-c8fa96deb89c"
VIDEO_MODEL = "gemini-omni-flash-preview"


async def generate_growth_play_video(
    play_title: str,
    visual_description: str,
    tool_context: ToolContext,
) -> dict[str, Any]:
    """Generates a short animated video for a growth play or strategy using Google's Omni model (gemini-omni-flash-preview).

    Performs two actions with the generated video:
    1. Saves the video with tool_context.save_artifact so it displays in the Playground's Artifacts panel.
    2. Uploads the same video bytes directly to the public Cloud Storage bucket and returns the public https URL.

    Args:
        play_title: Title or name of the growth play or financial strategy (e.g. 'Retainer Conversion Explainer' or 'Margin Expansion Overview').
        visual_description: Visual prompt describing the video scene to animate (e.g. '3-second clean 3D motion graphic showing recurring monthly revenue climbing exponentially with emerald green bars and white financial metrics').
        tool_context: ADK ToolContext injected by the framework to save artifacts.

    Returns:
        A dictionary containing the title, public Cloud Storage https URL, artifact filename, and status.
    """
    try:
        # Generate video using Google Omni model via Interactions API in the global region
        client = genai.Client(vertexai=True, project=PROJECT_ID, location="global")
        interaction = client.interactions.create(
            model=VIDEO_MODEL,
            input=f"{play_title}: {visual_description}",
            response_format={"type": "video"},
        )

        output_video = getattr(interaction, "output_video", None)
        if not output_video or not getattr(output_video, "data", None):
            return {
                "status": "error",
                "message": "Model did not return video output data.",
            }

        video_data = output_video.data
        if isinstance(video_data, str):
            video_bytes = base64.b64decode(video_data)
        else:
            video_bytes = bytes(video_data)

        mime_type = getattr(output_video, "mime_type", None) or "video/mp4"
        file_ext = "mp4"

        clean_slug = "".join(c if c.isalnum() else "_" for c in play_title.lower())[:24]
        unique_suffix = uuid.uuid4().hex[:6]
        filename = f"{clean_slug}_{unique_suffix}.{file_ext}"

        # 1. Save with tool_context.save_artifact for the Playground's Artifacts panel
        artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
        artifact_version = await tool_context.save_artifact(
            filename=filename,
            artifact=artifact_part,
            custom_metadata={"play_title": play_title, "model": VIDEO_MODEL},
        )

        # 2. Upload same bytes directly to public Cloud Storage bucket (do not write local file)
        storage_client = storage.Client(project=PROJECT_ID)
        bucket = storage_client.bucket(BUCKET_NAME)
        gcs_blob_name = f"growth_play_videos/{filename}"
        blob = bucket.blob(gcs_blob_name)
        blob.upload_from_string(video_bytes, content_type=mime_type)

        public_url = f"https://storage.googleapis.com/{BUCKET_NAME}/{gcs_blob_name}"

        return {
            "status": "success",
            "play_title": play_title,
            "artifact_filename": filename,
            "artifact_version": artifact_version,
            "video_url": public_url,
            "message": f"Successfully generated and published video for '{play_title}'.",
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to generate video for '{play_title}': {type(e).__name__}: {str(e)}",
        }
