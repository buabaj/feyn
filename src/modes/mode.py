import openai
from enum import Enum
from pathlib import Path


class ModeType(Enum):
    STANDARD = "standard"
    QUIZ = "quiz"
    CHALLENGE = "challenge"


class Mode:
    def __init__(self, topic: str, mode_type: ModeType, client: openai.OpenAI):
        self.topic = topic
        self.mode_type = mode_type if mode_type else ModeType.STANDARD
        self.context: list[dict[str, str]] = []
        self.client = client

    def _get_system_prompt(self) -> str:
        prompts = {
            ModeType.STANDARD: f"""You are an expert tutor using the Feynman Technique to help someone learn {self.topic}. 
Your role is to:
1. Listen carefully to explanations
2. Identify unclear or incomplete parts
3. Ask probing questions that expose gaps in understanding
4. Guide towards simpler, clearer explanations
5. Help make connections with related concepts

Rules:
- Focus on depth of understanding, not breadth
- Ask only ONE question at a time
- Always ask for clarification of technical terms
- Push for concrete examples
- Point out when analogies could be improved
- Challenge circular reasoning

Current topic: {self.topic}""",
            ModeType.QUIZ: f"""You are conducting an active recall session on {self.topic}. 
Your role is to:
1. Ask specific, targeted questions about key concepts
2. Focus on application and understanding, not just facts
3. Follow up on incorrect or incomplete answers
4. Gradually increase question difficulty
5. Mix theoretical and practical questions

Rules:
- Ask ONE question at a time
- Questions should test understanding, not memorization
- Include 'why' and 'how' questions
- Ask for real-world applications
- Challenge common misconceptions
- Follow up on partial or incorrect answers

Current topic: {self.topic}""",
            ModeType.CHALLENGE: f"""You are an advanced instructor pushing deeper understanding of {self.topic}.
Your role is to:
1. Present edge cases and corner cases
2. Explore advanced implications
3. Connect to related advanced topics
4. Challenge assumptions
5. Probe theoretical foundations

Rules:
- Focus on non-obvious aspects
- Question underlying assumptions
- Present ONE challenging scenario at a time
- Push for rigorous thinking
- Explore limitations and edge cases
- Challenge oversimplified explanations

Current topic: {self.topic}""",
        }
        return prompts.get(self.mode_type)

    def process_explanation(self, explanation: str) -> str:
        # Add user's explanation to context
        self.context.append({"role": "user", "content": explanation})

        # Prepare messages for the API
        messages = [
            {"role": "system", "content": self._get_system_prompt()},
            *self.context[-4:],  # Keep last 2 exchanges for context
        ]

        try:
            response = self.client.chat.completions.create(
                model="gpt-4-0125-preview",
                messages=messages,
                temperature=0.3,
                max_tokens=500,
                presence_penalty=0.1,
                frequency_penalty=0.1,
            )

            ai_response = response.choices[0].message.content
            self.context.append({"role": "assistant", "content": ai_response})

            return ai_response

        except Exception as e:
            return f"Error processing response: {str(e)}"


class TextMode(Mode):
    def __init__(self, input_file=None):
        self.input_file = input_file

    def process_text(self, text):
        if not text:
            raise ValueError("Empty text input")
        return {"text": text}

    def run(self):
        if not self.input_file or not Path(self.input_file).exists():
            raise FileNotFoundError(f"Input file not found: {self.input_file}")

        text = Path(self.input_file).read_text()
        result = self.process_text(text)

        return {"status": "success", "text": result["text"]}
