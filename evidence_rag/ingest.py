"""Deterministic Markdown ingestion with line-level provenance."""

from dataclasses import asdict, dataclass
from hashlib import sha256
from pathlib import Path


@dataclass(frozen=True)
class Chunk:
    id: str
    source: str
    line_start: int
    line_end: int
    text: str

    @property
    def citation(self) -> str:
        return f"{self.source}:L{self.line_start}-L{self.line_end}"

    def to_dict(self) -> dict:
        return asdict(self)


def ingest(root: Path | str, max_chars: int = 320, overlap_lines: int = 1) -> list[Chunk]:
    """Read .md files only. IDs encode relative path, line range, and content.

    Long lines are divided into pieces retaining the same original line number.
    Overlap counts line pieces, and always advances by at least one piece.
    Symlinks escaping the supplied corpus root are ignored.
    """
    root = Path(root).resolve()
    if not root.is_dir():
        raise ValueError(f"Corpus directory does not exist: {root}")
    if max_chars < 80 or overlap_lines < 0:
        raise ValueError("max_chars must be >= 80 and overlap_lines >= 0")
    chunks: list[Chunk] = []
    for path in sorted(root.rglob("*.md")):
        if not path.resolve().is_relative_to(root) or not path.is_file():
            continue
        source = path.relative_to(root).as_posix()
        pieces: list[tuple[int, str]] = []
        for line_no, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
            if not line.strip():
                pieces.append((line_no, ""))
            else:
                pieces.extend((line_no, line[i:i + max_chars]) for i in range(0, len(line), max_chars))
        start = 0
        while start < len(pieces):
            end, length = start, 0
            while end < len(pieces):
                cost = len(pieces[end][1]) + int(end > start)
                if end > start and length + cost > max_chars:
                    break
                length += cost
                end += 1
            text = "\n".join(part for _, part in pieces[start:end]).strip()
            if text:
                first, last = pieces[start][0], pieces[end - 1][0]
                digest = sha256(f"{source}\0{first}\0{last}\0{text}".encode()).hexdigest()[:16]
                chunks.append(Chunk(digest, source, first, last, text))
            if end == len(pieces):
                break
            start = max(start + 1, end - overlap_lines)
    return chunks
