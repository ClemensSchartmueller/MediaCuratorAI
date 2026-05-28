import argparse
import sys
from src.ai.profiler import Profiler
from src.ai.discovery import DiscoveryPipeline
from src.telegram.bot import TelegramBot
from src.database import Database
from src.telegram.formatter import format_markdown_for_telegram


def main():
    # Reconfigure stdout/stderr to UTF-8 to support printing emojis on all platforms
    if sys.platform == "win32":
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(description="Media Curator AI")
    parser.add_argument("command", choices=["profile", "discover", "listen"], help="Command to run")
    parser.add_argument("--no-telegram", action="store_true", help="Print output to CLI instead of sending via Telegram (for testing)")
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
            
            # Format message for Telegram with Markdown styling
            message = "# Weekly Media Recommendations\n\n"
            for rec in recs:
                icon = "🎥" if rec['media_type'] == "movie" else "📺"
                message += f"**{rec['position']}. {icon} {rec['title']}**\n"
                message += f"Why: *{rec['justification']}*\n\n"
            
            message += "Reply with 'Add [Title]' or 'Download #1' to add to your library!"
            
            if args.no_telegram:
                print("\n--- TEST OUTPUT (No Telegram) ---")
                print(format_markdown_for_telegram(message))
                print("-------------------------------\n")
            else:
                # Send to Telegram
                bot = TelegramBot()
                bot.send_message(message)
                print("Recommendations sent via Telegram.")
        except Exception as e:
            print(f"Error during discovery: {e}")

    elif args.command == "listen":
        print("Starting Telegram Listener...")
        bot = TelegramBot()
        bot.listen_loop()


if __name__ == "__main__":
    main()
