#!/usr/bin/env python3
r"""Record the race for site/slides/anim/race.html.

Asks several local models the same question through Ollama's API, streaming, and saves when each piece of the answer
arrived. The page replays the file this writes, site/slides/anim/data/race.json, token by token. Python's standard
library only.

For each --lane MODEL:gpu|cpu the script loads the model with a tiny request (so the load time is not in the race),
checks where it runs, streams the answer with temperature 0, seed 42 and a 4,096-token context (a cpu lane also gets num_gpu 0, which keeps
the model off the graphics chip), and unloads the model. It never downloads anything: pull the models first, and close
Zoom and other heavy apps so the timings are clean. The page draws up to three lanes.

The file (annotated here; JSON has no comments):

    {
      "question":    "In what year was NC State University founded? Answer in one sentence.",
      "machine":     "MacBook Pro, Apple M3 Pro, 36 GB",     # the --machine text
      "ollama":      "0.40.12",                              # GET /api/version
      "recorded":    "2026-11-01",                           # the day of the recording
      "placeholder": false,                                  # true only in the stand-in file that ships with the page
      "lanes": [
        {
          "model":     "gemma3:1b",
          "processor": "GPU",                                # "GPU", or "CPU only" for a cpu lane
          "eval_rate": 126.4,                                # tokens per second: eval_count / eval_duration
          "correct":   false,                                # does the answer contain --expect, ignoring case?
          "tokens":    [[162, "There"], [171, " are"], ...]  # [milliseconds since the request, the chunk's text]
        },
        ...
      ]
    }

Example:

    python3 tools/record_race.py \
        --question "In what year was NC State University founded? Answer in one sentence." --expect 1887 \
        --machine "MacBook Pro, Apple M3 Pro, 36 GB" \
        --lane gemma3:1b:gpu --lane gemma3:12b:gpu --lane gemma3:4b:cpu

--host points the script at another Ollama (default http://localhost:11434) and --out at another file (default the
page's data file).
"""
import argparse
import datetime
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT = ROOT / "site/slides/anim/data/race.json"
DEFAULT_HOST = "http://localhost:11434"
MAX_LANES = 3                                         # race.html draws three lanes
SEED = 42

# No proxy: this talks to a server on this machine (or, with --host, one that was named on purpose).
OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


class Failure(Exception):
    """Something the person running the script can fix. It is printed as one line, without a traceback."""


def call(host, path, body=None, timeout=600):
    """GET (no body) or POST (a JSON body) to the Ollama API. Returns the open response; the caller closes it."""
    req = urllib.request.Request(
        host + path,
        data=None if body is None else json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="GET" if body is None else "POST",
    )
    try:
        return OPENER.open(req, timeout=timeout)
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace").strip()
        try:
            detail = json.loads(detail).get("error", detail)
        except (ValueError, AttributeError):
            pass
        raise Failure(f"{path}: HTTP {e.code}: {detail}") from None
    except OSError as e:                              # refused, unreachable, timed out
        raise Failure(f"cannot reach Ollama at {host} ({getattr(e, 'reason', e)}). Is it running?") from None


def get_json(host, path):
    with call(host, path) as r:
        return json.load(r)


# The context length attendees' laptops get by default (Ollama gives 4,096 under 24 GiB of graphics memory). Left to
# Ollama, this Mac chose up to 131,072 tokens, whose working memory pushed gemma3:12b partly out of graphics memory.
NUM_CTX = 4096


def options(proc, **extra):
    """The request options: the same for every lane, plus num_gpu 0 for a cpu lane."""
    o = {"temperature": 0, "seed": SEED, "num_ctx": NUM_CTX}
    if proc == "cpu":
        o["num_gpu"] = 0
    o.update(extra)
    return o


def warm_up(host, model, proc):
    """Load the model with the lane's own options, so that the timed request does not pay for loading it.
    (num_gpu is a load-time option: a model loaded without it would be reloaded for the real request.)"""
    body = {"model": model, "prompt": "Say hi.", "stream": False, "options": options(proc, num_predict=1)}
    try:
        with call(host, "/api/generate", body) as r:
            r.read()
    except Failure as e:
        if "not found" in str(e):
            raise Failure(f"{e}\n  (this script never pulls a model: run `ollama pull {model}` first)") from None
        raise


def warn_if_misplaced(host, model, proc):
    """Ollama's /api/ps says how much of a loaded model sits in graphics memory. Warn when a lane runs elsewhere than
    its label says; the recording still goes ahead."""
    try:
        loaded = get_json(host, "/api/ps").get("models", [])
    except (Failure, ValueError, AttributeError):
        return
    for m in loaded:
        if m.get("name") not in (model, model + ":latest"):
            continue
        size, vram = m.get("size") or 0, m.get("size_vram") or 0
        if proc == "gpu" and size and vram < size:
            print(f"  warning: {model} is only {100 * vram // size}% in graphics memory, so this is not a GPU lane",
                  file=sys.stderr)
        if proc == "cpu" and vram > 0:
            print(f"  warning: {model} has {vram} bytes in graphics memory, so this is not a CPU-only lane",
                  file=sys.stderr)
        return


def stream_answer(host, model, proc, question):
    """Ask the question with stream: true. Returns ([[ms since the request, text], ...], the final chunk)."""
    body = {"model": model, "prompt": question, "stream": True, "options": options(proc)}
    tokens, final = [], None
    t0 = time.perf_counter()                          # the clock starts before the request goes out
    with call(host, "/api/generate", body) as r:
        for raw in r:                                 # one JSON object per line, as each chunk arrives
            ms = (time.perf_counter() - t0) * 1000
            raw = raw.strip()
            if not raw:
                continue
            try:
                chunk = json.loads(raw)
            except ValueError:
                raise Failure(f"{model}: the stream held something that is not JSON: {raw[:80]!r}") from None
            if chunk.get("error"):
                raise Failure(f"{model}: {chunk['error']}")
            text = chunk.get("response") or ""
            if text:
                tokens.append([round(ms), text])
            if chunk.get("done"):
                final = chunk
    if final is None:
        raise Failure(f"{model}: the stream ended before Ollama said it was done")
    if not tokens:
        raise Failure(f"{model}: the answer was empty")
    return tokens, final


def unload(host, model):
    """Free the model's memory (keep_alive 0), so the next lane starts clean. A failure here does not matter."""
    try:
        with call(host, "/api/generate", {"model": model, "keep_alive": 0}, timeout=60) as r:
            r.read()
    except Failure:
        pass


def record_lane(host, model, proc, question, expect):
    print(f"{model} ({proc}): loading ...", flush=True)
    warm_up(host, model, proc)
    warn_if_misplaced(host, model, proc)
    print("  streaming ...", flush=True)
    tokens, final = stream_answer(host, model, proc, question)
    unload(host, model)
    count, nanos = final.get("eval_count"), final.get("eval_duration")
    if not count or not nanos:
        raise Failure(f"{model}: Ollama's last chunk has no eval_count/eval_duration")
    text = "".join(t for _, t in tokens)
    lane = {
        "model": model,
        "processor": "GPU" if proc == "gpu" else "CPU only",
        "eval_rate": round(count / (nanos / 1e9), 1),
        "correct": expect.lower() in text.lower(),
        "tokens": tokens,
    }
    print(f"  {len(tokens)} chunks in {tokens[-1][0] / 1000:.1f} s, {lane['eval_rate']} tokens/s, "
          f"{'right' if lane['correct'] else 'wrong'} (looking for {expect!r})")
    print(f"  {' '.join(text.split())[:200]}")
    return lane


def render_json(data):
    """The file's text: one line per field, and each lane's tokens on a single line."""
    def dump(v):
        return json.dumps(v, ensure_ascii=False)

    lines = ["{"]
    for key in ("question", "machine", "ollama", "recorded", "placeholder"):
        lines.append(f"  {dump(key)}: {dump(data[key])},")
    lines.append('  "lanes": [')
    for i, lane in enumerate(data["lanes"]):
        lines.append("    {")
        for key in ("model", "processor", "eval_rate", "correct"):
            lines.append(f"      {dump(key)}: {dump(lane[key])},")
        tokens = ",".join(json.dumps(t, ensure_ascii=False, separators=(",", ":")) for t in lane["tokens"])
        lines.append(f'      "tokens": [{tokens}]')
        lines.append("    }" + ("," if i < len(data["lanes"]) - 1 else ""))
    lines += ["  ]", "}"]
    return "\n".join(lines) + "\n"


def parse_lane(spec):
    model, _, proc = spec.rpartition(":")             # model tags hold colons too: gemma3:1b:gpu
    proc = proc.lower()
    if not model or proc not in ("gpu", "cpu"):
        raise Failure(f"--lane {spec!r}: write it as MODEL:gpu or MODEL:cpu, for example gemma3:1b:gpu")
    return model, proc


def main(argv=None):
    ap = argparse.ArgumentParser(description="Record the race: one question, streamed from several local models.",
                                 epilog="Example: see the top of this file.")
    ap.add_argument("--lane", action="append", required=True, metavar="MODEL:gpu|cpu",
                    help=f"a model and where it runs; repeat for each lane (up to {MAX_LANES}). cpu adds num_gpu 0")
    ap.add_argument("--question", required=True, help="the prompt, also shown on the slide")
    ap.add_argument("--expect", required=True, metavar="TEXT",
                    help="a right answer contains this text, ignoring case (grades each lane's `correct`)")
    ap.add_argument("--machine", required=True, help="what it ran on, saved in the file (a MacBook Pro, its chip and memory)")
    ap.add_argument("--host", default=DEFAULT_HOST, help=f"Ollama's address (default {DEFAULT_HOST})")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT, help="where to write the data (default: the page's race.json)")
    args = ap.parse_args(argv)

    try:
        lanes = [parse_lane(s) for s in args.lane]
        if len(lanes) > MAX_LANES:
            raise Failure(f"the race page draws up to {MAX_LANES} lanes, and {len(lanes)} were given")
        if not args.expect.strip():
            raise Failure("--expect is empty, so every answer would count as right")
        host = args.host.strip().rstrip("/")
        if "://" not in host:
            host = "http://" + host
        version = get_json(host, "/api/version").get("version", "unknown")
        print(f"Ollama {version} at {host}", flush=True)
        data = {
            "question": args.question,
            "machine": args.machine,
            "ollama": version,
            "recorded": datetime.date.today().isoformat(),
            "placeholder": False,
            "lanes": [record_lane(host, m, p, args.question, args.expect) for m, p in lanes],
        }
    except Failure as e:
        sys.exit(f"error: {e}")
    except KeyboardInterrupt:
        sys.exit("interrupted: nothing was written")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    tmp = args.out.with_name(args.out.name + ".tmp")
    tmp.write_text(render_json(data), encoding="utf-8")
    tmp.replace(args.out)                             # the old file stays until a whole recording is ready
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
