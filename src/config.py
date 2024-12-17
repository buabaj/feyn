from pathlib import Path
from dataclasses import dataclass
import os
from dotenv import load_dotenv
from openai import OpenAI


@dataclass
class FeynConfig:
    client: OpenAI
    transcripts_dir: Path
    silence_threshold: float = 0.03
    pause_duration: float = 2.0
    sample_rate: int = 16000
    chunk_size: int = 1024

    @classmethod
    def load_from_env(cls) -> "FeynConfig":
        load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        transcripts_dir = Path(os.getenv("FEYN_TRANSCRIPTS_DIR", "./transcripts"))
        transcripts_dir.mkdir(parents=True, exist_ok=True)

        return cls(client=OpenAI(api_key=api_key), transcripts_dir=transcripts_dir)
