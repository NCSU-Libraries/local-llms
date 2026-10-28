"""Code open-ended survey answers by theme with a local model.

Usage:
    uv run --with ollama python code_answers.py survey-100.csv --model gemma3:4b

Reads a CSV with `id` and `answer` columns (and an optional `our_code` column
holding your own hand-coding), asks the model for one theme per answer, prints
a summary, and writes coded.csv. Everything runs on your computer.
"""
import argparse, csv, hashlib, json, time
from collections import Counter
import ollama

THEMES = ["quiet space", "longer hours", "seats and outlets",
          "wifi and computers", "group rooms", "food and drink"]
SYSTEM = ("You code survey answers about what would improve students' study experience at a university library. "
          "Pick the ONE theme the answer is mostly about. Themes: " + "; ".join(THEMES) + ".")
SCHEMA = {"type": "object", "required": ["theme"],
          "properties": {"theme": {"type": "string", "enum": THEMES}}}

parser = argparse.ArgumentParser()
parser.add_argument("csv_file")
parser.add_argument("--model", default="gemma3:4b")
args = parser.parse_args()
rows = list(csv.DictReader(open(args.csv_file, newline="", encoding="utf-8")))

start = time.time()
for n, row in enumerate(rows, 1):
    reply = ollama.chat(model=args.model, format=SCHEMA,
                        options={"temperature": 0, "seed": 42},
                        messages=[{"role": "system", "content": SYSTEM},
                                  {"role": "user", "content": row["answer"]}])
    row["theme"] = json.loads(reply.message.content)["theme"]
    print(f"\rcoded {n}/{len(rows)} · {time.time() - start:.0f} s", end="", flush=True)
seconds = time.time() - start

print("\n\nTHEMES")
counts = Counter(row["theme"] for row in rows)
for theme in THEMES:
    counts.setdefault(theme, 0)
for theme, count in counts.most_common():
    print(f"  {theme:<20}{'█' * count} {count}")

checked = [r for r in rows if r.get("our_code")]
if checked:
    agree = sum(r["theme"] == r["our_code"] for r in checked)
    print(f"\nThe model agrees with our coding on {agree} of {len(checked)}.")
    for r in checked:
        if r["theme"] != r["our_code"]:
            print(f'  "{r["answer"][:60]}..."\n      ours: {r["our_code"]}   model: {r["theme"]}')

print(f"\nTotal time: {seconds:.0f} s, {seconds / len(rows):.1f} s per answer")
fingerprint = hashlib.sha256("\n".join(r["theme"] for r in rows).encode()).hexdigest()[:8]
print(f"Fingerprint of all {len(rows)} labels: {fingerprint}")
print("Run it again: same fingerprint, same labels.")

with open("coded.csv", "w", newline="", encoding="utf-8") as f:
    out = csv.DictWriter(f, fieldnames=["id", "answer", "theme"], extrasaction="ignore")
    out.writeheader()
    out.writerows(rows)
