from config import FeynConfig
from core.speech_processor import SpeechProcessor
from core.text_handler import TextHandler
from core.transcript_manager import TranscriptManager
from core.report_generator import ReportGenerator
from modes.mode import Mode, ModeType


class FeynEngine:
    def __init__(
        self, topic: str, config: FeynConfig, mode: str, use_text: bool = False, generate_report: bool = False
    ):
        self.topic = topic
        self.config = config
        self.mode = Mode(topic=topic, mode_type=ModeType[str(mode).upper()], client=config.client)
        self.use_text = use_text
        self.generate_report = generate_report

        self.transcript_manager = TranscriptManager(config.transcripts_dir)
        self.speech_processor = SpeechProcessor(config) if not use_text else None
        self.text_handler = TextHandler() if use_text else None
        self.report_generator = ReportGenerator() if generate_report else None

    def run(self):
        print(f"\nStarting Feyn session on topic: {self.mode.topic} in {self.mode.mode_type.name} mode")

        try:
            self._run_session_loop()
        finally:
            self._handle_session_end()

    def _run_session_loop(self):
        print("\nExplain the topic. Press Enter to stop each recording.")
        print("Type 'quit' or press Ctrl+C to end the session.\n")

        while True:
            try:
                if self.use_text:
                    explanation = self.text_handler.get_input()
                    if explanation.lower().strip() == "quit":
                        break
                else:
                    with self.speech_processor as sp:
                        explanation = sp.record_and_transcribe()
                        if not explanation or not explanation.strip():
                            print("No speech detected. Please try again.")
                            continue
                        if explanation.lower() == "quit" or explanation.lower() == "end session":
                            break

                    response = self.mode.process_explanation(explanation)
                    if not response:
                        print("Failed to get AI response. Please try again.")
                        continue

                self.transcript_manager.add_exchange(explanation, response)

                print(f"\nYour explanation: {explanation}")
                print(f"\nFeyn: {response}\n")

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"\nError during recording/processing: {e}")
                continue

    def _handle_session_end(self):
        print("\nEnding session...")

        self.transcript_manager.save()

        if self.generate_report and self.report_generator:
            print("\nGenerating session report...")
            report = self.report_generator.generate(
                self.transcript_manager.get_transcript(), self.mode.topic, self.config
            )
            print("\nSession Report:")
            print(report)
