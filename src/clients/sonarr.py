from .base import BaseClient

class SonarrClient(BaseClient):
    def get_series(self):
        return self._get("/api/v3/series")

    def add_series(self, tmdb_id, root_folder_path, quality_profile_id):
        # Sonarr uses TVDB ID usually, but we can look up via TMDB if needed
        # TMDB discovery gives us TMDB ID. Sonarr lookup supports tmdb:
        series_info = self._get("/api/v3/series/lookup", params={"term": f"tmdb:{tmdb_id}"})[0]
        
        # Pre-check if series is already in the library to avoid 400 Bad Request
        try:
            existing_series = self.get_series()
            for s in existing_series:
                if (s.get("tvdbId") == series_info.get("tvdbId")) or \
                   (s.get("tmdbId") and s.get("tmdbId") == series_info.get("tmdbId")) or \
                   (s.get("tmdbId") and s.get("tmdbId") == tmdb_id):
                    return f"The series '{series_info.get('title')}' is already in your Sonarr library!"
        except Exception as e:
            print(f"Warning: Failed to check for duplicate series in Sonarr: {str(e)}")

        # Fetch and validate root folders dynamically
        try:
            root_folders = self._get("/api/v3/rootfolder")
            available_paths = [folder.get("path") for folder in root_folders if folder.get("path")]
            if not available_paths:
                raise Exception("No root folders are configured in Sonarr.")
            if root_folder_path not in available_paths:
                print(f"Warning: Configured root folder '{root_folder_path}' does not exist in Sonarr. Falling back to '{available_paths[0]}'.")
                root_folder_path = available_paths[0]
        except Exception as e:
            print(f"Warning: Failed to fetch root folders from Sonarr: {str(e)}. Using configured path: {root_folder_path}")

        # Fetch and validate quality profiles dynamically
        try:
            quality_profiles = self._get("/api/v3/qualityprofile")
            available_profile_ids = [profile.get("id") for profile in quality_profiles if profile.get("id")]
            if not available_profile_ids:
                raise Exception("No quality profiles are configured in Sonarr.")
            if quality_profile_id not in available_profile_ids:
                print(f"Warning: Configured quality profile ID '{quality_profile_id}' does not exist in Sonarr. Falling back to ID '{available_profile_ids[0]}'.")
                quality_profile_id = available_profile_ids[0]
        except Exception as e:
            print(f"Warning: Failed to fetch quality profiles from Sonarr: {str(e)}. Using configured ID: {quality_profile_id}")

        payload = {
            "title": series_info["title"],
            "qualityProfileId": quality_profile_id,
            "titleSlug": series_info["titleSlug"],
            "tvdbId": series_info["tvdbId"],
            "tmdbId": series_info.get("tmdbId"),
            "rootFolderPath": root_folder_path,
            "monitored": True,
            "addOptions": {"searchForMissingEpisodes": True}
        }
        return self._post("/api/v3/series", json=payload)
