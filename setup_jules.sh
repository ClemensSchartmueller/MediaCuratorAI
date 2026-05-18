#!/bin/bash
# setup_jules.sh
# Setup script for Jules AI implementation and testing environment (Linux VM Mode)

GEMINI_KEY="your_actual_key_here_for_live_testing"

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --gemini-key) GEMINI_KEY="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

echo -e "\e[36m--- Starting Jules AI Environment Setup (Linux VM Mode) ---\e[0m"

# 1. Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 2. Create dummy .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating dummy .env file..."
    cat <<EOF > .env
JELLYFIN_URL=http://localhost:8096
JELLYFIN_API_KEY=dummy_key
JELLYFIN_USER_ID=dummy_id
SONARR_URL=http://localhost:8989
SONARR_API_KEY=dummy_key
RADARR_URL=http://localhost:7878
RADARR_API_KEY=dummy_key
TMDB_API_KEY=dummy_key
GEMINI_API_KEY=$GEMINI_KEY
TELEGRAM_BOT_TOKEN=dummy_token
TELEGRAM_CHAT_ID=123456789
EOF
fi

# 3. Initialize and Seed Database
echo "Initializing and seeding local SQLite database..."
python3 -c "
from src.database import Database
db = Database()
profile = \"\"\"This user possesses an eclectic taste dominated by visceral action, sobering real-world conflict, and investigative social commentary. They gravitate toward high-stakes narratives, favoring gritty action thrillers characterized by professional 'operator' tropes (e.g., John Wick, Extraction) and immersive war dramas that blend history with intense tactical survival (e.g., The Covenant, Civil War). There is a clear secondary preference for R-rated comedy, ranging from nostalgic raunchiness (American Pie) to modern, character-driven humor (No Hard Feelings). While they appreciate blockbuster spectacles, they balance this with introspective, somber dramas focused on grief and isolation (Nomadland, The After). Overall, the user values intensity, technical filmmaking skill, and stories that confront the darker or more complex aspects of human nature and society.\"\"\"
db.save_taste_profile(profile)

recs = [
    {'tmdb_id': 603, 'title': 'The Matrix', 'media_type': 'movie', 'position': 1},
    {'tmdb_id': 157336, 'title': 'Interstellar', 'media_type': 'movie', 'position': 2},
    {'tmdb_id': 1396, 'title': 'Breaking Bad', 'media_type': 'tv', 'position': 3}
]
db.set_active_recommendations(recs)
print('Database seeded with taste profile and dummy recommendations.')
"

# 4. Set up pre-commit
if command -v pre-commit &> /dev/null; then
    echo "Installing pre-commit hooks..."
    pre-commit install
fi

# 5. Run Tests to verify setup
echo -e "\e[33mRunning initial test suite...\e[0m"
python3 -m unittest discover tests

echo -e "\n\e[32m--- Setup Complete ---\e[0m"
echo "You can now run the app in test mode using:"
echo -e "\e[90mpython3 main.py discover --no-telegram\e[0m"
echo -e "Or use the Makefile: \e[90mmake test\e[0m"
