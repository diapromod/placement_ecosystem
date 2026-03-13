import os
import json
from google import genai
from django.conf import settings

class InterviewManager:
    def __init__(self):
        self.api_key = getattr(settings, 'GEMINI_API_KEY', None)
        self.client = genai.Client(api_key=self.api_key) if self.api_key else None
        self.demo_mode = getattr(settings, 'GEMINI_DEMO_MODE', False)
        # Fallback chain for Demo Resiliency
        self.models_to_try = [
            'gemini-2.5-flash',
            'gemini-2.0-flash', 
            'gemini-1.5-flash', 
            'gemini-1.5-flash-8b', 
            'gemini-1.5-pro',
            'gemini-flash-latest'
        ]

    def _generate_with_fallback(self, prompt, system_prompt=None, contents=None):
        """Helper to try multiple models in sequence."""
        if not self.client:
            return None, "No API client"

        last_error = "Unknown error"
        for model_name in self.models_to_try:
            try:
                config = {}
                if system_prompt:
                    config["system_instruction"] = system_prompt

                if contents:
                    response = self.client.models.generate_content(
                        model=model_name,
                        config=config,
                        contents=contents,
                    )
                else:
                    response = self.client.models.generate_content(
                        model=model_name,
                        config=config,
                        contents=prompt,
                    )
                return response.text, None
            except Exception as e:
                last_error = str(e)
                print(f"DEBUG: Model {model_name} failed. Error: {last_error}")
                if "429" in last_error or "quota" in last_error.lower() or "500" in last_error:
                    continue
                else:
                    break
        return None, last_error

    def get_next_question(self, session, history_messages, jd_text, resume_text, candidate_name="Candidate", company_name="the company", current_turn=1, total_turns=10):
        """
        Generates the next interview question using a fallback model chain.
        Now includes turn-awareness and strict personalization grounding.
        """
        if not self.client:
            return "Gemini API key not configured. Mock Interview is in mock mode."

        system_prompt = f"""
        You are an Expert Technical Interviewer from {company_name}. 
        Conduct a professional, rigorous mock interview for the candidate: {candidate_name}.
        
        Candidate Resume: {resume_text}
        Job Description: {jd_text}
        
        INTERVIEW PROGRESS: Turn {current_turn} of {total_turns}
        
        CURRICULUM:
        - Turn 1: Professional greeting (address the candidate as {candidate_name}) and a soft introductory question.
        - Turns 2-3: Resume-specific questions (experience, projects).
        - Turns 4-7: Technical deep dive based on JD and Resume skills.
        - Turns 8-9: Behavioral and situational/scenario questions.
        - Turn 10: Final wrap-up. Acknowledge it's the end, thank the candidate, and do NOT ask any more questions.
        
        STRICT CONSTRAINTS:
        - NEVER use generic placeholders like "[Your Name]", "[Company Name]", or "[Interviewer Name]". 
        - If you need to identify yourself, use a fictional professional name or just "Interviewer from {company_name}".
        - Ask ONE specific question at a time.
        - Be concise and professional.
        - If Turn is {total_turns}, provide a closing statement ONLY.
        """

        pruned_history = list(history_messages)[-10:]
        contents = []
        for msg in pruned_history:
            role = "user" if msg.sender == "user" else "model"
            contents.append({
                "role": role,
                "parts": [{"text": msg.content}]
            })

        if not contents:
            # First turn logic: AI initiates
            text, error = self._generate_with_fallback(None, system_prompt=system_prompt, contents=[{
                "role": "user",
                "parts": [{"text": "I am ready for the interview. Please introduce yourself and ask the first question."}]
            }])
        else:
            text, error = self._generate_with_fallback(None, system_prompt=system_prompt, contents=contents)
        
        if text:
            return text
        
        # Turn 10 should ALWAYS be a wrap-up, even in mock/fail modes
        if current_turn >= total_turns:
            return "Thank you for sharing that. We have reached the end of our structured interview session. I have enough information to provide your feedback now. Best of luck!"

        if self.demo_mode:
            # Smart Mock Pool to avoid repetition during demo failures
            # Using current_turn for better predictability
            mock_questions = [
                "I see. Can you walk me through a complex technical challenge you faced in one of your projects and how you resolved it?",
                "Interesting approach. Given the stack mentioned in your resume, how would you handle a sudden surge in traffic for a cloud-based application?",
                "That's a solid explanation. Can you discuss your experience with testing and how you ensure code reliability?",
                "Let's pivot to behavioral. Tell me about a time you had a conflict with a teammate and how you handled it.",
                "Excellent. Given the job requirements, what's your approach to learning new technologies quickly?",
                "Understood. How do you handle tight deadlines and shifting priorities in a fast-paced environment?",
                "Can you describe a situation where you had to work with a difficult stakeholder or client?",
                "What's your preferred method for documenting your code and architectural decisions?",
                "Finally, where do you see your technical skills evolving in the next two years?"
            ]
            q_idx = min(current_turn - 1, len(mock_questions) - 1)
            return mock_questions[q_idx]
        
        if "429" in str(error) or "RESOURCE_EXHAUSTED" in str(error):
            return "API_QUOTA_REACHED: Google's free tier limit hit. Please try again later."
        return f"Error connecting to AI: {str(error)[:100]}"

    def generate_feedback(self, history_messages, jd_text):
        """
        Analyzes the entire interview transcript and provides a score + feedback with fallback support.
        """
        if not self.client:
            return json.dumps({"score": 70, "summary": "Mock feedback mode.", "strengths": [], "weaknesses": [], "suggestions": []})

        transcript = ""
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

        text, error = self._generate_with_fallback(prompt)
        
        if text:
            return text.replace('```json', '').replace('```', '').strip()

        if self.demo_mode:
            return json.dumps({
                "score": 85,
                "summary": "Strong technical knowledge demonstrated throughout the interview. Good communication skills.",
                "strengths": ["Excellent grasp of backend architecture", "Clear communication"],
                "weaknesses": ["Cloud experience could be deeper"],
                "suggestions": ["Review AWS/Azure scaling strategies"]
            })

        if "429" in str(error):
            return json.dumps({"error": "Daily quota reached for feedback generation."})
        return json.dumps({"error": str(error)})
