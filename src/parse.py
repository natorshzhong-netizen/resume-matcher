"""把简历/JD 文件读成纯文本：DOCX / PDF / TXT / MD。"""
from __future__ import annotations

from pathlib import Path

SUPPORTED = {".docx", ".pdf", ".txt", ".md"}


def read_docx(path: Path) -> str:
    import docx

    d = docx.Document(str(path))
    parts = [p.text for p in d.paragraphs if p.text.strip()]
    for table in d.tables:                      # 简历常用表格排版，别漏
        for row in table.rows:
            cells = [c.text.strip() for c in row.cells if c.text.strip()]
            if cells:
                parts.append(" | ".join(cells))
    return "\n".join(parts)


def read_pdf(path: Path) -> str:
    import fitz

    with fitz.open(path) as doc:
        return "\n".join(page.get_text("text") for page in doc)


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")


def read_any(path: str | Path, max_chars: int = 20000) -> str:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)
    suffix = p.suffix.lower()
    if suffix == ".docx":
        text = read_docx(p)
    elif suffix == ".pdf":
        text = read_pdf(p)
    elif suffix in (".txt", ".md"):
        text = read_text(p)
    else:
        raise ValueError(f"不支持的文件类型：{suffix}，支持 {sorted(SUPPORTED)}")
    return text[:max_chars]


def read_text_or_file(value: str, max_chars: int = 20000) -> str:
    """界面里用户可能直接粘贴文本，也可能给一个路径。"""
    v = (value or "").strip()
    if len(v) < 260 and Path(v).suffix.lower() in SUPPORTED and Path(v).exists():
        return read_any(v, max_chars)
    return v[:max_chars]
