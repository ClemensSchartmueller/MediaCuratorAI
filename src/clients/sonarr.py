from .base import BaseClient


class SonarrClient(BaseClient):
    def get_series(self):
        return self._get("/api/v3/series")

    def add_series(self, tmdb_id, root_folder_path, quality_profile_id):
        # Sonarr uses TVDB ID usually, but we can look up via TMDB if needed
        # TMDB discovery gives us TMDB ID. Sonarr lookup supports tmdb:
        series_info = self._get(
            "/api/v3/series/lookup", params={"term": f"tmdb:{tmdb_id}"}
        )[0]

        payload = {
            "title": series_info["title"],
            "qualityProfileId": quality_profile_id,
            "titleSlug": series_info["titleSlug"],
            "tvdbId": series_info["tvdbId"],
            "tmdbId": series_info.get("tmdbId"),
            "rootFolderPath": root_folder_path,
            "monitored": True,
            "addOptions": {"searchForMissingEpisodes": True},
        }
        return self._post("/api/v3/series", json=payload)
