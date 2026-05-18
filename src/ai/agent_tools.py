import time
from requests.exceptions import ConnectionError, HTTPError, Timeout
from src.ai.profiler import Profiler
from src.ai.discovery import DiscoveryPipeline
from src.clients.exceptions import MediaAlreadyExistsError
from src.database import Database
from src.config import Config


def _is_retryable_error(error):
    if isinstance(error, (Timeout, ConnectionError)):
        return True
    if isinstance(error, HTTPError):
        status_code = getattr(getattr(error, "response", None), "status_code", None)
        return status_code == 429 or (status_code is not None and status_code >= 500)
    return False


def _execute_with_retry(fn, notify_fn, label, max_retries=3):
    """Executes a function with exponential backoff and sends retry warnings to Telegram."""
    delay = 2
    for attempt in range(max_retries):
        try:
            return fn()
        except Exception as e:
            if not _is_retryable_error(e):
                err_msg = f"Failed to execute {label}. Error: {str(e)}"
                notify_fn(f"❌ {err_msg}")
                return err_msg

            if attempt == max_retries - 1:
                err_msg = f"Failed to execute {label} after {max_retries} attempts. Error: {str(e)}"
                notify_fn(f"❌ {err_msg}")
                return err_msg

            notify_fn(
                f"⚠️ Transient API/network error during {label}. Retrying in {delay}s... (Attempt {attempt+1}/{max_retries})"
            )
            time.sleep(delay)
            delay *= 2


def create_tools(tmdb, radarr, sonarr, bot_instance):
    notify_fn = bot_instance.send_message

    def add_movie_to_library(title: str) -> str:
        """Searches TMDB for the movie and adds it via Radarr. Use this when the user explicitly wants to download or add a movie."""

        def action():
            results = tmdb.search_multi(title)
            movies = [
                r for r in results.get("results", []) if r.get("media_type") == "movie"
            ]
            if not movies:
                return f"Could not find any movie matching '{title}'."
            if len(movies) > 1:
                candidates = []
                for movie in movies[:3]:
                    release_year = (movie.get("release_date") or "")[:4]
                    display_title = movie.get("title") or "Unknown title"
                    candidates.append(
                        f"{display_title} ({release_year})"
                        if release_year
                        else display_title
                    )
                return (
                    f"Multiple movie matches found for '{title}'. "
                    f"Please be more specific (for example include the year): {', '.join(candidates)}."
                )
            best_match = movies[0]
            try:
                radarr.add_movie(
                    best_match["id"],
                    Config.RADARR_ROOT_FOLDER,
                    Config.RADARR_QUALITY_PROFILE,
                )
            except MediaAlreadyExistsError as e:
                return (
                    f"The {e.media_kind} '{e.title}' is already in your "
                    f"{e.library_name} library!"
                )
            return f"Successfully added movie '{best_match.get('title')}' to your Radarr library!"

        return _execute_with_retry(action, notify_fn, f"adding movie '{title}'")

    def add_series_to_library(title: str) -> str:
        """Searches TMDB for the series and adds it via Sonarr. Use this when the user explicitly wants to download or add a TV show/series."""

        def action():
            results = tmdb.search_multi(title)
            series = [
                r for r in results.get("results", []) if r.get("media_type") == "tv"
            ]
            if not series:
                return f"Could not find any TV series matching '{title}'."
            if len(series) > 1:
                candidates = []
                for show in series[:3]:
                    first_air_year = (show.get("first_air_date") or "")[:4]
                    display_title = show.get("name") or "Unknown title"
                    candidates.append(
                        f"{display_title} ({first_air_year})"
                        if first_air_year
                        else display_title
                    )
                return (
                    f"Multiple TV series matches found for '{title}'. "
                    f"Please be more specific (for example include the year): {', '.join(candidates)}."
                )
            best_match = series[0]
            try:
                sonarr.add_series(
                    best_match["id"],
                    Config.SONARR_ROOT_FOLDER,
                    Config.SONARR_QUALITY_PROFILE,
                )
            except MediaAlreadyExistsError as e:
                return (
                    f"The {e.media_kind} '{e.title}' is already in your "
                    f"{e.library_name} library!"
                )
            return f"Successfully added series '{best_match.get('name')}' to your Sonarr library!"

        return _execute_with_retry(action, notify_fn, f"adding series '{title}'")

    def get_media_information(title: str) -> str:
        """Searches TMDB and returns plot, release year, rating, and other details for a movie or TV show. Use this when the user asks for information or plot details about a movie or series."""

        def action():
            results = tmdb.search_multi(title)
            if not results.get("results"):
                return f"Could not find any information for '{title}'."
            best_match = results["results"][0]
            media_type = best_match.get("media_type", "movie")
            if media_type == "movie":
                details = tmdb.get_movie_details(best_match["id"])
                return (
                    f"🎬 **{details.get('title')}** ({details.get('release_date', '')[:4]})\n"
                    f"⭐ Rating: {details.get('vote_average')}/10\n"
                    f"📝 Plot: {details.get('overview')}"
                )
            elif media_type == "tv":
                details = tmdb.get_tv_details(best_match["id"])
                return (
                    f"📺 **{details.get('name')}** ({details.get('first_air_date', '')[:4]})\n"
                    f"⭐ Rating: {details.get('vote_average')}/10\n"
                    f"📝 Plot: {details.get('overview')}"
                )
            return "Unsupported media type."

        return _execute_with_retry(action, notify_fn, f"fetching details for '{title}'")

    def discover_by_genre(genre_name: str, media_type: str) -> str:
        """Queries TMDB by genre to discover popular or recent movies or TV shows. media_type must be either 'movie' or 'tv'."""

        def action():
            genres_resp = tmdb.get_genres(media_type)
            genres = genres_resp.get("genres", [])
            genre_id = None
            for g in genres:
                if g["name"].lower() == genre_name.lower():
                    genre_id = g["id"]
                    break
            if not genre_id:
                available_genres = ", ".join([g["name"] for g in genres])
                return f"Could not find genre '{genre_name}' for {media_type}. Available genres: {available_genres}"

            discovery = tmdb.discover_by_genre(genre_id, media_type)
            items = discovery.get("results", [])[:5]
            if not items:
                return f"No results found for genre '{genre_name}'."

            res = []
            for i in items:
                name = i.get("title") or i.get("name")
                rating = i.get("vote_average", "N/A")
                overview_raw = (i.get("overview") or "").strip()
                if not overview_raw:
                    overview = "No overview available."
                elif len(overview_raw) > 120:
                    overview = overview_raw[:120] + "..."
                else:
                    overview = overview_raw
                res.append(f"- **{name}** (Rating: {rating})\n  _{overview}_")
            return (
                f"Top 5 popular {media_type}s in genre '{genre_name}':\n"
                + "\n".join(res)
            )

        return _execute_with_retry(
            action, notify_fn, f"discovering {media_type} in genre '{genre_name}'"
        )

    def generate_new_proposals() -> str:
        """Manually triggers a fresh calculation of recommendations by re-analyzing Jellyfin watch history and querying TMDB. Returns the updated top list."""

        def action():
            notify_fn("🔄 Updating taste profile from Jellyfin...")
            profiler = Profiler()
            profiler.run()

            notify_fn("✨ Generating weekly recommendations from TMDB...")
            pipeline = DiscoveryPipeline()
            recs, raw_curation = pipeline.run_weekly_discovery()

            db = Database()
            db.set_active_recommendations(recs)

            message = "🎬 Fresh Media Recommendations Generated! 🎬\n\n"
            for rec in recs:
                icon = "🎥" if rec["media_type"] == "movie" else "📺"
                message += f"{rec['position']}. {icon} {rec['title']}\n"
                message += f"   Why: {rec['justification']}\n\n"
            message += (
                "Reply with 'Add [Title]' or 'Download #1' to add to your library!"
            )
            return message

        return _execute_with_retry(action, notify_fn, "generating fresh proposals")

    def clear_chat_history() -> str:
        """Completely clears all conversation history and resets the assistant's state. Use this when the user explicitly requests to clear, reset, or wipe their chat history."""
        return bot_instance._clear_history_action()

    def compress_chat_history() -> str:
        """Compresses the conversation history into a concise context summary to save API tokens and memory. Use this when the user explicitly requests to compress, condense, or summarize history."""
        return bot_instance._compress_history_action()

    return [
        add_movie_to_library,
        add_series_to_library,
        get_media_information,
        discover_by_genre,
        generate_new_proposals,
        clear_chat_history,
        compress_chat_history,
    ]
