from pathlib import Path
import subprocess
import uuid
import shutil


BASE_DIR = Path(__file__).resolve().parent
AUDIO_DIR = BASE_DIR / "generated_audio"
AUDIO_DIR.mkdir(exist_ok=True)


def speak_text_to_audio_file(
    text: str,
    voice: str = "Samantha",
    rate: int = 180,
) -> dict:
    """
    Convert text to audio using macOS say command.
    Output is converted to .m4a for browser playback.
    """

    if not text or not text.strip():
        return {"error": "Text is empty."}

    if len(text) > 8000:
        text = text[:8000]

    file_id = uuid.uuid4().hex
    temp_aiff = AUDIO_DIR / f"{file_id}.aiff"
    final_m4a = AUDIO_DIR / f"{file_id}.m4a"

    try:
        # 1. macOS say creates AIFF audio
        subprocess.run(
            [
                "say",
                "-v",
                voice,
                "-r",
                str(rate),
                "-o",
                str(temp_aiff),
                text,
            ],
            check=True,
        )

        # 2. Convert AIFF to M4A if afconvert exists
        if shutil.which("afconvert"):
            subprocess.run(
                [
                    "afconvert",
                    str(temp_aiff),
                    str(final_m4a),
                    "-f",
                    "m4af",
                    "-d",
                    "aac",
                ],
                check=True,
            )

            temp_aiff.unlink(missing_ok=True)

            return {
                "message": "Audio created successfully.",
                "file_name": final_m4a.name,
                "file_path": str(final_m4a),
                "mime_type": "audio/mp4",
            }

        # fallback: return AIFF
        return {
            "message": "Audio created successfully as AIFF.",
            "file_name": temp_aiff.name,
            "file_path": str(temp_aiff),
            "mime_type": "audio/aiff",
        }

    except subprocess.CalledProcessError as e:
        return {"error": f"Audio generation failed: {e}"}

    except FileNotFoundError:
        return {
            "error": "macOS 'say' command not found. This version works on Mac."
        }