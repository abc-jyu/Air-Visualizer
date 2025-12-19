# 音声分析ロジック
import librosa
import numpy as np
from io import BytesIO
import soundfile as sf
from pydub import AudioSegment
from typing import Dict, Optional
import asyncio
import tempfile
import os

# Supported audio formats
SUPPORTED_FORMATS = {
    'webm': 'webm',
    'opus': 'webm',
    'wav': 'wav',
    'mp3': 'mp3',
    'ogg': 'ogg',
    'm4a': 'm4a'
}


async def analyze_audio(audio_bytes: bytes, format_hint: Optional[str] = None) -> Dict[str, float]:
    """
    Analyze audio features from audio bytes

    Args:
        audio_bytes: Raw audio data as bytes
        format_hint: Optional format hint ('webm', 'wav', 'mp3', etc.)

    Returns:
        Dictionary with audio features:
        {
            "volume": 0.65,  # RMS energy (0.0-1.0)
            "pitch": 220.5   # Fundamental frequency in Hz
        }
    """
    if not audio_bytes:
        return {"volume": 0.0, "pitch": 0.0}

    try:
        # Run audio processing in thread pool
        result = await asyncio.to_thread(_process_audio, audio_bytes, format_hint)
        return result

    except Exception as e:
        print(f"Error during audio analysis: {e}")
        import traceback
        traceback.print_exc()
        return {"volume": 0.0, "pitch": 0.0}


def _process_audio(audio_bytes: bytes, format_hint: Optional[str] = None) -> Dict[str, float]:
    """
    Synchronous audio processing (runs in thread pool)
    """
    y = None
    sr = None
    temp_file = None

    try:
        # Try to load audio directly with soundfile first (works for WAV)
        try:
            audio_io = BytesIO(audio_bytes)
            y, sr = sf.read(audio_io)

        except Exception:
            # If direct loading fails, use pydub for format conversion
            # This handles WebM, MP3, etc.
            temp_file = _convert_to_wav(audio_bytes, format_hint)
            y, sr = librosa.load(temp_file, sr=None)

        # Calculate volume (RMS energy)
        volume = _calculate_volume(y)

        # Calculate pitch (fundamental frequency)
        pitch = _calculate_pitch(y, sr)

        return {
            "volume": float(volume),
            "pitch": float(pitch)
        }

    finally:
        # Clean up temporary file
        if temp_file and os.path.exists(temp_file):
            try:
                os.remove(temp_file)
            except Exception:
                pass


def _convert_to_wav(audio_bytes: bytes, format_hint: Optional[str] = None) -> str:
    """
    Convert audio bytes to WAV format using pydub
    Returns path to temporary WAV file
    """
    # Detect format
    if format_hint:
        format_type = SUPPORTED_FORMATS.get(format_hint.lower(), 'webm')
    else:
        # Try to detect from magic bytes
        format_type = _detect_format(audio_bytes)

    # Load with pydub
    audio_io = BytesIO(audio_bytes)
    audio = AudioSegment.from_file(audio_io, format=format_type)

    # Convert to mono if stereo
    if audio.channels > 1:
        audio = audio.set_channels(1)

    # Export to temporary WAV file
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_wav:
        temp_path = temp_wav.name
        audio.export(temp_path, format='wav')

    return temp_path


def _detect_format(audio_bytes: bytes) -> str:
    """
    Detect audio format from magic bytes
    """
    # WebM/Matroska magic bytes
    if audio_bytes[:4] == b'\x1a\x45\xdf\xa3':
        return 'webm'

    # WAV magic bytes
    if audio_bytes[:4] == b'RIFF':
        return 'wav'

    # MP3 magic bytes
    if audio_bytes[:2] == b'\xff\xfb' or audio_bytes[:3] == b'ID3':
        return 'mp3'

    # OGG magic bytes
    if audio_bytes[:4] == b'OggS':
        return 'ogg'

    # Default to webm for unknown
    return 'webm'


def _calculate_volume(y: np.ndarray) -> float:
    """
    Calculate volume as RMS energy, normalized to 0.0-1.0
    """
    # Calculate RMS (root mean square) energy
    rms = librosa.feature.rms(y=y)[0]

    # Take mean RMS across all frames
    mean_rms = np.mean(rms)

    # Normalize to approximate 0-1 range
    # RMS values are typically 0-0.3 for normalized audio
    # Scale to 0-1 for better interpretation
    normalized_volume = min(mean_rms * 3.0, 1.0)

    return normalized_volume


def _calculate_pitch(y: np.ndarray, sr: int) -> float:
    """
    Calculate pitch (fundamental frequency) using piptrack algorithm
    """
    # Use librosa's piptrack for pitch detection
    pitches, magnitudes = librosa.piptrack(y=y, sr=sr)

    # Select pitch with highest magnitude in each frame
    pitch_values = []
    for t in range(pitches.shape[1]):
        index = magnitudes[:, t].argmax()
        pitch = pitches[index, t]
        if pitch > 0:  # Only include non-zero pitches
            pitch_values.append(pitch)

    # Return median pitch (more robust than mean)
    if pitch_values:
        return float(np.median(pitch_values))
    else:
        return 0.0


async def test_audio_processing() -> bool:
    """
    Test if audio processing libraries are working
    """
    try:
        # Generate simple sine wave for testing
        sr = 22050
        duration = 1.0
        frequency = 440.0  # A4 note

        t = np.linspace(0, duration, int(sr * duration))
        y = 0.5 * np.sin(2 * np.pi * frequency * t)

        # Test volume calculation
        volume = _calculate_volume(y)

        # Test pitch calculation
        pitch = _calculate_pitch(y, sr)

        # Verify results are reasonable
        if 0.0 <= volume <= 1.0 and 400 <= pitch <= 500:
            print("✓ Audio processing test passed")
            return True
        else:
            print(f"⚠ Audio processing test failed: volume={volume}, pitch={pitch}")
            return False

    except Exception as e:
        print(f"✗ Audio processing test error: {e}")
        import traceback
        traceback.print_exc()
        return False
