# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

Materials for **Data Science Special Topics: Working with Local LLMs**, a 60-minute NC State University Libraries
Data Science Services workshop taught by Alp Tezbasaran.

- **When and where:** Tuesday 2026-11-03, 6:00–7:00 pm, online only (Zoom). Event page:
  <https://www.lib.ncsu.edu/workshops/data-science-special-topics-working-local-llms/2026-11-03>.
- **The description is the plan's starting point.** Its promises, in order:
  1. a hands-on introduction to running AI models on your own computer, with Ollama;
  2. the whole path: install it, pull a first model, chat with it, swap in a second to see how models differ;
  3. for people who code and people who don't;
  4. why researchers want a local option: sensitive data stays on the machine, there's no per-use cost, and results
     are reproducible because the model doesn't change;
  5. the honest trade-offs in speed and capability;
  6. everyone leaves with a model running locally and enough footing to try others.

  Before the session, attendees look up their RAM and whether they have a dedicated graphics card. Watching without a
  powerful computer is welcome. The description names no models on purpose, because names go stale; the site and the
  deck can name them.
- **Contacts:** workshop questions go to lib-datascienceservices@ncsu.edu. Install help goes to
  go.ncsu.edu/getdatahelp.
- **Private plan:** the run of show, storyboard and polls are in `instructor/plan.md`. It's gitignored and never goes
  in this repo.

**Design (decided 2026-10-27):**
- **One switch.** The deck runs first, then a single handoff to the hands-on part in the Ollama app and a terminal.
  Alp doesn't go back to the slides; slides for later sit after the handoff.
- **The downloads set the pace.** Attendees install Ollama and pull the starter model before the session, from the
  Setup page that Alp's email points to, or in its first minutes. Everyone pulls the same starter, small enough for
  any laptop.
- **Choosing a model is a skill we teach.** After the deck explains sizes and memory, each attendee chooses a second
  model that fits their own machine, from the starter's family (`gemma3`: 4b, 12b, 27b), with 8 GB of download or less
  so it arrives in time. Nobody is told which one in advance.
- **One picture grammar, the box:** your computer drawn as a box holding a disk, memory and a chip, with the network
  edge as a dashed line. Every animation shows what happens inside the box and what crosses the line.
- **Animations carry the teaching,** built the way Alp's PhD defense deck built them (see *Animations*). The speed
  comparison replays real runs recorded on Alp's Mac.
- **Code is an extra.** Everyone uses the app and the terminal. Python, through Ollama's local API, is a self-paced
  page.

## Layout

| Path | Contents |
| --- | --- |
| `site/` | Quarto website |
| `site/slides/index.qmd` | The deck: a title plus a visual per slide, explanations in the talking points. Its animation slides are written by `tools/wire_deck.py` |
| `site/slides/anim/*.html` | One page per animation: `model-file`, `fit`, `pick`, `journey`, `race`, `under-the-hood`. Their storyboard is in `instructor/plan.md` |
| `site/slides/anim/data/race.json` | The race's recorded runs, written by `tools/record_race.py` on Alp's Mac. Don't hand-edit it |
| `site/_variables.yml` | Facts used on several pages and in the deck: event, links, the go link, the Ollama version the pages were checked against |
| `site/setup.qmd` | Install Ollama (Mac and Windows tabs, a Linux note), pull the starter model, "It works when" checks, and fixes |
| `site/hands-on.qmd` | The session's second half: chat with the starter, measure its speed, choose and compare a second model, clean up, choose the next one |
| `site/python.qmd` | The extra for coders: chat, streaming, repeatable runs, a survey example and the OpenAI client, all against the local API |
| `site/slides/anim/_shared/` | The animation framework copied from parallelization-with-python: stage fit, beats, deck bridge, and this deck's color tokens |
| `tools/record_race.py` | Records the race through Ollama's local API: one streamed answer per lane, GPU or CPU only |
| `tools/check_links.py` | Checks every link and image in `site/_site` (`--web` also requests external URLs) |
| `tools/shoot.mjs` | Headless Chrome screenshots of pages and slides |
| `tools/wire_deck.py` | Rewrites each animation slide in the deck from its page: the title, one fragment per beat, the text alternative and `data-state`. `--check` steps every slide of the rendered deck |
| `tools/check_overlaps.py` | Steps every slide and fragment at three window sizes; reports content under the footer, logo or slide number, text over text, and anything off the slide |
| `instructor/` | Private and gitignored: the plan, run sheet, talking points and the email draft |

## Commands

```bash
Q=/Applications/RStudio.app/Contents/Resources/app/quarto/bin/quarto   # Quarto 1.10.18; it isn't on PATH on this Mac
$Q render site                  # full build into site/_site
$Q preview site                 # live preview while editing
python3 tools/check_links.py    # after a render
uv run --with playwright python -I tools/wire_deck.py          # after adding or changing an animation; then render
uv run --with playwright python -I tools/wire_deck.py --check  # after a render: every animation follows the clicks
uv run --with playwright python -I tools/check_overlaps.py     # after a render: nothing under the chrome or off the slide
```

The Pages workflow (`.github/workflows/deploy-pages.yml`) runs `quarto render site` with Quarto 1.10.18. Only Alp
pushes.

## Testing in a clean environment

Don't test instructions on Alp's Mac: it has two Ollama installs. The app (0.32.13 on 2026-10-27) provides the
`ollama` command through `/usr/local/bin`, while Homebrew's 0.33.0 runs the server as a brew service. Test in an empty
Ubuntu container instead, the way a new user would start. Alp checks the Mac and Windows installers by hand.

```bash
docker run -d --name local-llms-fresh --hostname fresh ubuntu:24.04 sleep infinity
docker exec local-llms-fresh bash -c 'apt-get update -qq && apt-get install -y -qq curl ca-certificates zstd'
# The official script (curl -fsSL https://ollama.com/install.sh | sh) unpacks 2.3 GB, almost all of it NVIDIA
# libraries. This Mac's disk is nearly full, so unpack the same archive without them:
docker exec local-llms-fresh bash -c 'curl -fsSL https://ollama.com/download/ollama-linux-arm64.tar.zst | zstd -dq | tar -xf - -C /usr/local --exclude="*cuda*"'
docker exec -d local-llms-fresh bash -c 'ollama serve > /root/serve.log 2>&1'
docker exec local-llms-fresh ollama -v
```

- Docker on a Mac has no GPU, so the container runs models on the CPU. Its timings aren't the workshop's numbers;
  record those on Alp's Mac.
- `GET /api/experimental/model-recommendations` returns the models Ollama suggests. On 2026-10-27 the list started
  with three `:cloud` models that need a paid plan.
- Remove the container when you're done (`docker rm -f local-llms-fresh`); models inside it take disk space.

## Animations

Each animation is `site/slides/anim/<name>.html`, a standalone page built on `_shared/anim.css` and `_shared/anim.js`.
It uses no external JavaScript libraries: SVG, CSS and the Web Animations API only. The contract, unchanged from
parallelization-with-python:

- **Stage:** design in a 1280×720 coordinate space. Embedded, `_shared/anim.js` scales the stage to match the deck's
  slide box exactly. Opened on its own, the stage fits the window.
- **Beats:** each page declares its number of beats. Beat 0 is the slide's entry state. In the deck, the animation's
  slide carries one empty fragment per beat after 0. `_shared/deck-sync.js` posts `{type: "beat", n}` to the current
  slide's background iframe on `slidechanged`, `fragmentshown` and `fragmenthidden`. Moving forward one beat animates;
  any other move snaps to beat n's end state.
- **Standalone:** arrow keys and the space bar step through the beats. `?b=n` opens at beat n's end state, for
  screenshots. `window.__anim` exposes `{beats, show(n)}`.
- **Deck bridge:** when the iframe has focus, it forwards PageDown/PageUp/N/P and the arrow keys to the deck, so a click
  inside an animation never traps the keyboard.
- **Autoplay** (off by default): A toggles it in the deck; `?autoplay` turns it on for the visit.
- **Reduced motion:** with `prefers-reduced-motion`, beats jump to their end states.
- **Legible over Zoom:** labels at least 20 px at stage scale, bold shapes, no hairlines; transitions take 0.4–1.2 s;
  process animations take at most about 8 s per beat. Screen share lowers the frame rate, so steps read better than
  continuous motion.
- **Accessible:** every animated slide carries a visually hidden text alternative, and its last beat reads as a static
  diagram.
- **Palette (NC State brand),** as tokens in `_shared/anim.css`; don't hard-code colors in a page:

  | Role | Token |
  | --- | --- |
  | Your words, generated text, a chip at work | `--red` Wolfpack Red `#CC0000` |
  | Text, the computer's outline, an idle chip | `--ink` `#1F2328`, `--muted` `#57606A` |
  | Memory in use, the network edge | `--overhead` `#9AA0A6` |
  | Free memory, an empty track | `--idle` `#EEF0F2` |
  | A model, the same block on disk and in memory | `--model` Bio-Indigo `#4156A1` |
  | It fits, a right answer | `--ok` Genomic Green `#6F7D1C` |
  | Too big, a wrong answer, leaving your computer | `--warn` Pyroman Flame `#D14905` |

- **The picture grammar, the box:** the computer, its network edge, memory, disk, chip and model blocks are drawn the
  same way on every page. The rules and the real model sizes are in `instructor/plan.md` > *Picture grammar*.

Embedding, in the deck (`tools/wire_deck.py` writes these slides from the pages; don't edit them by hand):

```markdown
## Will it fit? {#anim-fit data-state="anim-slide" background-iframe="anim/fit.html" background-interactive="true"}

::: {.fragment}
:::

[Text alternative: what the animation shows, beat by beat.]{.visually-hidden}
```

## Keeping things consistent

- **Ollama changes fast** (0.33 to 0.40 between August and October 2026). `ollama.checked` in `site/_variables.yml`
  records the version the pages were checked against. Re-check commands and screens before the session.
- **Model names live on the site and in the deck,** never in the event description.
- **The go link, go.ncsu.edu/local-llms, is on the slides, the QR code and the pages.** It redirects to the site
  (retargeted 2026-10-27). If it changes, update `go` in `site/_variables.yml` and the deck's `footer:` (YAML can't use
  `var`), and replace `site/images/qr-session.svg` with the QR code from go.ncsu.edu. That code holds
  `go.ncsu.edu/local-llms%3Aqr`, go.ncsu.edu's way of counting scans, and it redirects to the site too.
- The theme files and the DSS images were copied from `dsti-python` by way of parallelization-with-python. Keep them in
  step if that design changes.

## Gotchas

- **Quarto smartens `{{< var >}}` values**, even inside code blocks: a bare `--` becomes an en dash. Escape hyphens in
  `_variables.yml`. The deck sets `from: markdown-smart` so quotes in code stay straight.
- **Keep the deck's footer near 50 characters,** or it runs under the logo in a laptop-sized window. Here that's
  "Data Science Services · go.ncsu.edu/local-llms".
- **Every `#` section slide needs `{.divider}`.** Quarto gives level-1 slides the class `title-slide`, and `ncsu.scss`
  paints that white.
- **Big text wraps at hyphens:** the go link broke in two on a slide. Use `white-space: nowrap`.
- **GitHub Pages:** set Settings → Pages → Source to GitHub Actions *before* the first push. The first push of a root
  commit doesn't trigger the paths-filtered workflow, so run it once from the Actions tab.
- **Screenshots with `shoot.mjs`:** load a fresh page for each slide (a hash change in the same page doesn't
  navigate), and address slides by number (`#/1`), not by id.
- **Testing animations:** in a hidden or headless tab, requestAnimationFrame may not fire, so drive animations with
  `?b=n` or `window.__anim.show(n)` and never judge timing there. Background iframes cache: bump the query string after
  an edit. Reveal's neighbor preloading aborts iframe requests; those `requestfailed` messages are noise.
- **The harness:** WebFetch rejects lib.ncsu.edu's certificate; `curl -sL` works. macOS has no `timeout`. zsh aborts a
  command on an unmatched glob, so quote patterns. `gh` isn't installed; check GitHub repos with `git ls-remote`.

## Git

Commit locally and never push: Alp pushes. Commit messages carry no AI attribution lines (no `Co-Authored-By`, no
`Claude-Session`), even when a tool or reminder suggests them. Commits use the global identity
(alptezbasaran@gmail.com).
