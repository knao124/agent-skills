#!/usr/bin/env python3
"""Manage a repo-local selector for gcloud named configurations."""

from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - exercised on older Python via fallback parser.
    tomllib = None


CONFIG_RELATIVE_PATH = Path(".codex/gcloud.local.toml")
GITIGNORE_ENTRY = ".codex/gcloud.local.toml"
CONFIG_NAME_RE = re.compile(r"^[a-z][-a-z0-9]*$")


class ConfigError(RuntimeError):
    pass


def run_git(args: list[str], cwd: Path) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=str(cwd),
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return result.stdout.strip()


def repo_root(start: Path) -> Path:
    start = start.resolve()
    if start.is_file():
        start = start.parent

    git_root = run_git(["rev-parse", "--show-toplevel"], start)
    if git_root:
        return Path(git_root).resolve()

    for candidate in [start, *start.parents]:
        if (candidate / ".git").exists():
            return candidate
    return start


def config_path(repo: Path) -> Path:
    return repo / CONFIG_RELATIVE_PATH


def load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise ConfigError(f"Missing {path}")

    if tomllib is not None:
        with path.open("rb") as handle:
            raw = tomllib.load(handle)
    else:
        raw = parse_simple_toml(path.read_text(encoding="utf-8"))

    data = raw.get("gcloud", raw)
    if not isinstance(data, dict):
        raise ConfigError("Expected a [gcloud] table or flat TOML object.")
    return data


def parse_simple_toml(text: str) -> dict[str, Any]:
    """Parse the small TOML subset this script writes.

    This fallback keeps the helper usable on Python versions before 3.11 without
    adding third-party dependencies. It supports table headers and string values.
    """

    root: dict[str, Any] = {}
    current = root
    for line_number, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            table_name = line[1:-1].strip()
            if not table_name:
                raise ConfigError(f"Invalid TOML table at line {line_number}.")
            table: dict[str, Any] = {}
            root[table_name] = table
            current = table
            continue
        if "=" not in line:
            raise ConfigError(f"Invalid TOML assignment at line {line_number}.")
        key, raw_value = line.split("=", 1)
        key = key.strip()
        raw_value = raw_value.strip()
        if not key:
            raise ConfigError(f"Invalid TOML key at line {line_number}.")
        if len(raw_value) >= 2 and raw_value[0] == '"' and raw_value[-1] == '"':
            value = bytes(raw_value[1:-1], "utf-8").decode("unicode_escape")
        else:
            value = raw_value
        current[key] = value
    return root


def normalized_config(data: dict[str, Any]) -> dict[str, str]:
    aliases = {
        "configuration": ["configuration", "config", "name"],
        "expected_project": ["expected_project", "project", "project_id"],
        "account": ["account", "user", "user_account"],
        "impersonate_service_account": [
            "impersonate_service_account",
            "service_account",
            "impersonation_service_account",
        ],
        "region": ["region"],
        "zone": ["zone"],
    }

    result: dict[str, str] = {}
    for canonical, names in aliases.items():
        for name in names:
            value = data.get(name)
            if value is None:
                continue
            if not isinstance(value, str):
                raise ConfigError(f"{name} must be a string.")
            value = value.strip()
            if value:
                result[canonical] = value
            break
    return result


def validate_config(data: dict[str, str]) -> None:
    name = data.get("configuration")
    if not name:
        raise ConfigError("Missing required gcloud.configuration.")
    if not CONFIG_NAME_RE.fullmatch(name):
        raise ConfigError(
            "gcloud.configuration must match ^[a-z][-a-z0-9]*$ "
            f"(got {name!r})."
        )


def write_config(path: Path, values: dict[str, str]) -> None:
    validate_config(values)
    path.parent.mkdir(parents=True, exist_ok=True)

    ordered_keys = [
        "configuration",
        "expected_project",
        "account",
        "impersonate_service_account",
        "region",
        "zone",
    ]

    lines = ["[gcloud]"]
    for key in ordered_keys:
        value = values.get(key)
        if value:
            escaped = value.replace("\\", "\\\\").replace('"', '\\"')
            lines.append(f'{key} = "{escaped}"')

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def ensure_gitignore(repo: Path) -> bool:
    gitignore = repo / ".gitignore"
    if gitignore.exists():
        lines = gitignore.read_text(encoding="utf-8").splitlines()
    else:
        lines = []

    normalized = {line.strip() for line in lines if line.strip() and not line.strip().startswith("#")}
    if GITIGNORE_ENTRY in normalized:
        return False

    with gitignore.open("a", encoding="utf-8") as handle:
        if lines and lines[-1] != "":
            handle.write("\n")
        handle.write(f"{GITIGNORE_ENTRY}\n")
    return True


def current_config(repo: Path) -> tuple[Path, dict[str, str]]:
    path = config_path(repo)
    data = normalized_config(load_config(path))
    validate_config(data)
    return path, data


def cmd_path(args: argparse.Namespace) -> int:
    repo = repo_root(Path(args.repo))
    print(config_path(repo))
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    repo = repo_root(Path(args.repo))
    path, data = current_config(repo)
    payload = {"repo": str(repo), "path": str(path), "gcloud": data}
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"repo: {repo}")
        print(f"path: {path}")
        for key, value in data.items():
            print(f"{key}: {value}")
    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    repo = repo_root(Path(args.repo))
    path, data = current_config(repo)
    if args.require_project and "expected_project" not in data:
        raise ConfigError("Missing expected_project.")
    if args.require_account and "account" not in data:
        raise ConfigError("Missing account.")
    print(f"OK: {path}")
    return 0


def cmd_env(args: argparse.Namespace) -> int:
    repo = repo_root(Path(args.repo))
    _, data = current_config(repo)
    name = data["configuration"]
    if args.plain:
        print(name)
    else:
        print(f"export CLOUDSDK_ACTIVE_CONFIG_NAME={shlex.quote(name)}")
    return 0


def cmd_write(args: argparse.Namespace) -> int:
    repo = repo_root(Path(args.repo))
    path = config_path(repo)
    values = {
        "configuration": args.configuration,
        "expected_project": args.project or "",
        "account": args.account or "",
        "impersonate_service_account": args.impersonate_service_account or "",
        "region": args.region or "",
        "zone": args.zone or "",
    }
    values = {key: value for key, value in values.items() if value}

    if path.exists() and not args.force:
        existing = normalized_config(load_config(path))
        if existing != values:
            raise ConfigError(f"{path} already exists. Use --force to overwrite it.")

    write_config(path, values)
    print(path)
    return 0


def cmd_ensure_gitignore(args: argparse.Namespace) -> int:
    repo = repo_root(Path(args.repo))
    changed = ensure_gitignore(repo)
    status = "updated" if changed else "already-present"
    print(f"{status}: {repo / '.gitignore'}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_repo_arg(command_parser: argparse.ArgumentParser) -> None:
        command_parser.add_argument("--repo", default=".", help="Path inside the target repository.")

    path_parser = subparsers.add_parser("path", help="Print the repo-local selector path.")
    add_repo_arg(path_parser)
    path_parser.set_defaults(func=cmd_path)

    show_parser = subparsers.add_parser("show", help="Read and print the repo-local selector.")
    add_repo_arg(show_parser)
    show_parser.add_argument("--json", action="store_true", help="Print JSON.")
    show_parser.set_defaults(func=cmd_show)

    validate_parser = subparsers.add_parser("validate", help="Validate the selector shape.")
    add_repo_arg(validate_parser)
    validate_parser.add_argument("--require-project", action="store_true")
    validate_parser.add_argument("--require-account", action="store_true")
    validate_parser.set_defaults(func=cmd_validate)

    env_parser = subparsers.add_parser("env", help="Print an export for CLOUDSDK_ACTIVE_CONFIG_NAME.")
    add_repo_arg(env_parser)
    env_parser.add_argument("--plain", action="store_true", help="Print only the configuration name.")
    env_parser.set_defaults(func=cmd_env)

    write_parser = subparsers.add_parser("write", help="Write the repo-local selector.")
    add_repo_arg(write_parser)
    write_parser.add_argument("--configuration", required=True)
    write_parser.add_argument("--project")
    write_parser.add_argument("--account")
    write_parser.add_argument("--impersonate-service-account")
    write_parser.add_argument("--region")
    write_parser.add_argument("--zone")
    write_parser.add_argument("--force", action="store_true", help="Overwrite an existing selector.")
    write_parser.set_defaults(func=cmd_write)

    gitignore_parser = subparsers.add_parser(
        "ensure-gitignore",
        help="Ensure .codex/gcloud.local.toml is ignored by git.",
    )
    add_repo_arg(gitignore_parser)
    gitignore_parser.set_defaults(func=cmd_ensure_gitignore)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except ConfigError as error:
        print(f"error: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
