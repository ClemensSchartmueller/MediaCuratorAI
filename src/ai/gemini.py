from google import genai
from google.genai import types
from src.config import Config

class GeminiClient:
    def __init__(self, api_key=Config.GEMINI_API_KEY):
        self.client = genai.Client(api_key=api_key)
        self.model_id = 'gemini-flash-latest'

    def generate_content(self, prompt, config=None):
        """Wrapper for simple content generation used by the Signal bot."""
        return self.client.models.generate_content(
            model=self.model_id,
            contents=prompt,
            config=config
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
        response = self.generate_content(prompt)
        return response.text.strip()

    def curate_recommendations(self, taste_profile, candidates):
        prompt = f"""
        User Taste Profile: {taste_profile}
        
        Candidate Titles for this week:
        {candidates}
        
        Using Google Search to verify current critical consensus and audience reception (e.g., from Reddit, Rotten Tomatoes), 
        select the top 5 movies and top 3 TV series from the candidates that best match the User Taste Profile.
        
        Return the result as a JSON object with a key 'recommendations' containing a list of objects.
        Each object must have:
        - "title": The title of the movie or series.
        - "tmdb_id": The exact TMDB ID provided in candidates.
        - "media_type": Either "movie" or "tv".
        - "justification": A one-sentence explanation of why it matches the profile.

        Ensure the output is ONLY the JSON object.
        """
        response = self.generate_content(
            prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())]
            )
        )
        return response.text.strip()
