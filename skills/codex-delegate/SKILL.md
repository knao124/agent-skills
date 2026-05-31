---
name: codex-delegate
description: Use this skill when the user wants a director Codex to delegate implementation to a worker Codex CLI, such as "実装役Codexに任せて", "専用worktreeでCodexに実装させて", or "2往復設計相談してから実装して". It performs explicit pre-implementation consultation rounds, creates a dedicated worktree/branch, delegates edits there, then reviews the diff and tests. Use codex-consult instead for consultation without file edits.
license: MIT
---

# Codex Delegate

## 概要

指示役Codexが、実装前に実装役Codexと明示X往復で設計相談し、その後に専用 worktree 上で実装を委譲する。指示役Codexは原則としてコードを直接編集せず、依頼設計、差分レビュー、統合報告に徹する。

## 基本ルール

- 1往復 = 実装役Codexを `codex exec` で1回呼び、設計・懸念・代替案を返させること。
- X往復は実装前の設計相談に適用する。X往復完了後にだけ実装へ進む。
- ユーザーが往復数を指定している場合は厳密にその回数を実行する。
- 往復数が未指定ならユーザーに確認する。対話できない場合だけ `2往復` をデフォルトにする。
- 最大3往復まで実行する。4往復以上を求められたら、実行前に確認する。
- 実装役Codexは専用 worktree/branch でのみ編集する。現在の worktree は直接編集しない。
- 指示役Codexは実装役の出力を鵜呑みにしない。diff、テスト結果、失敗ログを自分で確認してから報告する。

## 実行手順

1. `command -v codex` で Codex CLI の存在を確認する。見つからなければ、Codex CLI が未インストールであることを報告して終了する。
2. repo root を確認する。
   - `git rev-parse --show-toplevel`
   - repo でなければ、この skill ではなく通常作業として扱うか、ユーザーに repo を確認する。
3. 現在の repo ルールを確認する。
   - root から対象ディレクトリまでの `AGENTS.md`、`CLAUDE.md`、既存 skill 指示を読む。
   - 実装役プロンプトにも重要ルールを要約して含める。
4. base branch を決める。
   - ユーザー指定があればそれを使う。
   - それ以外は upstream branch、`origin/main`、`origin/master` の順に選ぶ。
5. `git fetch origin` を実行し、専用 worktree を作る。
6. 実装役CodexとX往復の設計相談を行う。
7. 指示役Codexが作業依頼書を確定する。
8. 専用 worktree 上で実装役Codexに実装を委譲する。
9. 指示役Codexが差分とテスト結果を確認し、統合レポートを返す。

## 専用 worktree の作成

現在の worktree が dirty でも直接編集しない。worker 用 branch は `codex/` プレフィックスを付ける。

```sh
repo_root="$(git rev-parse --show-toplevel)"
repo_name="$(basename "$repo_root")"
slug="codex-delegate-$(date +%Y%m%d-%H%M%S)"
base="origin/main" # 実際にはユーザー指定、upstream、origin/main、origin/master の順で決める
worktree="$(dirname "$repo_root")/${repo_name}-${slug}"
branch="codex/${slug}"

git -C "$repo_root" fetch origin
git -C "$repo_root" worktree add -b "$branch" "$worktree" "$base"
```

既存の branch/path と衝突したら、末尾に短い suffix を付けて再試行する。`git reset --hard`、`git checkout --` など破壊的コマンドは使わない。

## 設計相談の codex exec

設計相談では、実装役に編集させない。prompt file 経由で実行する。

```sh
tmpdir="$(mktemp -d)"
prompt="$tmpdir/codex-delegate-design-prompt.md"
out="$tmpdir/codex-delegate-design-output.md"
# prompt に設計相談を書く
codex exec --ephemeral --cd "$worktree" -s read-only -o "$out" - < "$prompt"
```

2往復目以降はステートレス前提で、元の背景、前回までの要約、指示役Codexの反論、未解決論点をすべて再投入する。

## 設計相談プロンプト

```md
あなたは実装役Codexですが、この往復では実装やファイル編集をしないでください。

背景:
- ...

実装したいこと:
- ...

repo ルール:
- ...

指示役Codexの仮説:
- ...

依頼:
- 指定観点は出発点であり制約ではありません。
- repo を探索し、実装方針、影響範囲、テスト、リスク、代替案を提案してください。
- 指示役Codexの仮説に反論できる点を明示してください。
- まだ実装やファイル編集はしないでください。
```

## 作業依頼書の確定

X往復後、指示役Codexが実装役に渡す作業依頼書を作る。必ず以下を含める。

- 背景と目的
- 採用する実装方針
- やること、やらないこと
- 影響範囲と守るべき repo ルール
- 受け入れ条件
- 実行すべきテスト/確認
- 失敗時に報告すべき情報
- 最終報告フォーマット

## 実装委譲の codex exec

実装フェーズでは workspace-write を使う。実装役は専用 worktree の中だけで作業する。

```sh
impl_prompt="$tmpdir/codex-delegate-implementation-prompt.md"
impl_out="$tmpdir/codex-delegate-implementation-output.md"
# impl_prompt に作業依頼書を書く
codex exec --ephemeral --cd "$worktree" -s workspace-write -o "$impl_out" - < "$impl_prompt"
```

ネットワークが必要なタスクでは、必要性を確認したうえで以下を使う。

```sh
codex exec --ephemeral --cd "$worktree" -s workspace-write \
  -c sandbox_workspace_write.network_access=true \
  -o "$impl_out" - < "$impl_prompt"
```

## 実装後レビュー

指示役Codexが自分で確認する。

```sh
git -C "$worktree" status --short --branch
git -C "$worktree" diff --stat
git -C "$worktree" diff
```

実装役が報告したテストは、可能なら指示役Codexも同じ worktree で再実行する。テストが未実行、失敗、環境不足の場合は、その理由とリスクを報告する。

## 失敗検知と補正

実装役の出力に以下があれば、指示役Codexが補正する。

- `permission denied`、`not found`、`failed`、`取得できなかった`
- `gh`、`git`、テスト、依存取得、ファイル参照の失敗
- 指定 worktree 外の編集
- repo ルール違反、未検証の断定、不要な大規模改修

必要なら追加修正を実装役Codexへ1回だけ依頼できる。ただしこれはユーザー指定の設計X往復には数えない。大きな方針変更や追加の複数回修正が必要ならユーザーに確認する。

## 最終報告

以下の構成で簡潔に報告する。

- 依頼内容: 実装役Codexに何を何往復相談し、何を実装させたか。
- 設計相談の要点: 各往復の主要論点と採用/不採用。
- 指示役Codexの見解: 同意、反論、補完、残リスク。
- 差分概要: 主要な変更点と触った領域。
- 検証結果: 実行したテスト、失敗、未実行理由。
- 次のアクション: 追加修正、レビュー、コミット/PR の必要性。

実装役の長い生ログは貼らない。ユーザーが判断できる粒度に統合する。
