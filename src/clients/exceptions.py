class MediaAlreadyExistsError(Exception):
    def __init__(self, media_kind, title, library_name):
        self.media_kind = media_kind
        self.title = title
        self.library_name = library_name
        super().__init__(
            f"{media_kind} '{title}' already exists in {library_name} library."
        )
