import json
import subprocess


class FilmValidationError(Exception):
    """Raised when FFprobe validation fails with a coach-facing message."""
    pass


def get_duration(local_path: str) -> float:
    """Get video duration in seconds without validation checks.

    Used for chunk files where duration may be under 60s (last segment).
    Returns 0.0 if duration cannot be determined.
    """
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                local_path,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            return 0.0
        data = json.loads(result.stdout)
        return float(data.get("format", {}).get("duration", 0))
    except Exception:
        return 0.0


def validate_film_file(local_path: str) -> dict:
    """Run FFprobe on a local file and validate it for processing.

    Checks:
    - Valid container (FFprobe can parse it)
    - Has at least one video stream
    - Duration >= 60 seconds
    - Duration <= 10800 seconds (3 hours)

    Returns: {"duration": float, "streams": list[dict]}
    Raises: FilmValidationError with a specific message on any failure.
    """
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                local_path,
            ],
            capture_output=True,
            text=True,
            timeout=60,
        )
    except subprocess.TimeoutExpired:
        raise FilmValidationError("Film validation timed out. The file may be corrupted.")
    except FileNotFoundError:
        raise FilmValidationError("FFprobe is not installed on this worker.")

    if result.returncode != 0:
        raise FilmValidationError(
            "This file is not a valid video. Please upload an MP4, MOV, AVI, MKV, or WebM file."
        )

    try:
        probe_data = json.loads(result.stdout)
    except json.JSONDecodeError:
        raise FilmValidationError(
            "Could not read video metadata. The file may be corrupted."
        )

    # Check for video stream
    streams = probe_data.get("streams", [])
    video_streams = [s for s in streams if s.get("codec_type") == "video"]
    if not video_streams:
        raise FilmValidationError(
            "This file has no video track. Please upload a file with video content."
        )

    # Get duration — try format-level first, then fall back to video stream duration
    format_info = probe_data.get("format", {})
    duration_str = format_info.get("duration")
    if not duration_str:
        duration_str = video_streams[0].get("duration")
    if not duration_str:
        # Some containers (MKV) don't report duration in format — try nb_frames / r_frame_rate
        raise FilmValidationError(
            "Could not determine video duration. The file may be corrupted or in an unsupported format."
        )

    try:
        duration = float(duration_str)
    except (ValueError, TypeError):
        raise FilmValidationError(
            "Could not determine video duration. The file may be corrupted."
        )

    if duration < 60:
        raise FilmValidationError(
            f"This film is only {int(duration)} seconds long. "
            "TEX requires at least 1 minute of game footage to generate a useful report."
        )

    if duration > 10800:
        minutes = int(duration / 60)
        raise FilmValidationError(
            f"This film is {minutes} minutes long. "
            "TEX supports films up to 3 hours (180 minutes). "
            "Please trim the file or upload it in parts."
        )

    return {
        "duration": duration,
        "streams": streams,
    }
