# Contributing Skills

この repository は、複数の Agent Skills を `gh skill` で配布するための専用 repository として扱う。

## Skill Directory

skill は必ず `skills/<skill-name>/` に置く。

```text
skills/
  <skill-name>/
    SKILL.md
```

`SKILL.md` の frontmatter は最低限こうする。

```yaml
---
name: <skill-name>
description: Use this skill when ...
license: MIT
---
```

守ること:

- `name` は directory name と一致させる。
- `name` は lowercase letters, numbers, hyphens のみ。
- `description` は 1024 文字以内。
- `description` は agent が trigger 判断に使うので、"Use this skill when ..." の形で user intent を書く。
- 長い補足は `references/` に逃がす。
- 実行補助は `scripts/` に置く。
- template や static resource は `assets/` に置く。
- `gh skill install` 後に入る `metadata.github-*` は commit しない。

`gh skill create` のような作成コマンドはない。必要なら creator skill を別途入れる。

```sh
gh skill install anthropics/skills skill-creator --agent claude-code --scope user
```

## Trigger Evals

trigger eval は `skills/<skill-name>/evals/trigger-queries.json` に置く。

```json
[
  {
    "query": "Can you publish this new SKILL.md with gh skill after validating it?",
    "should_trigger": true
  },
  {
    "query": "Can you summarize this unrelated README?",
    "should_trigger": false
  }
]
```

設計方針:

- positive / negative を両方入れる。
- positive は言い回し、明示性、具体度をばらす。
- negative は単に無関係なものではなく、keyword が近い near-miss を入れる。
- release 前には 20 ケース前後を目安に増やす。

## Output Evals

品質 eval は `skills/<skill-name>/evals/evals.json` に置く。

```json
{
  "skill_name": "<skill-name>",
  "evals": [
    {
      "id": "basic-flow",
      "prompt": "Create a minimal valid Agent Skill and validate it.",
      "expected_output": "A valid skill directory, passing validation, and publish instructions.",
      "files": []
    }
  ]
}
```

最初は 2-3 ケースでよい。失敗パターンが見えたら増やす。

## Validate Locally

全部まとめて検証する。

```sh
# Python 3.11+
python3 -m pip install skills-ref
scripts/validate-skills.sh
```

CI と同じく、`skills-ref` validation、eval JSON の shape check、`gh skill publish --dry-run` を実行する。

`gh` の publish dry-run だけを飛ばす場合:

```sh
scripts/validate-skills.sh --skip-gh
```

install できるかだけを local directory から確認する場合:

```sh
rm -rf /tmp/agent-skills-install-test
gh skill install . <skill-name> --from-local --dir /tmp/agent-skills-install-test --force
```

## Publish

dry-run:

```sh
gh skill publish --dry-run
```

publish:

```sh
gh skill publish --tag v0.1.0
```

公開前チェック:

- `gh skill preview knao124/agent-skills <skill-name>` で中身を確認する。
- `v*` tag protection ruleset を有効化する。
- secret scanning / code scanning を有効化する。
- team 向け案内では `--pin <tag>` を推奨する。
