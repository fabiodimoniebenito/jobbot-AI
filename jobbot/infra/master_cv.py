"""Lectura del PDF del CV maestro."""
import json
import shutil
from pathlib import Path

from jobbot.domain.master import merge_master, parse_master_text


def read_master(pdf: Path) -> dict:
    from pypdf import PdfReader

    text = "\n".join(p.extract_text(extraction_mode="layout") for p in PdfReader(str(pdf)).pages)
    return parse_master_text(text)


def sync_cv(pdf: Path, cv_file: Path, aplicar: bool) -> str:
    """Devuelve el diff; con aplicar=True escribe cv_file tras copiar cv_file.bak."""
    cv = json.loads(cv_file.read_text(encoding="utf-8"))
    new, diff = merge_master(cv, read_master(pdf))
    if aplicar and diff:
        shutil.copy2(cv_file, cv_file.with_suffix(cv_file.suffix + ".bak"))
        cv_file.write_text(json.dumps(new, ensure_ascii=False, indent=2), encoding="utf-8")
    return diff
