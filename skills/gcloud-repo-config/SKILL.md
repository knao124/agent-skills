---
name: gcloud-repo-config
description: Use this skill when Codex needs to set up, discover, validate, or use a repository-local Google Cloud CLI named configuration for gcloud commands. Trigger on repo-specific gcloud login, reauthentication, config switching, `.codex/gcloud.local.toml`, `CLOUDSDK_ACTIVE_CONFIG_NAME`, service account impersonation, or AI agent access to Google Cloud from a repo.
license: MIT
---

# Gcloud Repo Config

## Overview

Use this skill to make `gcloud` usage repo-aware without changing the user's global active configuration. The skill stores only a repo-local selector at `.codex/gcloud.local.toml`; the real `gcloud` properties and credentials stay in the user's normal Google Cloud SDK configuration.

## Core Rules

- Treat `.codex/gcloud.local.toml` as an agent/wrapper file, not a native `gcloud` file. `gcloud` will not read it by itself.
- Do not store tokens, service account keys, refresh tokens, or other secrets in the repo-local file.
- Ensure `.codex/gcloud.local.toml` is gitignored before writing it.
- Prefer `CLOUDSDK_ACTIVE_CONFIG_NAME=<name> gcloud ...` or `gcloud --configuration=<name> ...` for every command.
- Do not run `gcloud config configurations activate` unless the user explicitly asks to change global active config.
- Ask the user before running browser-based login, creating a named configuration, or changing `gcloud config` properties.
- Scope this workflow to the `gcloud` CLI. If app code uses ADC, call out that ADC is separate and ask whether ADC setup is also desired.

## Helper Script

Use `scripts/gcloud_repo_config.py` for deterministic repo-local file handling:

```sh
python3 <skill-dir>/scripts/gcloud_repo_config.py show --repo .
python3 <skill-dir>/scripts/gcloud_repo_config.py write --repo . \
  --configuration my-repo-prod \
  --project my-prod-project \
  --account you@example.com \
  --impersonate-service-account ai-agent@my-prod-project.iam.gserviceaccount.com
python3 <skill-dir>/scripts/gcloud_repo_config.py env --repo .
python3 <skill-dir>/scripts/gcloud_repo_config.py ensure-gitignore --repo .
```

## Workflow

### 1. Discover the repo-local selector

1. Find the repository root.
2. Run `show --repo <repo-root>`.
3. If `.codex/gcloud.local.toml` exists, validate the named configuration before using it.
4. If the file does not exist, start Initial Setup.

Expected file shape:

```toml
[gcloud]
configuration = "my-repo-prod"
expected_project = "my-prod-project"
account = "you@example.com"
impersonate_service_account = "ai-agent@my-prod-project.iam.gserviceaccount.com"
region = "asia-northeast1"
zone = "asia-northeast1-a"
```

Only `configuration` is required. `expected_project`, `account`, `impersonate_service_account`, `region`, and `zone` are validation/default hints.

### 2. Validate before running `gcloud`

For an existing selector, run:

```sh
python3 <skill-dir>/scripts/gcloud_repo_config.py validate --repo .
CLOUDSDK_ACTIVE_CONFIG_NAME=<configuration> gcloud config configurations describe <configuration>
CLOUDSDK_ACTIVE_CONFIG_NAME=<configuration> gcloud config list
```

If `expected_project` is present, compare it with `core/project`. If `account` is present, compare it with `core/account` or `gcloud auth list`. If `impersonate_service_account` is present, compare it with `auth/impersonate_service_account`.

### 3. Run gcloud with the selected config

Use one of these forms:

```sh
CLOUDSDK_ACTIVE_CONFIG_NAME=<configuration> gcloud <command>
gcloud --configuration=<configuration> <command>
```

Prefer the environment variable form when a multi-command workflow uses the same configuration.

## Reauthentication

When running a `gcloud` command unattended, set `CLOUDSDK_CORE_DISABLE_PROMPTS=1` for that command so it reports when interactive reauthentication is required instead of hanging on a password prompt.

If Google Cloud CLI user credentials need reauthentication (e.g., `Reauthentication required`), **do not** ask the user to open a terminal, **do not** use `localhost` browser-callback login (it fails on iPhone/mobile and remote clients), and **do not** put the login URL only inside a secret-request card/button (mobile clients cannot click it cleanly and it can time out).

Always use this exact 1-roundtrip clickable-link flow on the first try:

1. Start the named-configuration authorization-code login as a **background task** waiting on stdin (keeping the process alive):

```sh
CLOUDSDK_ACTIVE_CONFIG_NAME=<configuration> gcloud auth login <account> --no-launch-browser
```

(Pass `--force` only if `gcloud` skips login while reusing a stale session. `--no-launch-browser` redirects to Google's public `https://sdk.cloud.google.com/authcode.html`, so it works from iPhone, iPad, and desktop browsers.)

2. Extract the exact `https://accounts.google.com/o/oauth2/auth?...` URL from the background task output.
3. Reply directly in the chat message with a **clickable Markdown link** (not a code block, not a secret card), e.g.:

```markdown
[Google Cloud にログインする](https://accounts.google.com/o/oauth2/auth?...)
```

Ask the user to tap the link, sign in as `<account>`, and reply with the displayed verification code.
4. As soon as the user replies with the code, immediately send `<code + newline>` to the running background `gcloud` task's stdin, wait for it to exit `0`, and resume the original `gcloud` command. Never commit or save the verification code into files or repository logs.

See the [Google Cloud CLI login reference](https://docs.cloud.google.com/sdk/gcloud/reference/auth/login) for the authorization-code flow.

## Initial Setup

When `.codex/gcloud.local.toml` is missing or points to a nonexistent configuration, ask the user concise questions before changing anything:

1. Which Google Cloud project ID should this repo use?
2. Which Google account should `gcloud auth login` use?
3. What named configuration should be used? Propose a lowercase hyphenated name based on repo and project.
4. Should `gcloud` commands impersonate an agent/service account? If yes, ask for the service account email.
5. Are default region or zone needed for this repo?
6. Will repo code use ADC, or is this only for `gcloud` CLI commands?

After the user answers, run the setup with the chosen values:

```sh
# Skip this create command if the user chose an existing configuration.
gcloud config configurations create <configuration> --no-activate

CLOUDSDK_ACTIVE_CONFIG_NAME=<configuration> gcloud auth login <account> --no-launch-browser
CLOUDSDK_ACTIVE_CONFIG_NAME=<configuration> gcloud config set account <account>
CLOUDSDK_ACTIVE_CONFIG_NAME=<configuration> gcloud config set project <project-id>

# Optional defaults
CLOUDSDK_ACTIVE_CONFIG_NAME=<configuration> gcloud config set compute/region <region>
CLOUDSDK_ACTIVE_CONFIG_NAME=<configuration> gcloud config set compute/zone <zone>

# Optional agent identity
CLOUDSDK_ACTIVE_CONFIG_NAME=<configuration> \
  gcloud config set auth/impersonate_service_account <service-account-email>
```

Then write the repo-local selector:

```sh
python3 <skill-dir>/scripts/gcloud_repo_config.py ensure-gitignore --repo .
python3 <skill-dir>/scripts/gcloud_repo_config.py write --repo . \
  --configuration <configuration> \
  --project <project-id> \
  --account <account> \
  --impersonate-service-account <service-account-email> \
  --region <region> \
  --zone <zone>
```

Omit optional flags when the user did not provide those values.

If initial login prompts for an authorization code, use the same terminal input procedure as in Reauthentication.

## ADC Handling

Explain this distinction when relevant:

- `gcloud auth login` configures credentials for the `gcloud` CLI.
- `gcloud auth application-default login` configures ADC for client libraries and ADC-aware tools.
- Switching `CLOUDSDK_ACTIVE_CONFIG_NAME` does not automatically make app code use a different ADC file.

If the user wants ADC setup too, ask separately and prefer explicit choices:

```sh
gcloud auth application-default login
gcloud auth application-default login \
  --impersonate-service-account=<service-account-email>
```

Do not overwrite ADC with `--update-adc` unless the user explicitly confirms that behavior.

## Failure Handling

- If `gcloud` is missing, tell the user to install Google Cloud SDK before setup.
- If `gcloud` reports that user credentials need reauthentication, follow Reauthentication before retrying.
- If impersonation fails, check that the login account has `roles/iam.serviceAccountTokenCreator` on the target service account.
- If the selected configuration has a different project/account than the repo-local file, stop and ask before changing config properties.
- If `.codex/gcloud.local.toml` is tracked by git, stop and ask whether to remove it from tracking before proceeding.
