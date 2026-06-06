# agent-skills

`knao124` の Agent Skills 配布用 repository。

この repository は [Agent Skills specification](https://agentskills.io/specification) に従い、`gh skill` で preview / install / publish できる形で skill を管理する。

## Layout

`gh skill` が自動発見できる標準レイアウトに寄せる。

```text
skills/
  <skill-name>/
    SKILL.md
    evals/
      trigger-queries.json
      evals.json
    references/
    scripts/
    assets/
```

必須なのは `skills/<skill-name>/SKILL.md`。`evals/` はこの repository の運用ルールとして置く。

## Skills

| Skill | 内容 | Trigger |
| --- | --- | --- |
| `codex-consult` | Codex CLIを相談役として呼び、Codex同士で明示回数の設計相談・レビュー・反論を行う | Codex同士で相談、別Codexに聞く、2往復/3往復レビューなど、実装せずセカンドオピニオンを求めるとき |
| `codex-delegate` | 実装前にCodex同士で設計相談し、専用worktree上の実装役Codexへ作業委譲する | 実装役Codexに任せる、専用worktreeでCodexに実装させる、設計相談後に実装委譲するとき |
| `gh-pr-ja` | 日本語のPRタイトル・本文・diffコメントを作成、整理する | PR作成、PR本文の書き換え、レビューやインシデント文脈の追記、Files changed への日本語コメント追加を頼まれたとき |
| `git-worktree-start` | code change 前に clean な git worktree と `codex/` branch を用意する | 実装・修正・refactor・ドキュメント更新など、ファイル変更を伴う作業やそれをPR化する作業を始めるとき |
| `explain-to-html` | 解説を `/tmp` 配下の standalone HTML として作成する | コード、diff、設定、コマンドの解説をブラウザで見られるHTMLとして保存・共有したいと頼まれたとき |
| `gcloud-repo-config` | repo ごとの `gcloud` named configuration を安全に初期設定、検証、利用する | repo 固有の `gcloud` named configuration、`.codex/gcloud.local.toml`、`CLOUDSDK_ACTIVE_CONFIG_NAME`、service account impersonation の設定や利用を頼まれたとき |
| `teamspirit-monthly-attendance` | ローカル設定を使い、TeamSpirit/Salesforce の月次勤怠時刻修正と工数割合登録を console script で厳密に支援する | TeamSpirit 勤怠表、勤怠時刻修正申請、承認申請、工数割合、Chrome/Console 自動化を頼まれたとき |
| `tweet-explainer` | X/Tweet URLをブラウザ優先、`~/.x-token` のApp-only token fallbackで読み、`explain-to-html` で解説HTMLを作る | X投稿やX ArticleのURLを読んで、要約・解説・HTML記事化を頼まれたとき |
| `video-explainer` | 動画URLやローカル動画/音声を取得・文字起こしし、詳細な解説記事へ変換する | 動画を見て、音声を文字起こし、トランスクリプト抽出、動画を記事化して、と頼まれたとき |

## Install

まず中身を確認する。

```sh
gh skill preview knao124/agent-skills codex-consult
gh skill preview knao124/agent-skills codex-delegate
gh skill preview knao124/agent-skills gh-pr-ja
gh skill preview knao124/agent-skills git-worktree-start
gh skill preview knao124/agent-skills explain-to-html
gh skill preview knao124/agent-skills gcloud-repo-config
gh skill preview knao124/agent-skills teamspirit-monthly-attendance
gh skill preview knao124/agent-skills tweet-explainer
gh skill preview knao124/agent-skills video-explainer
```

Codex の user scope に入れる例:

```sh
gh skill install knao124/agent-skills codex-consult --agent codex --scope user
gh skill install knao124/agent-skills codex-delegate --agent codex --scope user
gh skill install knao124/agent-skills gh-pr-ja --agent codex --scope user
gh skill install knao124/agent-skills git-worktree-start --agent codex --scope user
gh skill install knao124/agent-skills explain-to-html --agent codex --scope user
gh skill install knao124/agent-skills gcloud-repo-config --agent codex --scope user
gh skill install knao124/agent-skills teamspirit-monthly-attendance --agent codex --scope user
gh skill install knao124/agent-skills tweet-explainer --agent codex --scope user
gh skill install knao124/agent-skills video-explainer --agent codex --scope user
```

チーム配布時は release tag に pin する。

```sh
gh skill install knao124/agent-skills gh-pr-ja --pin v0.1.0 --agent codex --scope user
```

## Validate

ローカル検証:

```sh
# Python 3.11+
python3 -m pip install skills-ref
scripts/validate-skills.sh
```

`scripts/validate-skills.sh` は次を確認する。

- `skills-ref` による Agent Skills specification validation
- `evals/trigger-queries.json` と `evals/evals.json` の JSON shape
- `gh skill publish --dry-run` による `gh skill` discovery / publish validation

CI でも pull request と `main` push のたびに同じ検証を実行する。

## Publish

公開前に dry-run する。

```sh
gh skill publish --dry-run
```

release tag を作って公開する。

```sh
gh skill publish --tag v0.1.0
```

公開前に GitHub repository 側で次を有効化しておく。

- `v*` tag protection ruleset
- secret scanning
- code scanning
- release / tag の運用ルール

## Add Skills

新しい skill を追加するときは [CONTRIBUTING.md](CONTRIBUTING.md) を見る。
