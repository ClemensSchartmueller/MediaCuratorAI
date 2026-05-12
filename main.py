import argparse
import sys
from src.ai.profiler import Profiler
from src.ai.discovery import DiscoveryPipeline
from src.signals.bot import SignalBot
from src.database import Database
import json
import re

def main():
    parser = argparse.ArgumentParser(description="Media Curator AI")
    parser.add_argument("command", choices=["profile", "discover", "listen"], help="Command to run")
    args = parser.parse_args()

    if args.command == "profile":
        print("Running Profiler...")
        profiler = Profiler()
        profile = profiler.run()
        print(f"Taste Profile generated and saved:\n{profile}")

    elif args.command == "discover":
        print("Running Weekly Discovery...")
        pipeline = DiscoveryPipeline()
        curation_text = pipeline.run_weekly_discovery()
        
        # Parse curation_text to populate active_recommendations
        # This is a bit tricky with raw LLM text, so we'll look for patterns
        # [Title] (TMDB ID: [ID])
        recs = []
        matches = re.finditer(r"(.+?)\s*\(TMDB ID:\s*(\d+)\)", curation_text)
        pos = 1
        for match in matches:
            title = match.group(1).strip("- ").strip()
            tmdb_id = int(match.group(2))
            # Determine type based on where it is in the text or another pattern
            media_type = "movie" # Default, maybe check context in later versions
            if "TV Series" in curation_text and curation_text.find(match.group(0)) > curation_text.find("TV Series"):
                media_type = "tv"
            
            recs.append({
                "tmdb_id": tmdb_id,
                "title": title,
                "media_type": media_type,
                "position": pos
            })
            pos += 1

        db = Database()
        db.set_active_recommendations(recs)
        
        # Send to Signal
        bot = SignalBot()
        bot.send_message(f"🎬 Weekly Media Recommendations 🎬\n\n{curation_text}\n\nReply with 'Add [Title]' or 'Download #1' to add to your library!")
        print("Recommendations sent via Signal.")

    elif args.command == "listen":
        print("Starting Signal Listener...")
        bot = SignalBot()
        bot.listen_loop()

if __name__ == "__main__":
    main()
