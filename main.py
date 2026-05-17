import argparse
import sys
from src.ai.profiler import Profiler
from src.ai.discovery import DiscoveryPipeline
from src.signals.bot import SignalBot
from src.database import Database
import json
import re

def main():
    # Reconfigure stdout/stderr to UTF-8 to support printing emojis on all platforms
    if sys.platform == "win32":
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(description="Media Curator AI")
    parser.add_argument("command", choices=["profile", "discover", "listen"], help="Command to run")
    parser.add_argument("--no-signal", action="store_true", help="Print output to CLI instead of sending via Signal (for testing)")
    args = parser.parse_args()

    if args.command == "profile":
        print("Running Profiler...")
        profiler = Profiler()
        profile = profiler.run()
        print(f"Taste Profile generated and saved:\n{profile}")

    elif args.command == "discover":
        print("Running Weekly Discovery...")
        pipeline = DiscoveryPipeline()
        try:
            recs, raw_curation = pipeline.run_weekly_discovery()
            
            db = Database()
            db.set_active_recommendations(recs)
            
            # Format message for Signal
            message = "🎬 Weekly Media Recommendations 🎬\n\n"
            for rec in recs:
                icon = "🎥" if rec['media_type'] == "movie" else "📺"
                message += f"{rec['position']}. {icon} {rec['title']}\n"
                message += f"   Why: {rec['justification']}\n\n"
            
            message += "Reply with 'Add [Title]' or 'Download #1' to add to your library!"
            
            if args.no_signal:
                print("\n--- TEST OUTPUT (No Signal) ---")
                print(message)
                print("-------------------------------\n")
            else:
                # Send to Signal
                bot = SignalBot()
                bot.send_message(message)
                print("Recommendations sent via Signal.")
        except Exception as e:
            print(f"Error during discovery: {e}")

    elif args.command == "listen":
        print("Starting Signal Listener...")
        bot = SignalBot()
        bot.listen_loop()

if __name__ == "__main__":
    main()
