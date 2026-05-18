# AI Agents Documentation

## Jules AI Agent
The Jules AI agent is designed to handle implementation and testing within a temporary Linux VM environment. 

### Environment Setup
To set up the environment for Jules (or any agent in a clean VM):
1. Run the setup script: `bash setup_jules.sh`
2. (Optional) Provide a Gemini API key: `bash setup_jules.sh --gemini-key YOUR_KEY`

This script handles:
- Dependency installation (`requirements.txt` and `requirements-dev.txt`).
- Dummy `.env` configuration.
- Database initialization and seeding with authentic taste profile data.
- Pre-commit hook installation.

### Workflow
- Use the **Makefile** for common tasks:
  - `make test`: Run all unit tests.
  - `make lint`: Check code style.
  - `make format`: Auto-format code.
  - `make run-test-discovery`: Run the discovery pipeline without sending Telegram messages.
- For testing implementation changes, always use `python3 -m unittest discover tests`.
- For manual verification of discovery logic, use `python3 main.py discover --no-telegram`.

---

Make sure to commit after logical implementation steps with a meaningful but concise commit message. Do not use other git actions that could manipulate the git project history.
