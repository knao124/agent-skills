---
name: reading-note
description: Use this skill when the user wants to deeply understand a book, PDF, article, or document through a 精読代替ノート, 読書ノート, 論理復元ノート, concept ledger, question-chain summary, chapter logic map, or understanding-goal breakdown. Use it for Japanese requests such as 本を理解したい, 精読ノートを作って, 論理の流れを整理して, 登場単語を網羅して, or XXをYYできる理解ゴールを作って.
license: MIT
---

# Reading Note

Create a "精読代替ノート": a note that is less than full close reading, but good enough to help a serious first-time reader enter the book's logic, concepts, and practical understanding goals under time pressure.

The note must not be a compressed summary only. A first-time reader cannot absorb a dense "logic flow" before they know what problem the book solves, what object the book is constructing, and why each concept has to appear. Build the reader's entry route first, then provide the compressed logic as a review layer.

## Core Standard

The output succeeds when a reader can:

- State what the book is trying to make, decide, prove, or explain.
- Follow the author's argument as a chain of questions and answers.
- Explain why each important term appears, not only define it.
- Use the terms to perform concrete understanding goals such as "XXをYYできる".
- Separate "what the author is saying" from "whether the claim is valid, complete, or applicable".
- Reconstruct the book's main logic without pretending they have completed full close reading.

## Non-Negotiable Rules

- Do not begin with the compressed logic flow. Begin with an entry layer for first-time comprehension.
- Do not list terms as a glossary only. For each important term, explain its role in the argument or workflow.
- Do not fabricate source content. If the source text is missing, unavailable, or unreadable, ask for the source or state the limitation.
- Do not overquote. Paraphrase and summarize, using only short quotes when necessary.
- Preserve uncertainty. Mark inferred structure, missing source evidence, and weak confidence explicitly.
- Treat high-stakes domains such as finance, law, medicine, and tax as educational analysis, not professional advice.

## Workflow

1. Confirm and read the source.
   - If a local path, PDF, book title, or URL is provided, inspect the source before writing.
   - For a PDF, extract text and identify the table of contents, chapter headings, recurring terms, examples, formulas, and summary sections.
   - If only a title is provided and source access is uncertain, do not invent details. Ask for the file or use available source access if the user explicitly permits.

2. Identify the book's object.
   - Ask: "この本は読者に何を作れる・判断できる・説明できるようにする本か?"
   - Express this as an object, not only a topic.
   - Examples: a valuation model, a decision procedure, a causal explanation, a historical interpretation, an operating framework.

3. Build the entry map.
   - Explain the minimum whole structure before the detailed logic.
   - Use a domain-specific frame when available. For example, a valuation book may be organized around "cash flow / discount rate / terminal value / validation"; a statistics book around "data / model / estimation / uncertainty / decision".
   - Keep this section concrete and short enough for an initial reader to hold in working memory.

4. Create one simple running example.
   - Introduce a toy example that makes the abstract structure visible.
   - Use the example repeatedly to explain the logic, terms, and goals.
   - The example should be intentionally simple; it is for orientation, not precision.

5. Convert the argument into a question chain.
   - Write the book's flow as "問い -> 答え -> 次の問い".
   - This is the main bridge between first-time comprehension and compressed logic.
   - Prefer causal and procedural connections over chapter-title paraphrase.

6. Only then write the compressed logic flow.
   - Now summarize the argument densely.
   - The compressed flow should be readable as a review because the entry map and question chain already prepared the reader.

7. Map chapters by function.
   - For each chapter or major section, record:
     - The question it answers.
     - The answer or move it contributes.
     - The concepts introduced.
     - The next question it creates.
   - Do not merely summarize chapter contents.

8. Build the concept ledger.
   - Split terms into categories such as 骨格語, 実務補助語, 手続き語, 評価語, and 反例語 when useful.
   - Use the same explanatory format for all categories.
   - For each term, include: plain meaning, why it is needed, where it appears in the logic, what misunderstanding it prevents, and what the reader should be able to do with it.

9. Extract formulas, procedures, or rules only when they are structurally important.
   - Include the minimum formulas or steps needed to reconstruct the book's reasoning.
   - Explain each formula as a role in the argument, not as a standalone equation.

10. Write understanding goals.
   - Use the format "XXをYYできる".
   - Cover concept recognition, explanation, calculation or application, comparison, diagnosis, and critique when relevant.
   - Goals should be testable by a reader, not vague aspirations.

11. Add validity checks.
   - Separate author-internal reconstruction from external evaluation.
   - Record assumptions, weak points, counterexamples, scope limits, and practical caveats.

12. Add self-tests.
   - Include questions that verify whether the reader can reconstruct the argument.
   - Include at least one "explain to a beginner" test and one "apply to a new case" test.

## Output Template

Use Japanese by default unless the user requests another language.

```markdown
# <書名> 精読代替ノート

## 1. この本は何を作る本か

## 2. 全体構造

## 3. ひとつの単純な例

## 4. 問いの連鎖

| 問い | 著者の答え | その答えが生む次の問い |
| --- | --- | --- |

## 5. 圧縮版の論理の流れ

## 6. 章ごとの役割

| 章 | 答える問い | 本章の答え | 登場概念 | 次の問い |
| --- | --- | --- | --- | --- |

## 7. 重要概念台帳

| 区分 | 概念 | 平たく言うと | なぜ必要か | 論理上の位置 | 誤解すると何が壊れるか | できるようになること |
| --- | --- | --- | --- | --- | --- | --- |

## 8. 理論と実務の接続

| 理論上の概念 | 実務で見る対象 | どう接続するか | 注意点 |
| --- | --- | --- | --- |

## 9. 最小公式・手順集

## 10. 理解ゴール一覧

| ゴール | 使う概念 | 合格基準 |
| --- | --- | --- |

## 11. 検証メモ

### 著者の前提

### 弱いところ・注意点

### 反例・適用限界

## 12. 自己テスト

## 13. 1分説明
```

## Style

- Write as a study tool, not as a book review.
- Prefer concrete verbs: 見積もる, 比較する, 切り分ける, 説明する, 検証する.
- Use tables for repeated structured information.
- Use prose for "why this matters" sections; do not reduce the whole note to lists.
- If the user asks for only an outline, provide the same structure in abbreviated form and say that it is a draft rule, not a source-grounded final note.

## Completion Checklist

Before finishing, verify that the note includes:

- An entry layer before the compressed logic.
- A running example or equivalent concrete anchor.
- A question chain.
- Chapter roles as question-answer-next question, if chapters are available.
- Concept ledger with "why needed" and "what the reader can do with it".
- Understanding goals in "XXをYYできる" form.
- Assumptions, limits, and self-tests.
