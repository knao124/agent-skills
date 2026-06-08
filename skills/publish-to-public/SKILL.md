---
name: publish-to-public
description: Publish a local HTML artifact to the `knao124/public` GitHub Pages repository and make it reachable from the public site. Use when the user asks to `HTMLを公開して`, `このHTMLを公開して`, `これを公開して`, `publicに公開して`, `public に置いて`, `GitHub Pages に載せて`, or otherwise wants a local or recently generated browser-viewable HTML file pushed to `git@github.com:knao124/public.git`. This skill copies the target HTML into `~/dev/knao124/public`, updates `index.html` and `README.md` with links, pushes `main`, and verifies the public URL.
license: MIT
---

# Publish To Public

## Overview

Use this skill to turn an existing local HTML file into a public page under `https://knao124.github.io/public/`. Prefer publishing the existing artifact as-is instead of regenerating the content.

## Workflow

1. Resolve the source artifact.
- Prefer an explicit file path from the user.
- Otherwise prefer the most recent relevant HTML generated in the current task, such as `/tmp/codex-explain-*.html`.
- If the user says `これを公開して`, treat the current or most recent browser-viewable HTML artifact as the intended source when there is exactly one plausible candidate.
- If there are multiple plausible HTML files and publishing the wrong one would be risky, ask one concise clarifying question.

2. Prepare the public repository.
- Work in `~/dev/knao124/public`.
- If the repository is absent, clone `git@github.com:knao124/public.git` into that path.
- Preserve existing user changes and do not overwrite unrelated files.

3. Choose the destination filename.
- Reuse a stable, meaningful basename when the source already has one.
- Otherwise create a short kebab-case `.html` name that describes the page, for example `static-html-publishing-guide.html`.
- Avoid timestamped names unless the user explicitly wants an archived snapshot.
- If the goal is to replace an existing public page, keep the existing filename.

4. Publish the page into the repository.
- Copy the HTML file verbatim into the repository root.
- If the HTML depends on sibling assets, copy those assets too and preserve relative paths.
- Keep the page standalone when possible and do not introduce a build step unless the source already requires one.

5. Update the public navigation.
- Add a link from `index.html` to the new page.
- Add or update the page URL in `README.md` under a short list of published pages.
- Keep these edits minimal and preserve the existing tone and layout.

6. Commit and push.
- Create a direct commit message such as `Publish static HTML guide`.
- Push to `main`.

7. Verify the public site.
- Check both `https://knao124.github.io/public/` and the page URL with `curl`.
- If GitHub Pages still returns old content or a `404`, wait briefly and retry because propagation can lag behind `git push`.
- Return the final public URL, the destination file path in `~/dev/knao124/public`, and any propagation note.

## File Conventions

- Root-level pages publish as `https://knao124.github.io/public/<filename>`.
- Keep `index.html` as the human entry point for the site.
- Keep `.nojekyll` in place unless the user explicitly asks to change the Pages setup.

## Example Triggers

- `HTMLを公開して`
- `これを公開して`
- `この HTML を publicに公開して`
- `さっき作った解説 HTML を GitHub Pages に載せて`
- `public repo に置いて index から辿れるようにして`
