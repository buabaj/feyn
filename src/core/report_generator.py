from config import FeynConfig


class ReportGenerator:
    def generate(self, transcript: list[tuple[str, str]], topic: str, config: FeynConfig) -> str:
        # Input validation
        if not transcript or not topic:
            return "Error: Transcript and topic must not be empty"

        # Prepare the transcript for analysis
        formatted_transcript = "\n\n".join(
            [f"User: {explanation}\nFeyn: {response}" for explanation, response in transcript]
        )

        prompt = f"""Analyze this Feynman Technique learning session on {topic}. 
        
Transcript:
{formatted_transcript}

Generate a concise report covering:
1. Understanding Level:
   - Key concepts that were well explained
   - Areas where understanding seems solid
   - Concepts that need more clarity

2. Explanation Quality:
   - Use of analogies and examples
   - Clarity and simplicity of explanations
   - Technical accuracy

3. Learning Progress:
   - Initial vs final understanding
   - Key learning moments
   - Breakthrough insights

4. Recommendations:
   - Specific topics to review
   - Concepts to explore further
   - Suggested next steps

Keep the analysis focused and practical."""

        try:
            response = config.client.chat.completions.create(
                model="gpt-4-0125-preview",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert in analyzing learning sessions and providing actionable feedback.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,
                max_tokens=1000,
                presence_penalty=0.1,
                frequency_penalty=0.1,
            )

            return response.choices[0].message.content

        except Exception as e:
            return f"Error generating report: {str(e)}"
