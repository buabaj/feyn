import json
from pathlib import Path
from datetime import datetime


class TranscriptManager:
    def __init__(self, transcripts_dir: Path):
        self.transcripts_dir = transcripts_dir
        self.transcript: list[tuple[str, str]] = []  # List of (explanation, response) pairs
        self.session_start = datetime.now()

    def add_exchange(self, explanation: str, response: str):
        self.transcript.append((explanation, response))

    def get_transcript(self) -> list[tuple[str, str]]:
        return self.transcript

    def save(self):
        if not self.transcript:
            return

        timestamp = self.session_start.strftime("%Y%m%d_%H%M%S")
        filename = self.transcripts_dir / f"transcript_{timestamp}.json"

        data = {
            "session_start": self.session_start.isoformat(),
            "session_end": datetime.now().isoformat(),
            "exchanges": [
                {"explanation": explanation, "response": response, "exchange_number": i + 1}
                for i, (explanation, response) in enumerate(self.transcript)
            ],
        }

        self.transcripts_dir.mkdir(parents=True, exist_ok=True)
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        print(f"\nTranscript saved to: {filename}")
