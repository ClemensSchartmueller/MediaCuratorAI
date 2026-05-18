from .base import BaseClient

class RadarrClient(BaseClient):
    def get_movies(self):
        return self._get("/api/v3/movie")

    def add_movie(self, tmdb_id, root_folder_path, quality_profile_id):
        # First lookup movie to get required metadata
        movie_info = self._get("/api/v3/movie/lookup", params={"term": f"tmdb:{tmdb_id}"})[0]
        
        # Pre-check if movie is already in the library to avoid 400 Bad Request
        if movie_info.get("id") is not None and movie_info.get("id") > 0:
            return f"The movie '{movie_info.get('title')}' is already in your Radarr library!"

        # Fetch and validate root folders dynamically
        try:
            root_folders = self._get("/api/v3/rootfolder")
            available_paths = [folder.get("path") for folder in root_folders if folder.get("path")]
            if not available_paths:
                raise Exception("No root folders are configured in Radarr.")
            if root_folder_path not in available_paths:
                print(f"Warning: Configured root folder '{root_folder_path}' does not exist in Radarr. Falling back to '{available_paths[0]}'.")
                root_folder_path = available_paths[0]
        except Exception as e:
            print(f"Warning: Failed to fetch root folders from Radarr: {str(e)}. Using configured path: {root_folder_path}")

        # Fetch and validate quality profiles dynamically
        try:
            quality_profiles = self._get("/api/v3/qualityprofile")
            available_profile_ids = [profile.get("id") for profile in quality_profiles if profile.get("id")]
            if not available_profile_ids:
                raise Exception("No quality profiles are configured in Radarr.")
            if quality_profile_id not in available_profile_ids:
                print(f"Warning: Configured quality profile ID '{quality_profile_id}' does not exist in Radarr. Falling back to ID '{available_profile_ids[0]}'.")
                quality_profile_id = available_profile_ids[0]
        except Exception as e:
            print(f"Warning: Failed to fetch quality profiles from Radarr: {str(e)}. Using configured ID: {quality_profile_id}")
        
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
