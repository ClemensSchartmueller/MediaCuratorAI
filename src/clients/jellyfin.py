from .base import BaseClient


class JellyfinClient(BaseClient):
    def __init__(self, base_url, api_key, user_id):
        super().__init__(base_url, api_key)
        self.user_id = user_id

    def _get(self, endpoint, params=None, headers=None):
        if not headers:
            headers = {}
        headers.update({"X-Emby-Token": self.api_key})
        return super()._get(endpoint, params=params, headers=headers)

    def get_watch_history(self):
        # Fetches playback reporting history if available, or just items
        # For simple profiling, we'll get the user's played items
        endpoint = f"/Users/{self.user_id}/Items"
        params = {
            "Recursive": True,
            "IsPlayed": True,
            "Fields": "Genres,Overview,OfficialRating",
            "IncludeItemTypes": "Movie,Series",
        }
        return self._get(endpoint, params=params)

    def get_recent_items(self, limit=50):
        endpoint = f"/Users/{self.user_id}/Items"
        params = {
            "SortBy": "DateCreated",
            "SortOrder": "Descending",
            "Limit": limit,
            "Recursive": True,
            "Fields": "Genres,Overview",
            "IncludeItemTypes": "Movie,Series",
        }
        return self._get(endpoint, params=params)
