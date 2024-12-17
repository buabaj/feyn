class TextHandler:
    def get_input(self) -> str:
        print("\nType your explanation (press Enter twice to finish):")
        lines = []
        empty_line_count = 0

        while empty_line_count < 2:
            line = input()
            if not line:
                empty_line_count += 1
            else:
                empty_line_count = 0
            lines.append(line)

        # Remove the last two empty lines and join
        return "\n".join(lines[:-2])
