#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path

from config import FeynConfig
from core.engine import FeynEngine


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Feyn: Learn anything using the Feynman Technique")

    parser.add_argument("-t", "--topic", required=True, help="Topic to learn/explain")

    parser.add_argument(
        "-m",
        "--mode",
        choices=["standard", "quiz", "challenge"],
        default="standard",
        help="Learning mode (default: standard)",
    )

    parser.add_argument("--text", action="store_true", help="Use text input instead of speech")

    parser.add_argument("-p", "--path", type=Path, help="Path to save transcripts (default: ./transcripts)")

    parser.add_argument("-r", "--report", action="store_true", help="Generate a session report")

    return parser.parse_args()


def main():
    try:
        args = parse_args()
        config = FeynConfig.load_from_env()

        if args.path:
            config.transcripts_dir = args.path

        mode = args.mode

        # Create and start the engine
        engine = FeynEngine(topic=args.topic, config=config, mode=mode, use_text=args.text, generate_report=args.report)

        engine.run()

    except Exception as e:
        print(f"\nError: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
