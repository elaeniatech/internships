import argparse
import json
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen

import pandas as pd

from generate_internships import DATA_CSV, ROOT, load_data


OUTPUT_DIR = ROOT / "output" / "txt"
MAX_WORDS = 150


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate bilingual internship summaries from data/internships.csv."
    )
    parser.add_argument("id", nargs="?", help="Internship id to generate, for example 012026.")
    return parser.parse_args()


def load_rows(internship_id: str | None = None) -> list[dict[str, str]]:
    df = load_data(DATA_CSV)

    if internship_id:
        df = df[df["id"].astype(str).str.strip() == internship_id.strip()]
        if df.empty:
            raise ValueError(f"Internship id not found in data/internships.csv: {internship_id}")

    rows: list[dict[str, str]] = []
    for _, row in df.iterrows():
        rows.append({column: ("" if pd.isna(value) else str(value).strip()) for column, value in row.items()})
    return rows


def as_items(text: str, limit: int) -> list[str]:
    return [item.strip() for item in text.split(";") if item.strip()][:limit]


def join_items(items: list[str], lowercase: bool = False) -> str:
    if not items:
        return ""
    if lowercase:
        items = [lower_first(item) for item in items]
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return f"{', '.join(items[:-1])}, and {items[-1]}"


def normalize_whitespace(text: str) -> str:
    return " ".join(text.split())


def lower_first(text: str) -> str:
    if not text:
        return text
    return text[0].lower() + text[1:]


def truncate_to_word_limit(text: str, max_words: int = MAX_WORDS) -> str:
    words = text.split()
    if len(words) <= max_words:
        return text
    trimmed = " ".join(words[:max_words]).rstrip(".,;: ")
    return f"{trimmed}."


def format_summary_text(text: str) -> str:
    sentences = [sentence.strip() for sentence in text.split(". ") if sentence.strip()]
    formatted: list[str] = []
    for sentence in sentences:
        formatted.append(sentence if sentence.endswith(".") else f"{sentence}.")
    return "\n".join(formatted)


def build_english_summary(row: dict[str, str]) -> str:
    objectives = join_items(as_items(row.get("objectives", ""), 3), lowercase=True)
    tasks = join_items(as_items(row.get("tasks", ""), 3), lowercase=True)
    requirements = join_items(as_items(row.get("requirements", ""), 3))
    deliverables = join_items(as_items(row.get("deliverables", ""), 2))

    parts = [
        f"{row['title']} ({row['id']}) is a {row['duration_months']}-month internship.",
        row["description"],
    ]

    if objectives:
        parts.append(f"The main goals are to {objectives}.")
    if tasks:
        parts.append(f"Typical work includes {tasks}.")
    if requirements:
        parts.append(f"The role is best suited for candidates with {requirements}.")
    if deliverables:
        parts.append(f"Expected deliverables include {deliverables}.")
    if row.get("payment") or row.get("supervisor"):
        parts.append(
            f"Payment: {row.get('payment', 'N/A')}. Supervisor: {row.get('supervisor', 'N/A')}."
        )

    return truncate_to_word_limit(normalize_whitespace(" ".join(parts)))


def translate_text(text: str, target_lang: str) -> str:
    url = (
        "https://translate.googleapis.com/translate_a/single"
        f"?client=gtx&sl=en&tl={target_lang}&dt=t&q={quote(text)}"
    )
    with urlopen(url, timeout=15) as response:
        payload = json.loads(response.read().decode("utf-8"))
    translated = "".join(chunk[0] for chunk in payload[0] if chunk and chunk[0])
    return normalize_whitespace(translated)


def safe_output_id(value: str) -> str:
    cleaned = "".join(char if char.isalnum() or char in ("-", "_") else "_" for char in value.strip())
    if not cleaned:
        raise ValueError("The selected internship row is missing an id.")
    return cleaned


def write_summary_files(row: dict[str, str]) -> tuple[Path, Path]:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_id = safe_output_id(row["id"])
    english_summary = build_english_summary(row)
    spanish_summary = truncate_to_word_limit(translate_text(english_summary, "es"))
    formatted_english_summary = format_summary_text(english_summary)
    formatted_spanish_summary = format_summary_text(spanish_summary)

    en_path = OUTPUT_DIR / f"{output_id}_en.txt"
    es_path = OUTPUT_DIR / f"{output_id}_es.txt"
    en_path.write_text(f"{formatted_english_summary}\n", encoding="utf-8")
    es_path.write_text(f"{formatted_spanish_summary}\n", encoding="utf-8")
    return en_path, es_path


def generate_summaries(internship_id: str | None = None) -> list[tuple[Path, Path]]:
    rows = load_rows(internship_id)
    return [write_summary_files(row) for row in rows]


if __name__ == "__main__":
    try:
        args = parse_args()
        generated = generate_summaries(args.id)
        for en_path, es_path in generated:
            print(f"Summary generated: {en_path}")
            print(f"Summary generated: {es_path}")
    except Exception as exc:
        raise SystemExit(f"Error: {exc}")
