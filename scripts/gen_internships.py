from pathlib import Path

import pandas as pd
from pandas.errors import EmptyDataError
from pylatex import (
    Document,
    NoEscape,
    Package,
)
from pylatex.utils import escape_latex


ROOT = Path(__file__).resolve().parent.parent
DATA_CSV = ROOT / "data" / "internships.csv"
OUTPUT_DIR = ROOT / "output" / "pdf"
RIGHT_LOGO = ROOT / "fig" / "logo.png"

REQUIRED_FIELDS = [
    "id",
    "title",
    "description",
    "requirements",
    "objectives",
    "tasks",
    "equipment",
    "deliverables",
    "work breakdown",
    "duration_months",
    "payment",
    "supervisor",
]


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names for resilient matching."""
    normalized = {
        col: " ".join(str(col).strip().lower().split())
        for col in df.columns
    }
    return df.rename(columns=normalized)


def load_last_row(csv_path: Path) -> dict:
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    try:
        try:
            df = pd.read_csv(csv_path, encoding="utf-8-sig", dtype=str, keep_default_na=False)
        except UnicodeDecodeError:
            df = pd.read_csv(csv_path, encoding="latin-1", dtype=str, keep_default_na=False)
    except EmptyDataError as exc:
        raise ValueError(
            f"The CSV is empty: {csv_path}. Add headers and at least one row in data/internships.csv."
        ) from exc

    if df.empty:
        raise ValueError(
            f"The CSV is empty: {csv_path}. Add at least one row in data/internships.csv."
        )

    df = normalize_columns(df)
    missing = [field for field in REQUIRED_FIELDS if field not in df.columns]
    if missing:
        raise ValueError(
            "Missing required columns in data/internships.csv: "
            + ", ".join(missing)
        )

    last_row = df.iloc[-1].to_dict()
    return {field: ("" if pd.isna(last_row[field]) else str(last_row[field])) for field in REQUIRED_FIELDS}


def build_header(doc: Document) -> None:
    right_logo = (
        rf"\includegraphics[width=0.82\linewidth]{{{RIGHT_LOGO.as_posix()}}}"
        if RIGHT_LOGO.exists()
        else ""
    )
    header = rf"""
\begin{{minipage}}[c]{{0.16\textwidth}}
    
\end{{minipage}}
\begin{{minipage}}[c]{{0.54\textwidth}}
    \raggedright
    {{\Large\textbf{{Internship Overview}}}}
\end{{minipage}}
\hfill
\begin{{minipage}}[c]{{0.28\textwidth}}
    \raggedleft
    {right_logo}
\end{{minipage}}
\vspace{{0.6cm}}
"""
    doc.append(NoEscape(header))


def as_items(text: str) -> list[str]:
    return [item.strip() for item in text.split(";") if item.strip()]


def build_bullets(doc: Document, title: str, values: list[str]) -> None:
    doc.append(NoEscape(rf"\textbf{{{escape_latex(title)}}}"))
    doc.append(NoEscape(r"\begin{itemize}[leftmargin=*,itemsep=2pt,topsep=0pt,parsep=0pt,partopsep=0pt]"))
    for value in values:
        doc.append(NoEscape(rf"\item {escape_latex(value)}"))
    doc.append(NoEscape(r"\end{itemize}"))


def build_content(doc: Document, data: dict) -> None:
    title = escape_latex(data["title"])
    opp_id = escape_latex(data["id"])
    description = escape_latex(data["description"])

    doc.append(NoEscape(rf"\begin{{center}}\LARGE\textbf{{{title}}}\\[2pt]\large [ID {opp_id}]\end{{center}}"))
    doc.append(NoEscape(r"\vspace{4pt}"))
    doc.append(NoEscape(rf"\noindent {description}"))
    doc.append(NoEscape(r"\vspace{6pt}"))

    requirements = as_items(data["requirements"])
    objectives = as_items(data["objectives"])
    tasks = as_items(data["tasks"])
    equipment = as_items(data["equipment"])
    deliverables = as_items(data["deliverables"])
    work_breakdown = as_items(data["work breakdown"])
    duration_months = data["duration_months"].strip()
    payment = data["payment"].strip()
    supervisor = data["supervisor"].strip()

    doc.append(NoEscape(r"\vspace{4pt}\hrule\vspace{8pt}"))

    if objectives:
        build_bullets(doc, "Objectives", objectives)
    if tasks:
        build_bullets(doc, "Tasks", tasks)
    if requirements:
        build_bullets(doc, "Requirements", requirements)
    if equipment:
        build_bullets(doc, "Equipment", equipment)
    if deliverables:
        build_bullets(doc, "Deliverables", deliverables)
    if work_breakdown:
        build_bullets(doc, "Work Breakdown", work_breakdown)

    doc.append(NoEscape(r"\vspace{6pt}\hrule\vspace{8pt}"))
    doc.append(NoEscape(rf"\textbf{{Duration:}} {escape_latex(duration_months)} months\\[4pt]"))
    doc.append(NoEscape(rf"\textbf{{Payment:}} {escape_latex(payment)}\\[4pt]"))
    doc.append(NoEscape(rf"\textbf{{Supervisor:}} {escape_latex(supervisor)}"))


def generate_pdf() -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    latest = load_last_row(DATA_CSV)

    doc = Document(
        documentclass="article",
        geometry_options={
            "margin": "1.8cm",
            "letterpaper": True,
        },
    )

    doc.packages.append(Package("graphicx"))
    doc.packages.append(Package("xcolor"))
    doc.packages.append(Package("array"))
    doc.packages.append(Package("enumitem"))
    doc.packages.append(Package("parskip"))

    build_header(doc)
    build_content(doc, latest)

    output_id = latest["id"].strip()
    if not output_id:
        raise ValueError("The selected internship row is missing an id.")

    safe_output_id = "".join(char if char.isalnum() or char in ("-", "_") else "_" for char in output_id)
    doc_name = OUTPUT_DIR / safe_output_id
    doc.generate_pdf(str(doc_name), clean_tex=False)
    return doc_name.with_suffix(".pdf")


if __name__ == "__main__":
    try:
        pdf_path = generate_pdf()
        print(f"PDF generated: {pdf_path}")
    except Exception as exc:
        raise SystemExit(f"Error: {exc}")

