import os
import json
from google import genai
from django.conf import settings

class InterviewManager:
    def __init__(self):
        self.api_key = getattr(settings, 'GEMINI_API_KEY', None)
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None

    def get_next_question(self, session, history_messages, jd_text, resume_text):
        """
        Generates the next interview question using gemini-flash-latest.
        Prunes history to the last 10 messages to ensure responsiveness and save quota tokens.
        """
        if not self.client:
            return "Gemini API key not configured. Mock Interview is in mock mode."

        system_prompt = f"""
        You are an Expert Technical Interviewer at a top-tier tech company. Do NOT use placeholder names. 
        Your goal is to conduct a professional, rigorous, but encouraging mock interview.
        You have the candidate's Master Resume and the Job Description they are applying for.
        
        Candidate Resume: {resume_text}
        Job Description: {jd_text}

        Rules:
        1. Ask ONE question at a time.
        2. Acknowledge the user's previous answer briefly and insightfuly.
        3. Keep your own responses concise (max 2-3 paragraphs) to maintain flow.
        4. Focus on technical depth and behavioral STAR alignment.
        5. Do not break persona.
        """

        # Context Pruning: keep only the last 10 messages for current context
        # This keeps the generation faster and more likely to succeed under quota
        pruned_history = list(history_messages)[-10:]

        contents = []
        for msg in pruned_history:
            role = "user" if msg.sender == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg.content}]
            })

        if not contents:
            contents.append({
                "role": "user",
                "parts": [{"text": "I am ready for the interview. Please introduce yourself and ask the first question."}]
            })

        try:
            # gemini-flash-latest is the current most stable alias for high-quota 1.5-flash
            response = self.client.models.generate_content(
                model="gemini-flash-latest",
                config={"system_instruction": system_prompt},
                contents=contents,
            )
            return response.text
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "RESOURCE_EXHAUSTED" in error_msg:
                return "API_QUOTA_REACHED: Google's free tier limit for this model has been reached. Please try again in a few minutes or tomorrow."
            return f"Error connecting to AI Interviewer: {str(e)[:100]}"

    def generate_feedback(self, history_messages, jd_text):
        """
        Analyzes the entire interview transcript and provides a score + feedback.
        """
        if not self.client:
            return json.dumps({"score": 70, "summary": "Mock feedback mode.", "strengths": [], "weaknesses": [], "suggestions": []})

        transcript = ""
        # For feedback, we use the FULL transcript
        for msg in history_messages:
            transcript += f"{msg.sender.upper()}: {msg.content}\n"

        prompt = f"""
        Analyze the following interview transcript for a candidate applying to this Job Description:
        JD: {jd_text}
        Transcript: {transcript}
        
        Return JSON ONLY:
        {{
            "score": (0-100),
            "summary": "2-3 sentences.",
            "strengths": [".."], "weaknesses": [".."], "suggestions": [".."]
        }}
        """

        try:
            response = self.client.models.generate_content(
                model="gemini-flash-latest",
                contents=prompt,
            )
            # Clean possible markdown wrap
            clean_text = response.text.replace('```json', '').replace('```', '').strip()
            return clean_text
        except Exception as e:
            if "429" in str(e):
                return json.dumps({"error": "Daily quota reached for feedback generation."})
            return json.dumps({"error": str(e)})
