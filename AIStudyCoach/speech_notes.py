import base64
import os
import tempfile
import subprocess
import shutil
from dataclasses import dataclass
from typing import Optional, Dict, Any


try:
    from faster_whisper import WhisperModel
except Exception:  # pragma: no cover
    WhisperModel = None  # type: ignore

try:
    import ffmpeg
    FFMPEG_PYTHON_AVAILABLE = True
except Exception:
    FFMPEG_PYTHON_AVAILABLE = False


@dataclass
class TranscriptionResult:
    text: str
    detected_language: Optional[str]
    duration: Optional[float]


class SpeechNotesManager:
    """Utility that manages Whisper transcription for clinical notes."""

    def __init__(self):
        self.model_size = os.getenv("WHISPER_MODEL_SIZE", "small")
        self.device = os.getenv("WHISPER_DEVICE", "cpu")
        self.compute_type = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
        self.model: Optional[WhisperModel] = None
        self.available = False
        self.last_error: Optional[str] = None
        self._ensure_ffmpeg_in_path()
        self._lazy_load_model()
    
    def _ensure_ffmpeg_in_path(self):
        """Ensure FFmpeg is accessible by adding it to PATH if found in project."""
        ffmpeg_path = self._find_ffmpeg()
        if ffmpeg_path and ffmpeg_path not in os.environ.get("PATH", ""):
            # Add FFmpeg directory to PATH for this process
            ffmpeg_dir = os.path.dirname(ffmpeg_path)
            current_path = os.environ.get("PATH", "")
            os.environ["PATH"] = ffmpeg_dir + os.pathsep + current_path

    def _lazy_load_model(self):
        if WhisperModel is None:
            self.last_error = "faster-whisper not installed"
            self.available = False
            return
        try:
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=self.compute_type,
            )
            self.available = True
            self.last_error = None
        except Exception as exc:  # pragma: no cover - hardware/env dependent
            self.model = None
            self.available = False
            self.last_error = str(exc)

    def is_ready(self) -> bool:
        return self.available and self.model is not None

    def _find_ffmpeg(self) -> Optional[str]:
        """Find FFmpeg executable in system PATH or project directory."""
        # Check system PATH first
        ffmpeg_path = shutil.which("ffmpeg")
        if ffmpeg_path:
            return ffmpeg_path
        
        # Check project directory for FFmpeg (multiple possible locations)
        current_file = os.path.abspath(__file__)
        project_root = os.path.dirname(os.path.dirname(current_file))
        possible_paths = [
            # Check in parent directory (D:\Arogya\ffmpeg-8.0.1-full_build\...)
            os.path.join(project_root, "ffmpeg-8.0.1-full_build", "ffmpeg-8.0.1-full_build", "bin", "ffmpeg.exe"),
            # Check in AIStudyCoach directory
            os.path.join(os.path.dirname(current_file), "ffmpeg-8.0.1-full_build", "ffmpeg-8.0.1-full_build", "bin", "ffmpeg.exe"),
            # Other common locations
            os.path.join(project_root, "ffmpeg", "bin", "ffmpeg.exe"),
            os.path.join(project_root, "ffmpeg.exe"),
            os.path.join(os.path.dirname(current_file), "ffmpeg.exe"),
        ]
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None

    def _convert_audio_to_wav(self, input_path: str, output_path: str) -> bool:
        """Convert audio file to WAV format using FFmpeg."""
        # Try ffmpeg-python first (cleaner API)
        if FFMPEG_PYTHON_AVAILABLE:
            try:
                (
                    ffmpeg
                    .input(input_path)
                    .output(
                        output_path,
                        acodec='pcm_s16le',  # 16-bit PCM
                        ac=1,                # Mono channel
                        ar='16k',            # 16kHz sample rate
                        y=None               # Overwrite output file
                    )
                    .overwrite_output()
                    .run(quiet=True, timeout=30)
                )
                return os.path.exists(output_path) and os.path.getsize(output_path) > 0
            except Exception as e:
                # Fall back to subprocess if ffmpeg-python fails
                pass
        
        # Fallback to subprocess
        ffmpeg_path = self._find_ffmpeg()
        if not ffmpeg_path:
            return False
        
        try:
            cmd = [
                ffmpeg_path,
                "-i", input_path,
                "-ar", "16000",  # Sample rate 16kHz (good for Whisper)
                "-ac", "1",      # Mono channel
                "-y",            # Overwrite output file
                output_path
            ]
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30
            )
            success = result.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0
            if not success and result.stderr:
                # Log FFmpeg errors for debugging
                error_output = result.stderr.decode('utf-8', errors='ignore')
                if error_output:
                    pass  # Could log this if needed
            return success
        except subprocess.TimeoutExpired:
            return False
        except Exception:
            return False

    def transcribe_audio(self, audio_bytes: bytes, language: Optional[str] = None) -> TranscriptionResult:
        if not self.is_ready():
            self._lazy_load_model()
        if not self.is_ready():
            raise RuntimeError(self.last_error or "Whisper model unavailable")

        if not audio_bytes or len(audio_bytes) == 0:
            raise ValueError("Audio bytes are empty")

        # Save input audio (could be WebM, MP3, etc.)
        input_suffix = ".webm"  # Streamlit audio_input typically provides WebM
        with tempfile.NamedTemporaryFile(suffix=input_suffix, delete=False) as tmp_input:
            tmp_input.write(audio_bytes)
            input_path = tmp_input.name

        # Create output WAV file path
        output_path = input_path.replace(input_suffix, ".wav")
        if output_path == input_path:
            output_path = input_path + ".wav"

        try:
            # Try direct transcription first (faster-whisper can handle many formats if FFmpeg is in PATH)
            transcription_path = input_path
            direct_transcription_failed = False
            conversion_error = None
            
            try:
                # Test if Whisper can handle the file directly
                segments, info = self.model.transcribe(
                    transcription_path,
                    language=None if (language is None or language.lower() == "auto") else language,
                    vad_filter=True,
                    beam_size=5,
                )
            except Exception as direct_error:
                direct_transcription_failed = True
                conversion_error = str(direct_error)
                # If direct transcription fails, try converting to WAV
                ffmpeg_path = self._find_ffmpeg()
                if not ffmpeg_path:
                    raise RuntimeError(
                        f"Direct transcription failed and FFmpeg not found. "
                        f"Original error: {conversion_error}. "
                        f"Please install FFmpeg or add it to your PATH."
                    )
                
                converted = self._convert_audio_to_wav(input_path, output_path)
                if not converted:
                    raise RuntimeError(
                        f"Failed to transcribe audio directly and FFmpeg conversion failed. "
                        f"Direct error: {conversion_error}. "
                        f"FFmpeg path: {ffmpeg_path}"
                    )
                transcription_path = output_path
                # Retry transcription with converted file
                try:
                    segments, info = self.model.transcribe(
                        transcription_path,
                        language=None if (language is None or language.lower() == "auto") else language,
                        vad_filter=True,
                        beam_size=5,
                    )
                except Exception as retry_error:
                    raise RuntimeError(
                        f"Audio conversion succeeded but transcription of converted file failed. "
                        f"Direct transcription error: {conversion_error}. "
                        f"Retry transcription error: {retry_error}. "
                        f"Converted file path: {transcription_path}"
                    ) from retry_error
            
            # Extract text from segments
            text_parts = []
            duration = getattr(info, "duration", None)
            detected_lang = getattr(info, "language", None)
            
            for segment in segments:
                seg_text = getattr(segment, "text", "")
                if seg_text:
                    text_parts.append(seg_text.strip())
            
            transcript = " ".join(text_parts).strip()
            
            return TranscriptionResult(
                text=transcript,
                detected_language=detected_lang,
                duration=duration,
            )
        finally:
            # Clean up temp files
            paths_to_clean = [input_path]
            if output_path != input_path and os.path.exists(output_path):
                paths_to_clean.append(output_path)
            
            for path in paths_to_clean:
                try:
                    if os.path.exists(path):
                        os.remove(path)
                except OSError:
                    pass

    @staticmethod
    def encode_audio(audio_bytes: bytes) -> str:
        return base64.b64encode(audio_bytes).decode()

    @staticmethod
    def decode_audio(audio_b64: str) -> bytes:
        return base64.b64decode(audio_b64)

