import subprocess
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import logging

# Configure structured logging with correlation IDs
logger = logging.getLogger(__name__)

def validate_input_path(input_path: Path) -> None:
    """Validate that the input file exists."""
    if not input_path.exists():
        raise FileNotFoundError(f"Input file {input_path} does not exist.")

async def run_ffmpeg_command(command: List[str], timeout: int = 600) -> None:
    """Run an FFmpeg command and handle errors."""
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        logger.info(f"FFmpeg command succeeded: {command}")
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg command failed: {command}\nstderr: {e.stderr}")
        raise RuntimeError(f"FFmpeg command failed with stderr: {e.stderr}")

def extract_clip(
    input_path: Path,
    output_path: Path,
    start_sec: float,
    end_sec: float,
    fade_sec: float = 0.5,
    timeout: int = 600
) -> Path:
    """Extract video clip with optional fade effects."""
    validate_input_path(input_path)
    command = [
        'ffmpeg',
        '-y',
        '-hide_banner',
        '-loglevel', 'error',
        '-i', str(input_path),
        '-ss', str(start_sec),
        '-to', str(end_sec),
        '-af', f'afade=t=in:ss=0:d={fade_sec},afade=t=out:st={end_sec-start_sec-fade_sec}:d={fade_sec}',
        str(output_path)
    ]
    run_ffmpeg_command(command, timeout)
    return output_path

def normalize_audio(
    input_path: Path,
    output_path: Path,
    target_lufs: float = -16,
    timeout: int = 600
) -> Path:
    """Normalize audio to specified LUFS level."""
    validate_input_path(input_path)
    command = [
        'ffmpeg',
        '-y',
        '-hide_banner',
        '-loglevel', 'error',
        '-i', str(input_path),
        '-af', f'loudnorm=I={target_lufs}',
        str(output_path)
    ]
    run_ffmpeg_command(command, timeout)
    return output_path

def get_media_info(path: Path) -> Dict[str, Any]:
    """Get media metadata using ffprobe."""
    validate_input_path(path)
    command = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration;stream=width,height,r_frame_rate,pix_fmt,codec_name,channels',
        '-of', 'json',
        str(path)
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    info = json.loads(result.stdout)

    format_info = info.get('format', {})
    stream_info = next((s for s in info.get('streams', []) if s['codec_type'] == 'video'), {})

    duration = float(format_info.get('duration', 0))
    resolution = (int(stream_info.get('width', 0)), int(stream_info.get('height', 0)))
    codec = stream_info.get('codec_name', '')
    fps = eval(stream_info.get('r_frame_rate', '0/1'))  # Convert fraction to float
    audio_channels = next((s['channels'] for s in info.get('streams', []) if s['codec_type'] == 'audio'), 0)

    return {
        'duration': duration,
        'resolution': resolution,
        'codec': codec,
        'fps': fps,
        'audio_channels': audio_channels
    }

def extract_audio(
    input_path: Path,
    output_path: Path,
    format: str = 'wav',
    timeout: int = 600
) -> Path:
    """Extract audio from video file."""
    validate_input_path(input_path)
    command = [
        'ffmpeg',
        '-y',
        '-hide_banner',
        '-loglevel', 'error',
        '-i', str(input_path),
        '-q:a', '0',
        '-map', 'a',
        f'-f', format,
        str(output_path)
    ]
    run_ffmpeg_command(command, timeout)
    return output_path

def concat_videos(
    input_paths: List[Path],
    output_path: Path,
    transition_sec: float = 0.5,
    timeout: int = 600
) -> Path:
    """Concatenate multiple video files with optional transition effects between clips."""
    if not all(path.exists() for path in input_paths):
        raise FileNotFoundError("One or more input files do not exist.")

    concat_file = output_path.with_name('concat_list.txt')
    with open(concat_file, 'w') as f:
        for path in input_paths:
            f.write(f"file '{path}'\n")

    command = [
        'ffmpeg',
        '-y',
        '-hide_banner',
        '-loglevel', 'error',
        '-f', 'concat',
        '-safe', '0',
        '-i', str(concat_file),
        '-c:v', 'libx264',
        '-crf', '18',
        '-preset', 'fast',
        '-pix_fmt', 'yuv420p',
        '-filter_complex',
        f"[0:v] [0:a] [1:v] [1:a] acrossfade=d={transition_sec}:c1=first:c2=second[v][a]",
        '-map', '[v]',
        '-map', '[a]',
        str(output_path)
    ]
    run_ffmpeg_command(command, timeout)
    concat_file.unlink()
    return output_path

def overlay_text(
    input_path: Path,
    output_path: Path,
    text: str,
    position: Tuple[int, int],
    font_path: Path,
    font_size: int,
    color: str,
    timeout: int = 600
) -> Path:
    """Overlay text on a video file at a specified position, font, size, and color."""
    validate_input_path(input_path)
    command = [
        'ffmpeg',
        '-y',
        '-hide_banner',
        '-loglevel', 'error',
        '-i', str(input_path),
        '-vf',
        f"drawtext=fontfile={font_path}:text='{text}':x={position[0]}:y={position[1]}:fontsize={font_size}:fontcolor={color}",
        str(output_path)
    ]
    run_ffmpeg_command(command, timeout)
    return output_path

def overlay_image(
    input_path: Path,
    output_path: Path,
    image_path: Path,
    position: Tuple[int, int],
    duration_sec: Optional[float] = None,
    timeout: int = 600
) -> Path:
    """Overlay an image on a video file at a specified position and duration."""
    validate_input_path(input_path)
    if not image_path.exists():
        raise FileNotFoundError(f"Image file {image_path} does not exist.")

    overlay_filter = f"overlay={position[0]}:{position[1]}"
    if duration_sec is not None:
        overlay_filter += f":enable='between(t,0,{duration_sec})'"

    command = [
        'ffmpeg',
        '-y',
        '-hide_banner',
        '-loglevel', 'error',
        '-i', str(input_path),
        '-i', str(image_path),
        '-filter_complex', overlay_filter,
        str(output_path)
    ]
    run_ffmpeg_command(command, timeout)
    return output_path

def scene_detect(
    input_path: Path,
    threshold: float = 0.3,
    timeout: int = 600
) -> List[float]:
    """Detect scene changes in a video file based on a specified threshold."""
    validate_input_path(input_path)
    command = [
        'ffmpeg',
        '-y',
        '-hide_banner',
        '-loglevel', 'error',
        '-i', str(input_path),
        '-vf', f'select=gt(scene\\,{threshold})',
        '-f', 'null',
        '-'
    ]
    result = subprocess.run(command, capture_output=True, text=True, check=True)
    timestamps = [float(line.split()[0]) for line in result.stderr.strip().split('\n')]
    return timestamps

def create_silent_audio(
    output_path: Path,
    duration_sec: float,
    sample_rate: int = 48000,
    timeout: int = 600
) -> Path:
    """Generate a silent audio file of a specified duration and sample rate."""
    command = [
        'ffmpeg',
        '-y',
        '-hide_banner',
        '-loglevel', 'error',
        '-f', 'lavfi',
        '-i', f'anullsrc=r={sample_rate}:cl=stereo:d={duration_sec}',
        str(output_path)
    ]
    run_ffmpeg_command(command, timeout)
    return output_path

def mix_audio_tracks(
    tracks: List[Dict[str, Any]],
    output_path: Path,
    timeout: int = 600
) -> Path:
    """Mix multiple audio tracks with specified volumes and start times into a single output file."""
    input_files = []
    filter_complex_parts = []

    for i, track in enumerate(tracks):
        validate_input_path(track['path'])
        input_files.extend(['-i', str(track['path'])])
        filter_complex_parts.append(f"[{i}:a]volume={track.get('volume_db', 0) / 10}dB[a{i}]")
        if 'start_sec' in track:
            filter_complex_parts[-1] = f"[{i}:a]adelay={int(track['start_sec'] * 1000)}|{int(track['start_sec'] * 1000)}[a{i}]"

    filter_complex_parts.append(f"amix=inputs={len(tracks)}:duration=longest[aout]")
    command = [
        'ffmpeg',
        '-y',
        '-hide_banner',
        '-loglevel', 'error',
        *input_files,
        '-filter_complex', '|'.join(filter_complex_parts),
        '-map', '[aout]',
        str(output_path)
    ]
    run_ffmpeg_command(command, timeout)
    return output_path

def render_video(
    inputs: Dict[str, Any],
    output_path: Path,
    resolution: Tuple[int, int],
    fps: float,
    codec: str,
    crf: int,
    audio_codec: str,
    audio_bitrate: str,
    timeout: int = 600
) -> Path:
    """Render video from multiple inputs using FFmpeg's filter graph capabilities."""
    input_files = []
    filter_complex_parts = []

    for i, (key, value) in enumerate(inputs.items()):
        validate_input_path(value['path'])
        input_files.extend(['-i', str(value['path'])])
        if value.get('type') == 'video':
            filter_complex_parts.append(f"[{i}:v]scale={resolution[0]}:{resolution[1]}[v{i}]")
        elif value.get('type') == 'audio':
            filter_complex_parts.append(f"[{i}:a][aout]amix=inputs=2:duration=longest[aout]")

    filter_complex_parts.append(f"concat=n={len([v for v in inputs.values() if v.get('type') == 'video'])}:v=1:a=0[vout]")
    command = [
        'ffmpeg',
        '-y',
        '-hide_banner',
        '-loglevel', 'error',
        *input_files,
        '-filter_complex', '|'.join(filter_complex_parts),
        '-map', '[vout]',
        '-map', '[aout]',
        '-c:v', codec,
        '-crf', str(crf),
        '-r', str(fps),
        '-c:a', audio_codec,
        '-b:a', audio_bitrate,
        str(output_path)
    ]
    run_ffmpeg_command(command, timeout)
    return output_path