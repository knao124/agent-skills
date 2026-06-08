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
| `claude-worklog-summary` | Claude Code local transcript log から作業時間と会話圧縮メモを折りたたみMarkdownで出力する | Claude作業ログ、Agent作業ログ、会話圧縮メモ、PRコメント用の作業時間メモ、transcript log要約を頼まれたとき |
| `codex-consult` | Codex CLIを相談役として呼び、Codex同士で明示回数の設計相談・レビュー・反論を行う | Codex同士で相談、別Codexに聞く、2往復/3往復レビューなど、実装せずセカンドオピニオンを求めるとき |
| `codex-delegate` | 実装前にCodex同士で設計相談し、専用worktree上の実装役Codexへ作業委譲する | 実装役Codexに任せる、専用worktreeでCodexに実装させる、設計相談後に実装委譲するとき |
| `codex-worklog-summary` | Codex local rollout log から作業時間と会話圧縮メモを折りたたみMarkdownで出力する | Codex作業ログ、Agent作業ログ、会話圧縮メモ、PRコメント用の作業時間メモ、rollout log要約を頼まれたとき |
| `daily-report` | GitHub PR、Slack投稿、Googleカレンダー予定を統合してSlack投稿用の日報を作る | 日報作成、Slack/PR/Calendar統合、日付別コードブロック、Slack投稿用の箇条書き日報を頼まれたとき |
| `gh-pr-period-list` | `gh` で指定期間の自分のPRをopen/merge日時ベースで一覧化する | GitHub PRを指定期間で一覧化、merge日時を含める、open日時またはmerge日時で検索するよう頼まれたとき |
| `gh-pr-ja` | 日本語のPRタイトル・本文・diffコメントを作成、整理する | PR作成、PR本文の書き換え、レビューやインシデント文脈の追記、Files changed への日本語コメント追加を頼まれたとき |
| `git-worktree-start` | code change 前に clean な git worktree と `codex/` branch を用意する | 実装・修正・refactor・ドキュメント更新など、ファイル変更を伴う作業やそれをPR化する作業を始めるとき |
| `gws-calendar-agenda` | `gws` で指定期間の自分のGoogleカレンダー予定を取得し、日付・参加状態つきの表にまとめる | MCPなしでGoogleカレンダー予定を一覧化、参加状態つきで表にする、指定期間の予定をまとめるよう頼まれたとき |
| `explain-to-html` | 解説を `/tmp` 配下の standalone HTML として作成する | コード、diff、設定、コマンドの解説をブラウザで見られるHTMLとして保存・共有したいと頼まれたとき |
| `gcloud-repo-config` | repo ごとの `gcloud` named configuration を安全に初期設定、検証、利用する | repo 固有の `gcloud` named configuration、`.codex/gcloud.local.toml`、`CLOUDSDK_ACTIVE_CONFIG_NAME`、service account impersonation の設定や利用を頼まれたとき |
| `publish-to-public` | ローカルHTMLを `knao124/public` に配置し、index/README導線更新、push、公開URL検証まで行う | HTMLを公開して、これを公開して、publicに公開、GitHub Pagesに載せて、と頼まれたとき |
| `reading-note` | 本やPDFを理解導入、問いの連鎖、概念台帳、理解ゴール、検証メモで精読代替ノート化する | 精読ノート、読書ノート、論理復元、本/PDFを深く理解したい、登場概念や理解ゴール整理を頼まれたとき |
| `slack-daily-report` | `agent-slack` で指定 workspace の自分の投稿を取得し、日報用の raw table と日時サマリを作る | Slack投稿から日報、作業時間つきの表、Slack/git/calendar統合前のrawデータ作成を頼まれたとき |
| `teamspirit-monthly-attendance` | ローカル設定を使い、TeamSpirit/Salesforce の月次勤怠時刻修正と工数割合登録を console script で厳密に支援する | TeamSpirit 勤怠表、勤怠時刻修正申請、承認申請、工数割合、Chrome/Console 自動化を頼まれたとき |
| `tweet-explainer` | X/Tweet URLをブラウザ優先、`~/.x-token` のApp-only token fallbackで読み、`explain-to-html` で解説HTMLを作る | X投稿やX ArticleのURLを読んで、要約・解説・HTML記事化を頼まれたとき |
| `video-explainer` | 動画URLやローカル動画/音声を取得・文字起こしし、詳細な解説記事へ変換する | 動画を見て、音声を文字起こし、トランスクリプト抽出、動画を記事化して、と頼まれたとき |

## Install

まず中身を確認する。

```sh
gh skill preview knao124/agent-skills claude-worklog-summary
gh skill preview knao124/agent-skills codex-consult
gh skill preview knao124/agent-skills codex-delegate
gh skill preview knao124/agent-skills codex-worklog-summary
gh skill preview knao124/agent-skills daily-report
gh skill preview knao124/agent-skills gh-pr-period-list
gh skill preview knao124/agent-skills gh-pr-ja
gh skill preview knao124/agent-skills git-worktree-start
gh skill preview knao124/agent-skills gws-calendar-agenda
gh skill preview knao124/agent-skills explain-to-html
gh skill preview knao124/agent-skills gcloud-repo-config
gh skill preview knao124/agent-skills publish-to-public
gh skill preview knao124/agent-skills reading-note
gh skill preview knao124/agent-skills slack-daily-report
gh skill preview knao124/agent-skills teamspirit-monthly-attendance
gh skill preview knao124/agent-skills tweet-explainer
gh skill preview knao124/agent-skills video-explainer
```

Codex の user scope に入れる例:

```sh
gh skill install knao124/agent-skills codex-consult --agent codex --scope user
gh skill install knao124/agent-skills codex-delegate --agent codex --scope user
gh skill install knao124/agent-skills codex-worklog-summary --agent codex --scope user
gh skill install knao124/agent-skills daily-report --agent codex --scope user
gh skill install knao124/agent-skills gh-pr-period-list --agent codex --scope user
gh skill install knao124/agent-skills gh-pr-ja --agent codex --scope user
gh skill install knao124/agent-skills git-worktree-start --agent codex --scope user
gh skill install knao124/agent-skills gws-calendar-agenda --agent codex --scope user
gh skill install knao124/agent-skills explain-to-html --agent codex --scope user
gh skill install knao124/agent-skills gcloud-repo-config --agent codex --scope user
gh skill install knao124/agent-skills publish-to-public --agent codex --scope user
gh skill install knao124/agent-skills reading-note --agent codex --scope user
gh skill install knao124/agent-skills slack-daily-report --agent codex --scope user
gh skill install knao124/agent-skills teamspirit-monthly-attendance --agent codex --scope user
gh skill install knao124/agent-skills tweet-explainer --agent codex --scope user
gh skill install knao124/agent-skills video-explainer --agent codex --scope user
```

Claude Code で PR 作成 skill を使う例:

```sh
gh skill install knao124/agent-skills gh-pr-ja --agent claude-code --scope user
gh skill install knao124/agent-skills claude-worklog-summary --agent claude-code --scope user
gh skill install knao124/agent-skills git-worktree-start --agent claude-code --scope user
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
