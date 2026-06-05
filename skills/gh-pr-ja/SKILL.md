---
name: gh-pr-ja
description: Draft or revise GitHub pull request titles and bodies in Japanese. Use when the user asks to create a PR, rewrite a PR body, add context from incidents or reviews, normalize multiple PRs to the same Japanese structure and tone, or add Japanese intent comments to PR diffs after opening the PR.
license: MIT
---

# Gh Pr Ja

## Overview

Use this skill when creating or editing GitHub PR titles and bodies in Japanese for engineering work. The default body structure is fixed so reviewers can scan the incident, the actual problem, the chosen approach, and the concrete changes without guessing.

## When To Use

- The user asks to create a PR or rewrite an existing PR body.
- The user asks to add context such as monitoring results, Cloud Logging links, review feedback, or latest incident timestamps to a PR.
- Multiple PRs need to be aligned to the same Japanese structure and tone.
- The user wants the `Files changed` diff to explain the intent of the change with Japanese comments after the PR is opened.

## Default Body Structure

Use these sections in this order unless the user explicitly asks for a different structure:

1. `背景`
2. `問題`
3. `対策の方針`
4. `やることの全体像`
5. `影響範囲`
6. `関連PR`
7. `実際にやったこと`
8. `今回の対象外`
9. `レビュー観点`
10. `スクリーンショット`
11. `実行したコマンド`
12. `結果`
13. `残リスク`
14. `ロールバック`

Keep every section visible by default. If a section has no applicable content, write `なし` or a short explicit reason such as `なし（UI変更なし）`. This keeps reviewer checklist items closed instead of forcing reviewers to infer that an omitted section was intentionally skipped.

## Writing Rules

- Write in Japanese plain form. Do not use polite endings such as `〜ました`, `〜です`, or `〜ます`.
- Keep bullets flat and short. One bullet should contain one point.
- When adding comments to PR diffs, write one short Japanese comment per logical hunk so a reviewer can understand why the change exists without re-reading the whole PR body.
- Diff comments should explain intent, guardrails, or why the implementation is safe. Do not restate the code literally.
- Add diff comments only to non-obvious or reviewer-relevant changes. Skip self-evident renames, formatting-only hunks, and trivial mechanical edits.
- In `背景`, explain the trigger for the PR. If the change came from monitoring or incident investigation, include the latest confirmed timestamp with timezone and a direct link such as Cloud Logging or the alert URL when available.
- In `問題`, describe the broken behavior, missing guardrail, or operational risk. Focus on what was wrong before the change.
- In `対策の方針`, explain the design choice and the guardrails being introduced. Separate benign cases from real errors when that distinction matters.
- In `やることの全体像`, summarize the end-to-end scope before implementation details. Use objective-level bullets such as "基盤を作る", "データを同期する", "権限を分ける", "検証する". Do not list individual files here.
- In `影響範囲`, describe affected screens, APIs, DB objects, jobs, Cloud Run services, deploy steps, permissions, or operations. Include important non-effects only when they prevent a likely misunderstanding.
- In `関連PR`, list only PRs that change review order, merge order, dependency context, rollout context, or follow-up scope. Include the PR number or URL, title if useful, and the relationship such as `先行`, `後続`, `依存`, `分割元`, or `補足`. Omit loosely related PRs that do not affect review.
- In `実際にやったこと`, group concrete code, query, config, or test changes by purpose using short `###` subheadings. Use names such as `API`, `DB`, `権限`, `CI`, `docs`, or domain-specific groups. Do not repeat rationale here.
- Under each `実際にやったこと` subgroup, keep bullets flat and concrete. Avoid one long ungrouped list when there are more than about six bullets or multiple objectives.
- In `今回の対象外`, list only nearby scope that a reviewer could reasonably mistake as included in this PR. Use it for intentional exclusions, follow-up PR scope, or rollout work handled elsewhere. Do not list arbitrary things that were not done.
- In `レビュー観点`, name specific design decisions, risky hunks, behavior changes, or spec points that need focused review. Write `なし` for straightforward changes.
- UI changes require screenshots in the PR description. Treat changes to user-visible screens, components, layout, styling, copy, icons, images, interaction states, or responsive behavior as UI changes; when unsure, treat the PR as a UI change.
- For UI changes, the `スクリーンショット` section must contain an actual pasted or attached image rendered by GitHub Markdown, such as `![label](https://github.com/user-attachments/assets/...)`. A local file path, placeholder, `なし`, `不要`, or text-only explanation does not satisfy this requirement.
- When local screenshot image files need to be attached, use the GitHub CLI `gh image` extension to upload them and paste the returned Markdown. Before using it, check `gh extension list`; if `gh image` is not installed, run `gh extension install drogers0/gh-image`. Upload with `gh image --repo <owner/repo> <image-path>...`.
- Do not open or update a UI-change PR until the screenshot is captured and can be pasted or attached. If screenshot capture is blocked by auth, environment, data, or tooling, stop and report the blocker instead of creating a PR without the image. Only skip this rule when the user explicitly says to omit screenshots for that PR.
- For non-UI changes, write `なし（UI変更なし）` in `スクリーンショット`.
- In `実行したコマンド`, list the exact verification commands and whether each succeeded.
- In `結果`, state the current state such as local checks passed, CI passed or pending, demo not deployed, prod unaffected, or rollout complete.
- In `残リスク`, list only remaining uncertainty, unverified behavior, operational monitoring points, or risk accepted by the PR. Write `なし` when there is no meaningful residual risk.
- In `ロールバック`, explain how to revert or stop the change for infra, DB, auth, billing, deploy, data migration, or other operationally risky changes. Mention whether a plain revert is enough or whether config, DB, or deploy steps are required. For low-risk changes, state the simple rollback path such as `通常のrevertで切り戻し可能`.

## Workflow

1. Sync the branch with the latest base branch before opening or updating the PR:
   identify the base branch, run `git fetch origin`, and rebase or merge the working branch onto the latest `origin/<base>` using the repository's standard flow. If conflicts appear, resolve them before drafting the PR body or running `gh pr create`. If the base branch advances again while the PR is open, repeat this step before finalizing the PR.
2. Gather the evidence needed to justify the PR:
   `git diff`, tests, CI results, review comments, incident logs, monitoring links, and latest occurrence timestamps.
   Inspect the diff for UI changes. If there are UI changes, capture the relevant before/after or after-change screenshots for the PR description without committing those image files.
   If screenshots are local files, install `gh image` if needed and use it to upload the files to GitHub user attachments.
   Confirm the screenshots are attached or pasted as GitHub-rendered images before proceeding.
3. Decide the title:
   keep it short, in Japanese, and consistent with the repository's commit or PR prefix conventions such as `fix:` or `feat:` when those conventions exist.
4. Draft the body using the default section order.
   For UI changes, include the `スクリーンショット` section with the actual image Markdown; never leave a placeholder to fill in later.
5. Open or update the PR only after the body satisfies the screenshot requirement for UI changes.
6. After the PR exists, inspect the `Files changed` tab and add Japanese comments to the important diff hunks:
   cover changes whose intent is not immediately obvious from the code, especially guard conditions, error handling, operational workarounds, schema changes, and behavior changes.
7. Remove fluff:
   do not narrate the work process; keep only reviewer-useful facts.
8. If the user asks to revise an existing PR:
   preserve the facts, but rewrite the structure and tone to match this skill.

## Diff Comment Rules

- Prefer comments on added lines or the nearest changed line in the hunk.
- Keep each comment to one to three short sentences.
- Mention the before/after behavioral difference when that helps, such as `旧実装では...` and `この変更で...`.
- If a hunk is already fully explained by the PR body and the code is obvious, do not add a redundant comment.
- If the repository or team has a stronger convention for self-comments on PRs, follow that convention.

## Example Skeleton

```md
## 背景
- Demo 環境のアラート調査で `...` が継続的に発生していた
- 最新確認: 2026年3月12日 09:40:55 JST（`...Z` / `revision-name`）
- Cloud Logging: [Log Explorer](https://console.cloud.google.com/logs/query;query=...)

## 問題
- ...

## 対策の方針
- ...

## やることの全体像
- ...

## 影響範囲
- ...

## 関連PR
- なし

## 実際にやったこと

### ...
- ...

## 今回の対象外
- なし

## レビュー観点
- なし

## スクリーンショット
- なし（UI変更なし）

## 実行したコマンド
- `...` : 成功

## 結果
- ...

## 残リスク
- なし

## ロールバック
- 通常のrevertで切り戻し可能
```

## Example Diff Comments

```md
- この分岐を追加して、空レスポンスを異常系として扱わずに早期 return するようにした
- ここで request id をログに残し、Cloud Logging 上で失敗ケースを同一キーで追跡できるようにした
- リトライ回数を設定値経由に寄せて、環境ごとの差分をコード変更なしで切り替えられるようにした
```
