import pyaudio
import wave
import tempfile
import threading
import queue
import numpy as np
from pathlib import Path
from typing import Optional

from config import FeynConfig


class SpeechProcessor:
    def __init__(self, config: FeynConfig):
        self.config = config
        self.audio = None
        self.recording_thread: Optional[threading.Thread] = None
        self.audio_queue = queue.Queue()
        self.is_recording = False
        self._audio_levels = queue.Queue()
        self.client = config.client
        self.frames = []
        self.input_device_index = None

        self._initialize_audio()

    def _initialize_audio(self):
        self.audio = pyaudio.PyAudio()
        # Find the first available input device
        for i in range(self.audio.get_device_count()):
            device_info = self.audio.get_device_info_by_index(i)
            if device_info["maxInputChannels"] > 0:
                self.input_device_index = i
                break

        if self.input_device_index is None:
            self.audio.terminate()
            raise RuntimeError("No input device found. Please check your microphone connection.")

    def record_and_transcribe(self) -> str:
        if self.is_recording:
            raise RuntimeError("Recording already in progress")

        # Ensure audio is initialized
        if self.audio is None:
            self._initialize_audio()

        print("🎤 Start speaking... Press Enter to stop recording")

        try:
            # Start recording and level monitoring threads
            self.is_recording = True
            self.recording_thread = threading.Thread(target=self._record_audio)
            self.level_monitor_thread = threading.Thread(target=self._monitor_audio_levels)
            self.recording_thread.start()
            self.level_monitor_thread.start()

            # Wait for Enter key
            input()
        finally:
            self.is_recording = False
            if self.recording_thread:
                self.recording_thread.join()
            if self.level_monitor_thread:
                self.level_monitor_thread.join()

        if self.audio_queue.empty():
            return ""

        # Save the recorded audio to a temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
            self._save_audio(temp_audio.name)

            # Transcribe using Whisper
            try:
                with open(temp_audio.name, "rb") as audio_file:
                    transcript = self.client.audio.transcriptions.create(
                        model="whisper-1", file=audio_file, language="en", response_format="text", temperature=0.2
                    )
                return transcript
            except Exception as e:
                print(f"Transcription error: {e}")
                return ""
            finally:
                Path(temp_audio.name).unlink()  # Clean up temp file

    def _record_audio(self):
        if self.audio is None:
            self._initialize_audio()

        try:
            stream = self.audio.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                input_device_index=self.input_device_index,
                frames_per_buffer=self.config.chunk_size,
            )

            while self.is_recording:
                audio_data = stream.read(self.config.chunk_size)
                self.audio_queue.put(audio_data)
        except OSError as e:
            print(f"Audio Error: {str(e)}")
            self.is_recording = False
        finally:
            if "stream" in locals():
                stream.stop_stream()
                stream.close()

    def _monitor_audio_levels(self):
        while self.is_recording:
            if not self.audio_queue.empty():
                data = self.audio_queue.queue[-1]
                audio_array = np.frombuffer(data, dtype=np.int16)
                level = np.abs(audio_array).mean() / 32768.0  # 32768 is max value for 16-bit audio
                self._audio_levels.put(level)

                bars = int(level * 50)
                print(f"\rAudio Level: {'|' * bars}{' ' * (50 - bars)}", end="")
            threading.Event().wait(0.1)  # Small delay to prevent CPU overuse

    def _save_audio(self, filename: str):
        with wave.open(filename, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(self.audio.get_sample_size(pyaudio.paInt16))
            wf.setframerate(self.config.sample_rate)

            while not self.audio_queue.empty():
                data = self.audio_queue.get()
                wf.writeframes(data)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def __del__(self):
        self.cleanup()

    def cleanup(self):
        self.is_recording = False
        if hasattr(self, "recording_thread") and self.recording_thread:
            self.recording_thread.join(timeout=1)
        if hasattr(self, "level_monitor_thread") and self.level_monitor_thread:
            self.level_monitor_thread.join(timeout=1)
        if hasattr(self, "audio") and self.audio:
            try:
                self.audio.terminate()
            except:
                pass
        self.audio = None
