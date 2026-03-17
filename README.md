# internships

Genera fichas PDF de pasantías y resúmenes bilingües.

## Estructura

- `scripts/gen_internships.py` — genera la ficha LaTeX/PDF de una pasantía a partir de `data/internships.csv`
- `scripts/gen_summary.py` — genera resúmenes en inglés y español en `output/summary/`
- `data/internships.csv` — fuente de datos
- `assets/images/` — logos e imágenes usadas por la plantilla
- `output/tex/` — archivos `.tex` generados
- `output/pdf/` — archivos `.pdf` generados
- `output/txt/` — resúmenes `.txt` generados

## Uso

```bash
python3 scripts/generate_internships.py
python3 scripts/generate_summary.py
```

También podés generar una pasantía específica por ID:

```bash
python3 scripts/generate_internships.py 012026
python3 scripts/generate_summary.py 012026
```
