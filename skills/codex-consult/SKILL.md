---
name: codex-consult
description: Use this skill when the user wants Codex-to-Codex consultation through Codex CLI, such as "Codex同士で相談して", "別Codexに聞いて", "2往復レビューして", or "実装前に3往復検討して". It runs an explicit number of design/review/critique rounds, then reports an integrated judgment instead of raw worker output. Use codex-delegate instead when another Codex should edit files or implement changes.
license: MIT
---

# Codex Consult

## 概要

指示役Codexが、相談役Codex CLIに明示X往復でセカンドオピニオンを求める。相談役の生出力をそのまま返さず、指示役が検証し、同意・反論・補完・採用判断を統合して報告する。

## 基本ルール

- 1往復 = 相談役Codexを `codex exec` で1回呼び、指示役Codexが出力を読んで次の論点を組み立てること。
- ユーザーが往復数を指定している場合は厳密にその回数を実行する。
- 往復数が未指定ならユーザーに確認する。対話できない場合だけ `2往復` をデフォルトにする。
- 最大3往復まで実行する。4往復以上を求められたら、実行前に確認する。
- 相談役Codexに実装やファイル編集をさせない。編集委譲が必要なら `codex-delegate` に切り替える。
- 指定観点は出発点であり制約ではない、と必ず相談役に伝える。
- 相談役の回答を鵜呑みにしない。誤読、探索不足、コマンド失敗、過剰設計を必ず疑う。

## 実行手順

1. `command -v codex` で Codex CLI の存在を確認する。見つからなければ、Codex CLI が未インストールであることを報告して終了する。
2. 相談対象を整理する。
   - 背景、目的、制約、評価観点を短くまとめる。
   - 指示役Codexの仮説を作る。初回プロンプトには必ず含める。
   - repo がある場合は `pwd`、`git status --short --branch`、必要な `AGENTS.md` などを確認し、重要なルールを要約する。
   - git repo 外で相談する場合は、`codex exec` に `--skip-git-repo-check` を付ける。
3. 各往復のプロンプトを一時ファイルに書き出し、`codex exec` に標準入力で渡す。
4. 各往復後、相談役の回答を要約し、次の往復に入れる。
5. 指定回数が終わったら統合レポートを返す。

## codex exec の呼び出し

長いプロンプトの shell quoting 問題を避けるため、prompt file 経由で実行する。

```sh
tmpdir="$(mktemp -d)"
prompt="$tmpdir/codex-consult-prompt.md"
out="$tmpdir/codex-consult-output.md"
# prompt に依頼文を書く
codex exec --ephemeral --cd "$PWD" -s read-only -o "$out" - < "$prompt"
```

git repo 外で実行する場合だけ、同じコマンドに `--skip-git-repo-check` を追加する。

相談に GitHub、外部ドキュメント、ネットワーク取得が不可欠で、read-only sandbox で失敗した場合のみ、明示的に編集禁止をプロンプトへ入れたうえで再実行する。

```sh
codex exec --ephemeral --cd "$PWD" -s workspace-write \
  -c sandbox_workspace_write.network_access=true \
  -o "$out" - < "$prompt"
```

## 初回プロンプトの構成

```md
あなたは相談役Codexです。実装やファイル編集は行わず、設計・レビュー・反論に徹してください。

背景:
- ...

相談したいこと:
- ...

制約・既存ルール:
- ...

指示役Codexの仮説:
- ...

依頼:
- 指定観点は出発点であり制約ではありません。
- repo や文脈を自分で探索し、前提の誤り、漏れ抜け、代替案、運用リスクを積極的に指摘してください。
- 指示役Codexの仮説に反論できる点があれば明示してください。
- 実装やファイル編集はしないでください。
```

## 2往復目以降のプロンプト

`codex exec` はステートレスなので、前回の記憶がない前提で全文脈を再投入する。

```md
あなたは相談役Codexです。これは X 往復中の N 往復目です。

元の背景・目的・制約:
- ...

指示役Codexの初期仮説:
- ...

前回までの相談役Codexの主張:
- ...

指示役Codexの検証・反論・補完:
- ...

今回さらに掘る観点:
- ...

依頼:
- 前回回答の自己追認ではなく、前提を疑ってください。
- まだ探索されていない領域、過剰/不足な設計、壊れやすい運用を探してください。
- 実装やファイル編集はしないでください。
```

## 失敗検知と補正

相談役の出力に以下があれば、指示役Codexが自分で確認して補正する。

- `permission denied`、`not found`、`failed`、`取得できなかった`
- `gh`、`git`、`curl`、テスト、依存取得、ファイル参照の失敗
- repo を十分に探索していない推測ベースの断定

補正後の最終報告では、欠落情報、影響を受けた指摘、再評価結果を明示する。

## 最終報告

以下の構成で簡潔に報告する。

- 相談内容: 相談役Codexに何を何往復聞いたか。
- 往復ごとの主要論点: 各往復で新しく分かったこと。
- 指示役Codexの見解: 同意、反論、補完、見落とし。
- 採用方針: どの案を採るべきか、何を避けるべきか。
- 次のアクション: 実装、追加調査、ユーザー確認のいずれが必要か。

相談役の長い生ログは貼らない。必要な場合だけ短く引用し、基本は指示役Codexの言葉で要約する。
