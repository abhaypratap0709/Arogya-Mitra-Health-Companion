import os
from dataclasses import dataclass
from typing import Optional, Dict, Any

try:
    import google.generativeai as genai
except Exception:
    genai = None  # type: ignore


SUMMARY_PROMPT = """You are a clinical documentation assistant.
Given the following doctor-patient conversation transcript, produce a structured medical visit note.

Return concise bullet content for each section. Use 'N/A' if the section has no information.

Transcript:
\"\"\"{transcript}\"\"\"

Respond in JSON with keys:
chief_complaint, symptoms, medications, findings, plan, follow_up, additional_notes.
"""


@dataclass
class StructuredNote:
    chief_complaint: str
    symptoms: str
    medications: str
    findings: str
    plan: str
    follow_up: str
    additional_notes: str
    raw_response: str
    model: str


class ClinicalNoteSummarizer:
    def __init__(self):
        self.provider = None
        self.last_error: Optional[str] = None
        self.model_name = None

        gemini_key = os.getenv("GEMINI_API_KEY")
        self.provider = "gemini"
        if gemini_key and genai is not None:
            self.model_name = os.getenv("GEMINI_SUMMARY_MODEL", "gemini-1.5-pro-latest")
            genai.configure(api_key=gemini_key)
            self.client = genai.GenerativeModel(self.model_name)
        else:
            self.client = None
            self.model_name = None
            self.last_error = "GEMINI_API_KEY missing or google-generativeai not installed."

    def summarize(self, transcript: str) -> StructuredNote:
        if not self.provider or not getattr(self, "client", None):
            raise RuntimeError(self.last_error or "LLM summarizer unavailable.")

        prompt = SUMMARY_PROMPT.format(transcript=transcript.strip())
        response_text = self._summarize_gemini(prompt)
        data = self._parse_json(response_text)
        return StructuredNote(
            chief_complaint=data["chief_complaint"],
            symptoms=data["symptoms"],
            medications=data["medications"],
            findings=data["findings"],
            plan=data["plan"],
            follow_up=data["follow_up"],
            additional_notes=data["additional_notes"],
            raw_response=response_text,
            model=f"{self.provider}:{self.model_name}",
        )

    def _summarize_gemini(self, prompt: str) -> str:
        try:
            response = self.client.generate_content(prompt)
            if hasattr(response, "text"):
                return response.text
            if response.candidates:
                return response.candidates[0].content.parts[0].text
            return ""
        except Exception as exc:
            self.last_error = str(exc)
            raise

    @staticmethod
    def _parse_json(text: str) -> Dict[str, str]:
        import json

        keys = [
            "chief_complaint",
            "symptoms",
            "medications",
            "findings",
            "plan",
            "follow_up",
            "additional_notes",
        ]

        try:
            data = json.loads(text)
        except Exception:
            data = {}

        normalized = {}
        for key in keys:
            value = data.get(key, text if not data else "")
            if isinstance(value, list):
                value = "\n".join(str(item) for item in value)
            normalized[key] = str(value) if value is not None else ""

        return normalized

