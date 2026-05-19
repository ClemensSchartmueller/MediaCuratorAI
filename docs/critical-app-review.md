# Critical App Review

This review captures the current state of Media Curator AI from three perspectives: developer quality, user experience, and product direction. It is based on the current implementation, test suite, and a manual CLI verification run.

## 1. Developer review

### What is working well

- The project has a clear core flow (`profile`, `discover`, `listen`) in `/home/runner/work/MediaCuratorAI/MediaCuratorAI/main.py`.
- The application has solid test coverage across discovery, Telegram behavior, formatting, and API clients in `/home/runner/work/MediaCuratorAI/MediaCuratorAI/tests`.
- Retry handling for transient API/network errors is already present in `/home/runner/work/MediaCuratorAI/MediaCuratorAI/src/ai/agent_tools.py`.
- Radarr and Sonarr integrations already contain duplicate-prevention and fallback logic in `/home/runner/work/MediaCuratorAI/MediaCuratorAI/src/clients/radarr.py` and `/home/runner/work/MediaCuratorAI/MediaCuratorAI/src/clients/sonarr.py`.

### Main concerns

1. **Observability is weak**
   - The codebase still relies heavily on `print()` instead of structured logging, for example in `/home/runner/work/MediaCuratorAI/MediaCuratorAI/main.py`, `/home/runner/work/MediaCuratorAI/MediaCuratorAI/src/ai/discovery.py`, and `/home/runner/work/MediaCuratorAI/MediaCuratorAI/src/telegram/bot.py`.
   - This makes production troubleshooting harder, especially in containers and long-running services.

2. **Configuration validation is missing**
   - `/home/runner/work/MediaCuratorAI/MediaCuratorAI/src/config.py` loads environment variables directly but does not validate required values or give actionable startup errors.
   - During manual verification, `python3 main.py discover --no-telegram` failed with a raw connection error when local media services were unavailable instead of a guided setup or health-check message.

3. **Some error handling is too broad**
   - `/home/runner/work/MediaCuratorAI/MediaCuratorAI/src/telegram/bot.py` and `/home/runner/work/MediaCuratorAI/MediaCuratorAI/src/ai/discovery.py` catch broad exceptions and often only print the error.
   - This risks hiding context that would help diagnose failures.

4. **Type safety and maintainability could be better**
   - Core modules such as `/home/runner/work/MediaCuratorAI/MediaCuratorAI/src/ai/discovery.py`, `/home/runner/work/MediaCuratorAI/MediaCuratorAI/src/database.py`, and `/home/runner/work/MediaCuratorAI/MediaCuratorAI/src/telegram/bot.py` currently have no type hints.
   - That increases maintenance cost as the app grows.

5. **LLM output parsing is fragile**
   - `/home/runner/work/MediaCuratorAI/MediaCuratorAI/src/ai/discovery.py` strips fenced code blocks before parsing JSON from Gemini output.
   - This works for happy paths, but it is not as robust as structured output or stricter validation.

### Highest-value engineering improvements

- Add structured logging and log levels across CLI, discovery, and Telegram flows.
- Validate required configuration at startup with clear remediation messages.
- Add type hints to public functions and core data paths.
- Harden Gemini response parsing with stricter schema validation.

## 2. UX review

### What is working well

- The Telegram experience is broad and flexible: recommendations, direct download requests, information lookup, genre discovery, and history management are all exposed in the conversational interface described in `/home/runner/work/MediaCuratorAI/MediaCuratorAI/README.md`.
- `/home/runner/work/MediaCuratorAI/MediaCuratorAI/src/telegram/formatter.py` gives the bot a more polished Telegram presentation.
- Conversation persistence and compression in `/home/runner/work/MediaCuratorAI/MediaCuratorAI/src/telegram/bot.py` are thoughtful cost and continuity features.

### Main concerns

1. **Initial setup is still high-friction**
   - Users must configure multiple services and API keys, but the app does not guide them through validation or explain which dependency failed first.

2. **Failures can feel technical rather than helpful**
   - Manual discovery currently surfaces a raw connection error if Radarr/Sonarr/Jellyfin are unreachable.
   - A user-friendly health summary would be much easier to act on.

3. **Ambiguous search flows could be smoother**
   - `/home/runner/work/MediaCuratorAI/MediaCuratorAI/src/ai/agent_tools.py` correctly asks for clarification when multiple titles match, but it does not provide a simple numbered selection flow.

4. **Success paths could be more explicit**
   - The CLI commands report activity, but they do not consistently confirm what was saved, what was skipped, or what the user should do next.

### Highest-value UX improvements

- Add a startup health check that reports configuration and service connectivity in user language.
- Improve ambiguous title resolution with numbered reply options.
- Add clearer success and next-step messaging after `profile` and `discover`.

## 3. Product review

### Current product strengths

- The app already solves a compelling self-hosted workflow: profile a user from Jellyfin history, discover new releases, curate them with AI, and let the user act on them from Telegram.
- The scope is focused and coherent rather than overly broad.

### Best next product opportunities

1. **Negative feedback loop**
   - Let users mark a recommendation as not interesting so future curation can improve.

2. **Recommendation confidence or match score**
   - Show why a recommendation is strong, not just the free-text justification.

3. **Availability context**
   - Tell users where the title is available or whether it is already pending in Radarr/Sonarr.

4. **Profile transparency**
   - Show how the taste profile changed over time and what signals are driving recommendations.

5. **Shared or household recommendations**
   - Support multi-user or blended profiles for shared media environments.

## Suggested priority order

### P0

- Add startup configuration and service validation.
- Replace `print()`-based diagnostics with structured logging.

### P1

- Improve ambiguous-title UX with numbered follow-up actions.
- Add recommendation feedback (`skip`, `not interested`) to improve the loop.

### P2

- Add confidence scoring, recommendation explanations, and taste-profile history.
- Explore household/shared recommendation support.
