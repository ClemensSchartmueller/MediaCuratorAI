import requests

class BaseClient:
    def __init__(self, base_url, api_key=None):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.session = requests.Session()

    def _get(self, endpoint, params=None, headers=None):
        url = f"{self.base_url}{endpoint}"
        if not headers:
            headers = {}
        if self.api_key:
            # Most Arrs use X-Api-Key, Jellyfin uses X-Emby-Token
            headers.update({"X-Api-Key": self.api_key})
        
        response = self.session.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()

    def _post(self, endpoint, json=None, params=None, headers=None):
        url = f"{self.base_url}{endpoint}"
        if not headers:
            headers = {}
        if self.api_key:
            headers.update({"X-Api-Key": self.api_key})
            
        response = self.session.post(url, json=json, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
