# AG2 Team Setup (Aligned with AGENTS.md)

This folder provides a multi-agent AG2/autogen setup that mirrors the roles in `AGENTS.md`:

- `Orchestrator` (manager you talk to)
- `ScopeGuardian`
- `ReconAgent`
- `VulnResearchAgent`
- `ExploitationAgent`
- `ReportingAgent`
- `IntelligenceAgent`
- `ExecAgent` (optional local command execution)

This setup is for compliant bug bounty workflows only.

## Files

- `run_team.py`: run the AG2 team over an existing campaign context.
- `prompts.py`: role prompts mapped to AGENTS.md sections 2, 5, 6, 8, and 14.
- `context_loader.py`: loads campaign artifacts and AGENTS.md excerpts.
- `team_builder.py`: creates AG2 agents and llm config.
- `init_target_structure.py`: creates directory layout from AGENTS.md section 3.6.
- `web_chat.py`: local Flask chat GUI to work with the AG2 team.

## Prerequisites

- Python package available: `autogen` (detected on this machine).
- `OPENAI_API_KEY` exported.
- Optional: `AG2_MODEL` (default: `gpt-4.1-mini`).
- Optional: `OPENAI_BASE_URL`.

## Quick start

From the repo root:

```bash
cd ag2

# sanity check without model calls
python3 run_team.py --dry-run

# full run (manager-driven, plain-text final response)
export OPENAI_API_KEY='<your_key>'
python3 run_team.py \
  --campaign ../output/campaign_20260217_205128 \
  --agents-md ../../AGENTS.md \
  --task "Build a compliant next-step testing and reporting plan." \
  --max-round 10 \
  --speaker-selection auto \
  --allow-exec \
  --out ./runs/campaign_20260217_205128.json
```

Use an external `.env` directly (for example Gemini/Vertex setup):

```bash
python3 run_team.py \
  --env-file /absolute/path/to/your/.env \
  --campaign ../output/campaign_20260217_205128 \
  --agents-md ../../AGENTS.md \
  --task "Build a compliant next-step testing and reporting plan." \
  --max-round 10 \
  --speaker-selection auto \
  --allow-exec \
  --out ./runs/campaign_20260217_205128_google_env.json
```

## Local Chat GUI

Run a local chat interface on `http://127.0.0.1:5050`:

```bash
cd ag2
python3 web_chat.py
```

From the GUI:

- set `Env file` to your setup (for example `/absolute/path/to/your/.env`);
- set campaign/AGENTS paths as needed;
- keep `speaker_selection=auto` for orchestrator routing;
- enable `Allow agents to run commands` if you want `ExecAgent`;
- write a prompt and click `Send to agents`.

Each send launches `run_team.py` asynchronously, shows `Run en cours...`, and streams concise process activity in `Live Activity`.
When needed, use `Stop run` to send `SIGTERM` to the current run process.
The GUI accepts env paths prefixed with `@` too (for example `@/path/to/.env`).

## Initialize AGENTS.md directory structure

```bash
python3 init_target_structure.py \
  --root ~/bugbounty \
  --program robinhood \
  --target robinhood.com
```

## Notes

- The team is explicitly instructed to enforce in-scope and safe-harbor constraints.
- Keep request rates conservative and use owned accounts only.
- Review agent outputs before acting on any test step.
