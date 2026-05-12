import google.generativeai as genai
from src.config import Config

class GeminiClient:
    def __init__(self, api_key=Config.GEMINI_API_KEY):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash-latest')
        self.search_model = genai.GenerativeModel(
            'gemini-1.5-flash-latest',
            tools=[{"google_search_retrieval": {}}]
        )

    def generate_taste_profile(self, watch_history_summary):
        prompt = f"""
        Based on the following media watch history (titles, genres, and overviews), 
        generate a condensed, plain-text "User Taste Profile". 
        Focus on recurring themes, preferred genres, and specific dislikes or stylistic preferences.
        Keep it under 200 words.
        
        Watch History:
        {watch_history_summary}
        """
        response = self.model.generate_content(prompt)
        return response.text.strip()

    def curate_recommendations(self, taste_profile, candidates):
        prompt = f"""
        User Taste Profile: {taste_profile}
        
        Candidate Titles for this week:
        {candidates}
        
        Using Google Search to verify current critical consensus and audience reception (e.g., from Reddit, Rotten Tomatoes), 
        select the top 5 movies and top 3 TV series from the candidates that best match the User Taste Profile.
        
        For each selection, provide:
        1. Title
        2. TMDB ID (exactly as provided in candidates)
        3. A one-sentence justification explaining why it matches the profile.
        
        Return the result in a structured format that I can easily parse (JSON-like or clear list).
        """
        response = self.search_model.generate_content(prompt)
        return response.text.strip()
