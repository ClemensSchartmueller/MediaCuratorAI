from .base import BaseClient
from datetime import datetime, timedelta

class TMDBClient(BaseClient):
    def __init__(self, api_key):
        super().__init__("https://api.themoviedb.org/3", api_key)

    def _get(self, endpoint, params=None, headers=None):
        if not params:
            params = {}
        params["api_key"] = self.api_key
        return super()._get(endpoint, params=params, headers=headers)

    def discover_new_releases(self):
        # Movies released to digital/VOD in last 30 days
        today = datetime.now()
        thirty_days_ago = today - timedelta(days=30)
        
        params = {
            "include_adult": False,
            "include_video": False,
            "language": "en-US",
            "page": 1,
            "sort_by": "popularity.desc",
            "with_release_type": "4|5", # Digital or Physical
            "release_date.gte": thirty_days_ago.strftime("%Y-%m-%d"),
            "release_date.lte": today.strftime("%Y-%m-%d")
        }
        return self._get("/discover/movie", params=params)

    def discover_new_tv(self):
        # TV shows with first air date in last 30 days
        today = datetime.now()
        thirty_days_ago = today - timedelta(days=30)
        
        params = {
            "include_adult": False,
            "language": "en-US",
            "page": 1,
            "sort_by": "popularity.desc",
            "first_air_date.gte": thirty_days_ago.strftime("%Y-%m-%d"),
            "first_air_date.lte": today.strftime("%Y-%m-%d")
        }
        return self._get("/discover/tv", params=params)
