# Gemini CLI Instructions

- **Source Control:** Make sure to commit after logical implementation steps with a meaningful but concise commit message. Do not use other git actions that could manipulate the git project history.
- **Python Environment:** 
  - On local development machines, always use the `.venv` to execute anything python related.
  - In temporary agent VMs (like Jules), use the system python after running `bash setup_jules.sh`.
- **Testing:** 
  - Always run tests using `make test` or `python3 -m unittest discover tests` before considering a task complete.
  - Use `python3 main.py discover --no-signal` to verify discovery logic without external side effects.
- **Development Tools:** 
  - Utilize `make lint` and `make format` to maintain code standards.
  - Ensure `requirements-dev.txt` is installed for all development tasks.
- **Setup:** If starting in a new environment, run `bash setup_jules.sh` to initialize the database with seed data and configure dummy environment variables.
