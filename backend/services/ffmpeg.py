import glob
import subprocess


class FFmpegError(Exception):
    """Raised when an FFmpeg operation fails."""
    pass


def compress_film(input_path: str, output_path: str) -> None:
    """Compress a film to H.264 720p for Gemini upload.

    Only called when file_size_bytes > 1.8GB.
    H.264, CRF 28, scale to 720p height (preserving aspect ratio), AAC 128k audio.
    Timeout: 3600 seconds (1 hour).

    Raises FFmpegError on failure.
    """
    try:
        result = subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i", input_path,
                "-c:v", "libx264",
                "-crf", "28",
                "-vf", "scale=-2:720",
                "-c:a", "aac",
                "-b:a", "128k",
                "-movflags", "+faststart",
                output_path,
            ],
            capture_output=True,
            text=True,
            timeout=3600,
        )
    except subprocess.TimeoutExpired:
        raise FFmpegError("Film compression timed out after 60 minutes.")
    except FileNotFoundError:
        raise FFmpegError("FFmpeg is not installed on this worker.")

    if result.returncode != 0:
        raise FFmpegError(f"Film compression failed: {result.stderr[:500]}")


def split_film(input_path: str, output_pattern: str) -> list[str]:
    """Split a film into 20-25 minute segments.

    segment_time=1500 (25 minutes). Copy codec (no re-encoding). Reset timestamps.
    Output pattern must contain %03d, e.g. /tmp/{film_id}_chunk_%03d.mp4

    Returns sorted list of output chunk file paths.
    Raises FFmpegError on failure.
    """
    try:
        result = subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i", input_path,
                "-c", "copy",
                "-map", "0",
                "-segment_time", "1500",
                "-f", "segment",
                "-reset_timestamps", "1",
                output_pattern,
            ],
            capture_output=True,
            text=True,
            timeout=1800,
        )
    except subprocess.TimeoutExpired:
        raise FFmpegError("Film splitting timed out after 30 minutes.")
    except FileNotFoundError:
        raise FFmpegError("FFmpeg is not installed on this worker.")

    if result.returncode != 0:
        raise FFmpegError(f"Film splitting failed: {result.stderr[:500]}")

    # Find all output chunks matching the pattern
    # Convert pattern like /tmp/abc_chunk_%03d.mp4 to glob /tmp/abc_chunk_*.mp4
    glob_pattern = output_pattern.replace("%03d", "*")
    chunk_paths = sorted(glob.glob(glob_pattern))

    if not chunk_paths:
        raise FFmpegError("Film splitting produced no output chunks.")

    return chunk_paths
