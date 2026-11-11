# ローカル設定と操作例

ローカル設定の形式と、Computer Useで対象を扱えない場合のCLI手順。画面操作が使えるときは[computer-use.md](computer-use.md)を優先する。

## ローカル設定

`~/.config/daily-task-plan/config.json`に保存する。以下は形式の例で、URL・ID・メールアドレスは実際の設定で置き換える。実値をこのファイルへ書き戻さない。

```json
{
  "repository": "example-owner/tasks",
  "project_owner": "example-owner",
  "project_number": 1,
  "timezone": "Asia/Tokyo",
  "google_account": "user@example.com",
  "document_url": "",
  "tab_id": "",
  "tab_name": "日報",
  "calendars": [
    {"id": "calendar@example.com", "company": ""}
  ]
}
```

URLから`/d/`直後の文書IDと、`tab=`のタブIDを取り出す。タブIDがなければ文書を取得して「日報」を探す。接続ツールでは、IDを使う前にそのアカウントから対象へアクセスできることを確認する。

`calendars`には対象カレンダーを必要な数だけ登録する。`company`にはGitHubの会社フィールドから取得した値を使う。会社名や区分の数を設定例から推測しない。

一つのGoogleアカウントから対象カレンダーを取得できれば、アカウントを切り替える必要はない。`gws auth status`とカレンダー一覧を読み、設定したIDへアクセスできるかを確認する。未回答の予定も必要なので、既存の実績日報skillの「参加・主催者だけ」という絞り込みは流用しない。

別のgws設定が必要な環境では、ローカル設定に任意の`gws_config_dir`を記録し、コマンドごとに`GOOGLE_WORKSPACE_CLI_CONFIG_DIR`を指定する。未検証の`--account`を付けたり、既存アカウントをログアウトしたりしない。利用版の`gws --help`と`gws auth --help`を確認する。

## 取得用コマンド

一時ファイルはリポジトリ外に作る。以下の変数は同じシェル内で使う。`DAILY_SKILL_DIR`は、読み込んだこのskillの絶対パスとする。

```sh
DAILY_CONFIG="$HOME/.config/daily-task-plan/config.json"
DAILY_TMP="$(mktemp -d "${TMPDIR:-/tmp}/daily-task-plan.XXXXXX")"
chmod 700 "$DAILY_TMP"
DAILY_OWNER="$(jq -r '.project_owner' "$DAILY_CONFIG")"
DAILY_PROJECT="$(jq -r '.project_number' "$DAILY_CONFIG")"
DAILY_REPO="$(jq -r '.repository' "$DAILY_CONFIG")"

gh api graphql --paginate --slurp \
  -F query=@"$DAILY_SKILL_DIR/references/project-items.graphql" \
  -f owner="$DAILY_OWNER" -F projectNumber="$DAILY_PROJECT" \
  > "$DAILY_TMP/project.json"
```

各ページの`.data.user.projectV2.items.nodes`をまとめ、`fieldValues.nodes[].field.name`で値を読む。`content`がIssueでないものと`isArchived`の項目は通常の候補から除く。子IssueやfieldValuesにも`hasNextPage`があれば、その接続を追加取得する。本文に「待ち」「最短受領日」「次にやること」があれば、期限と合わせて読む。

`gh project item-list`は日本語カスタムフィールドのキーが崩れる版がある。取得できない値を「未設定」と決めつけず、同梱クエリで確認する。

対象日の開始と翌日の開始をISO 8601で指定する。各カレンダーについて以下を実行する。

```sh
gws calendar calendarList list --params '{"maxResults":250}'

gws calendar events list --params "$(jq -nc \
  --arg id "$DAILY_CALENDAR_ID" \
  --arg begin "$DAILY_START" --arg end "$DAILY_END" \
  '{calendarId:$id,timeMin:$begin,timeMax:$end,singleEvents:true,orderBy:"startTime",maxResults:250}')"
```

`nextPageToken`があれば`pageToken`を付けて続ける。終日予定は日付型の終了日が排他的であることに注意する。予定は対象日の範囲へ切り詰め、対象カレンダー共通の時間軸で扱う。

Docsは次の形で取得する。文書IDはローカル設定のURLから解決し、`DAILY_DOC_ID`に入れる。

```sh
gws docs documents get --params "$(jq -nc --arg id "$DAILY_DOC_ID" \
  '{documentId:$id,includeTabsContent:true}')" > "$DAILY_TMP/document.json"
```

生のDocs APIでは`.tabs[].tabProperties`と`.documentTab.body.content`を読む。`childTabs`もたどる。接続ツールがタブを平坦化して返す場合は、その返却形式に合わせる。`body`だけを読んで先頭タブを日報だと思い込まない。

## Docsへの書き込み

日付見出しと本文を組み立て、`documents.batchUpdate`を使う。必要なら`gws schema docs.documents.batchUpdate`で利用版のスキーマを確認する。

- 新しい日の挿入位置は日報タブの`index: 1`。`insertText.location.tabId`を指定する。範囲操作にも対象の`range.tabId`を付ける。
- 同日を更新するときは、対象の日付見出しから次の日付見出しまでを読み、変更する計画段落だけの範囲を求める。本人の追記が混ざったブロックを丸ごと置換しない。
- インデックスはUTF-16のコード単位。Pythonなら`len(text.encode("utf-16-le")) // 2`で数える。日付やIssueリンクの位置にも同じ計算を使う。
- 一つのbatch内でも、先の挿入・削除で後のインデックスが変わる。既存段落の複数編集は後方から行うなど、ずれを織り込む。
- 新規本文は先頭のタブ文字の数で階層を表現し、`createParagraphBullets`でネイティブの箇条書きにする。文字列の`- `をそのまま貼るだけでは終えない。
- 挿入箇所から継承した箇条書き・見出し・取り消し線などは、新規範囲内だけで整える。日付は原本に合わせた見出し、本文は通常段落とする。
- `createParagraphBullets`は先頭のタブ文字を除去する。見出しやリンクなど、挿入直後のインデックスを使う装飾を先に済ませ、箇条書き化を最後に行うか、除去後のインデックスを再計算する。
- 取得した`revisionId`を`writeControl.requiredRevisionId`に指定する。競合したら対象部分を読み直し、本人の変更を残して組み直す。

タブ指定の最小例。実際にはこれに、原本に合わせた見出し・本文スタイル・箇条書きの操作を加える。

```json
{
  "writeControl": {"requiredRevisionId": "READ_REVISION_ID"},
  "requests": [
    {"insertText": {
      "location": {"index": 1, "tabId": "TARGET_TAB_ID"},
      "text": "YYYY-MM-DD（曜）\n今日やること\n\t<会社フィールドの値>\n\t\t[社名] 作業名\n"
    }}
  ]
}
```

作成したJSONを一時ディレクトリに保存し、次の形で送る。

```sh
gws docs documents batchUpdate \
  --params "$(jq -nc --arg id "$DAILY_DOC_ID" '{documentId:$id}')" \
  --json "$(cat "$DAILY_TMP/requests.json")"
```

通信失敗で成否が不明なら、挿入位置を取得してから再実行する。追記を無条件に繰り返さない。完了後、対象タブを一度取得して内容と階層を確認する。

## GitHubへの反映

本文の実績は、例えば`## YYYY-MM-DD 日報の実績・メモ`の下にまとめる。同日の節があればその節を更新し、ほかの本文を残す。元のメモが複数階層ならMarkdownのインデントに直す。

```sh
gh issue view "$DAILY_ISSUE" --repo "$DAILY_REPO" --json number,title,body,state
gh issue list --repo "$DAILY_REPO" --state all --search "$DAILY_SEARCH" \
  --limit 100 --json number,title,body,state,url

# 既存本文を保持した更新後の全文を一時ファイルに用意する。
gh issue edit "$DAILY_ISSUE" --repo "$DAILY_REPO" \
  --body-file "$DAILY_TMP/issue-body.md"

# 新規Issueは重複検索を済ませてから作る。
gh issue create --repo "$DAILY_REPO" --title "$DAILY_TITLE" \
  --body-file "$DAILY_TMP/new-issue.md"

gh project field-list "$DAILY_PROJECT" --owner "$DAILY_OWNER" --format json
gh project item-add "$DAILY_PROJECT" --owner "$DAILY_OWNER" \
  --url "$DAILY_ISSUE_URL" --format json
```

元からProjectにあるIssueは、取得済みのitem IDを使う。フィールド操作は取得したProject ID・フィールドID・選択肢IDで行う。新規ログの期限は作業当日とし、既存タスクの期限は明示的な変更があるときだけ変更する。

```sh
gh project item-edit --id "$DAILY_ITEM_ID" --project-id "$DAILY_PROJECT_ID" \
  --field-id "$DAILY_DUE_FIELD_ID" --date "$DAILY_DATE"
gh project item-edit --id "$DAILY_ITEM_ID" --project-id "$DAILY_PROJECT_ID" \
  --field-id "$DAILY_STATUS_FIELD_ID" --single-select-option-id "$DAILY_STATUS_OPTION_ID"
```

会社・タスクの種類も、必要な場合は同じ単一選択フィールドの操作で設定する。通常の完了なら`gh issue close --reason completed`、重複・中止なら理由を本文に残して`--reason "not planned"`を使う。明示的な再開なら`gh issue reopen`とProjectのStatus更新を行う。コマンドには対象Issueと`--repo`を付ける。

親子関係はIssue本文への「親タスク」記述だけで済ませず、GitHubのsub-issuesを使う。作成したIssueの数値IDを取得し、親へ関連付ける。

```sh
gh api "repos/$DAILY_REPO/issues/$DAILY_CHILD_NUMBER" --jq .id
gh api --method POST "repos/$DAILY_REPO/issues/$DAILY_PARENT_NUMBER/sub_issues" \
  -F sub_issue_id="$DAILY_CHILD_DATABASE_ID"
```

書き込み後はIssue本文・状態・Projectの該当フィールドを確認する。途中で失敗したら完了済みの操作と残りを区別し、全体を最初から再登録しない。

## 参照先

- [Google Workspace CLIの認証と環境変数](https://github.com/googleworkspace/cli)
- [Google Docs APIのタブ](https://developers.google.com/workspace/docs/api/how-tos/tabs)
- [Google Docs APIの箇条書き](https://developers.google.com/workspace/docs/api/how-tos/lists)
- [GitHub CLIのProject操作](https://cli.github.com/manual/gh_project)
- [GitHub REST APIのsub-issues](https://docs.github.com/en/rest/issues/sub-issues)
