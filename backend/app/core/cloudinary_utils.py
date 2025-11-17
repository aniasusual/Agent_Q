"""
Cloudinary integration for uploading and managing screenshots
"""
import os
import base64
import cloudinary
import cloudinary.uploader
from typing import Optional, Dict
from datetime import datetime

# Configure Cloudinary using environment variable
cloudinary.config(
    cloudinary_url=os.getenv("CLOUDINARY_URL")
)


def upload_screenshot_base64(
    base64_data: str,
    folder: str = "agent_q_screenshots",
    public_id: Optional[str] = None
) -> Dict[str, str]:
    """
    Upload a base64-encoded screenshot to Cloudinary

    Args:
        base64_data: Base64 encoded image data (with or without data URI prefix)
        folder: Cloudinary folder to organize screenshots
        public_id: Optional custom public ID for the image

    Returns:
        Dictionary with 'url' and 'public_id' of the uploaded image

    Raises:
        Exception: If upload fails
    """
    try:
        # Remove data URI prefix if present (e.g., "data:image/png;base64,")
        if "base64," in base64_data:
            base64_data = base64_data.split("base64,")[1]

        # Generate public_id if not provided
        if not public_id:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            public_id = f"screenshot_{timestamp}"

        # Upload to Cloudinary
        result = cloudinary.uploader.upload(
            f"data:image/png;base64,{base64_data}",
            folder=folder,
            public_id=public_id,
            resource_type="image",
            overwrite=True,
            transformation=[
                {"quality": "auto:good"},
                {"fetch_format": "auto"}
            ]
        )

        return {
            "url": result["secure_url"],
            "public_id": result["public_id"],
            "width": result.get("width"),
            "height": result.get("height"),
            "format": result.get("format")
        }

    except Exception as e:
        print(f"[Cloudinary] Error uploading screenshot: {e}")
        raise


def upload_screenshot_file(
    file_path: str,
    folder: str = "agent_q_screenshots",
    public_id: Optional[str] = None
) -> Dict[str, str]:
    """
    Upload a screenshot file to Cloudinary

    Args:
        file_path: Path to the image file
        folder: Cloudinary folder to organize screenshots
        public_id: Optional custom public ID for the image

    Returns:
        Dictionary with 'url' and 'public_id' of the uploaded image

    Raises:
        Exception: If upload fails
    """
    try:
        # Generate public_id if not provided
        if not public_id:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            public_id = f"screenshot_{timestamp}"

        # Upload to Cloudinary
        result = cloudinary.uploader.upload(
            file_path,
            folder=folder,
            public_id=public_id,
            resource_type="image",
            overwrite=True,
            transformation=[
                {"quality": "auto:good"},
                {"fetch_format": "auto"}
            ]
        )

        return {
            "url": result["secure_url"],
            "public_id": result["public_id"],
            "width": result.get("width"),
            "height": result.get("height"),
            "format": result.get("format")
        }

    except Exception as e:
        print(f"[Cloudinary] Error uploading screenshot: {e}")
        raise


def delete_screenshot(public_id: str) -> bool:
    """
    Delete a screenshot from Cloudinary

    Args:
        public_id: The public ID of the image to delete

    Returns:
        True if deletion was successful, False otherwise
    """
    try:
        result = cloudinary.uploader.destroy(public_id, resource_type="image")
        return result.get("result") == "ok"
    except Exception as e:
        print(f"[Cloudinary] Error deleting screenshot: {e}")
        return False
