---
name: infisical-secret-intake
description: Store one new API key or other secret in an Infisical project when a person has the value and wants it saved without exposing it to the agent, chat, shell history, or process arguments. Use for attended "add this key to Infisical" requests. Do not use for reading or exporting secrets, rotating machine identities, or bulk migration.
---

# Infisical secret intake

The person pastes the value into a hidden prompt in their own terminal. The
agent prepares everything else and never sees, echoes, or stores the value.

## Gather the target first

Resolve these before opening the prompt. Each comes from local, private
configuration or a read-only listing, never from tracked repository text:

- **Domain**: the Infisical instance API URL (ends in `/api`).
- **Project ID**: confirm it against the projects the signed-in person can
  see. A project ID copied from an old env file or handoff may be stale; a
  stale ID fails with "Project ... not found".
- **Environment** and **folder path**: follow the owner's existing layout.
  List folder names (metadata only) and place the secret beside its peers.
- **Name**: UPPER_SNAKE_CASE that names the provider and kind, such as
  `EXAMPLE_API_KEY`. Check the name does not already exist.

State the target in one line (`NAME` in project, env, path) before opening
the prompt.

## Sign-in

Use the person's own attended Infisical login. If the session expired, the
script tells them to run `infisical login --domain <domain>`. Do not fall back
to a stored machine identity to get past a sign-in step; an unattended writer
credential that returns "Invalid credentials" needs rotation by its owner,
which is outside this skill.

## Run the intake

Open a terminal the person can type into and run:

```bash
python3 scripts/store_secret.py --name NAME --project-id ID --env ENV --path /FOLDER --domain https://HOST/api
```

The script:

1. checks the sign-in;
2. refuses to replace an existing value unless `--overwrite` is passed;
3. reads the value from a hidden prompt;
4. writes it through a mode-600 temporary file that is always deleted;
5. reads the stored value back, compares it in memory, and prints only
   `verified` or an error with the value redacted.

Read the terminal output, not the value. Report `verified` with the name and
location, or the exact error and the next step. Pass `--overwrite` only when
the person asked to replace the existing value.

## Boundaries

- Never ask the person to paste the value into chat, a file, or a command.
- Never print, log, or echo the value, and never run `secrets get` yourself;
  the script's in-memory read-back is the only read.
- Never write project IDs, hostnames, or secret values into tracked files.
- Storing a key grants no authority to use it; the consuming tool's own
  binding and scope still apply.
