from .base import BaseClient

class RadarrClient(BaseClient):
    def get_movies(self):
        return self._get("/api/v3/movie")

    def add_movie(self, tmdb_id, root_folder_path, quality_profile_id):
        # First lookup movie to get required metadata
        movie_info = self._get("/api/v3/movie/lookup", params={"term": f"tmdb:{tmdb_id}"})[0]
        
        payload = {
            "title": movie_info["title"],
            "qualityProfileId": quality_profile_id,
            "titleSlug": movie_info["titleSlug"],
            "tmdbId": tmdb_id,
            "rootFolderPath": root_folder_path,
            "monitored": True,
            "addOptions": {"searchForMovie": True}
        }
        return self._post("/api/v3/movie", json=payload)
