from .base import BaseClient
from datetime import datetime, timedelta


class TMDBClient(BaseClient):
    def __init__(self, api_key):
        super().__init__("https://api.themoviedb.org/3", api_key)
        self.is_bearer = api_key.startswith("eyJ")

    def _get(self, endpoint, params=None, headers=None):
        if not headers:
            headers = {}
        if not params:
            params = {}

        if self.is_bearer:
            headers["Authorization"] = f"Bearer {self.api_key}"
        else:
            params["api_key"] = self.api_key

        # TMDB doesn't use X-Api-Key, so we avoid BaseClient adding it
        # by calling requests directly or passing custom headers to super
        url = f"{self.base_url}{endpoint}"
        response = self.session.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()

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
            "with_release_type": "4|5",  # Digital or Physical
            "release_date.gte": thirty_days_ago.strftime("%Y-%m-%d"),
            "release_date.lte": today.strftime("%Y-%m-%d"),
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
            "first_air_date.lte": today.strftime("%Y-%m-%d"),
        }
        return self._get("/discover/tv", params=params)

    def search_multi(self, query):
        """Searches for movies, TV shows, and people based on a query string."""
        return self._get("/search/multi", params={"query": query})

    def search_movie(self, query, year=None):
        """Searches specifically for movies. Supports optional year filtering."""
        params = {"query": query}
        if year:
            params["year"] = year
        return self._get("/search/movie", params=params)

    def search_tv(self, query, year=None):
        """Searches specifically for TV shows. Supports optional year filtering."""
        params = {"query": query}
        if year:
            params["first_air_date_year"] = year
        return self._get("/search/tv", params=params)

    def get_movie_details(self, movie_id):
        """Fetches detailed information for a specific movie ID."""
        return self._get(f"/movie/{movie_id}")

    def get_tv_details(self, tv_id):
        """Fetches detailed information for a specific TV show ID."""
        return self._get(f"/tv/{tv_id}")

    def get_genres(self, media_type):
        """Gets the list of official TMDB genres for 'movie' or 'tv'."""
        return self._get(f"/genre/{media_type}/list")

    def discover_by_genre(self, genre_id, media_type):
        """Discovers popular movies or TV shows belonging to a specific genre ID."""
        return self._get(
            f"/discover/{media_type}",
            params={"with_genres": genre_id, "sort_by": "popularity.desc", "page": 1},
        )
