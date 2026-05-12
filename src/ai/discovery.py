from src.clients.tmdb import TMDBClient
from src.clients.radarr import RadarrClient
from src.clients.sonarr import SonarrClient
from src.clients.jellyfin import JellyfinClient
from src.ai.gemini import GeminiClient
from src.utils.llm import extract_json_from_response
from src.database import Database
from src.config import Config
import json

class DiscoveryPipeline:
    def __init__(self):
        self.tmdb = TMDBClient(Config.TMDB_API_KEY)
        self.radarr = RadarrClient(Config.RADARR_URL, Config.RADARR_API_KEY)
        self.sonarr = SonarrClient(Config.SONARR_URL, Config.SONARR_API_KEY)
        self.jellyfin = JellyfinClient(Config.JELLYFIN_URL, Config.JELLYFIN_API_KEY, Config.JELLYFIN_USER_ID)
        self.gemini = GeminiClient()
        self.db = Database()

    def _get_existing_tmdb_ids(self):
        existing_ids = set()
        
        # Radarr
        movies = self.radarr.get_movies()
        for m in movies:
            if m.get('tmdbId'): existing_ids.add(m['tmdbId'])
            
        # Sonarr
        series = self.sonarr.get_series()
        for s in series:
            # Sonarr stores tvdbId, but might have tmdbId too. 
            # We'll also check titles just in case if tmdbId is missing.
            if s.get('tmdbId'): existing_ids.add(s['tmdbId'])
            
        # Jellyfin
        jf_items = self.jellyfin.get_recent_items(limit=200).get('Items', [])
        for item in jf_items:
            # Jellyfin ExternalIds: {'Tmdb': '123'}
            tmdb_id = item.get('ExternalIds', {}).get('Tmdb')
            if tmdb_id: existing_ids.add(int(tmdb_id))
            
        return existing_ids

    def run_weekly_discovery(self):
        # 1. Get Taste Profile
        profile = self.db.get_taste_profile()
        if not profile:
            raise ValueError("Taste profile missing. Run Profiler first.")

        # 2. Get Existing Media
        existing_ids = self._get_existing_tmdb_ids()

        # 3. Discover Candidates
        new_movies = self.tmdb.discover_new_releases().get('results', [])
        new_tv = self.tmdb.discover_new_tv().get('results', [])

        # 4. Filter
        candidate_movies = [m for m in new_movies if m['id'] not in existing_ids]
        candidate_tv = [t for t in new_tv if t['id'] not in existing_ids]

        # 5. Prepare candidates for Gemini
        candidates_text = "Movies:\n"
        for m in candidate_movies[:20]: # Limit to top 20 popular new releases
            candidates_text += f"- {m['title']} (TMDB ID: {m['id']}): {m['overview']}\n"
        
        candidates_text += "\nTV Series:\n"
        for t in candidate_tv[:20]:
            candidates_text += f"- {t['name']} (TMDB ID: {t['id']}): {t['overview']}\n"

        # 6. Curate via Gemini
        raw_curation = self.gemini.curate_recommendations(profile, candidates_text)
        
        # 7. Parse and return
        # Clean up JSON if LLM added backticks
        json_str = extract_json_from_response(raw_curation)
            
        try:
            data = json.loads(json_str)
            recommendations = data.get('recommendations', [])
            for i, rec in enumerate(recommendations):
                rec['position'] = i + 1
            return recommendations, raw_curation
        except Exception as e:
            print(f"Error parsing Gemini curation: {e}")
            # Fallback or re-raise
            raise
