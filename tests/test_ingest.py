from pathlib import Path

import pytest

from evidence_rag.ingest import ingest


def test_source_spans_are_real_and_ids_change_with_content(tmp_path):
    path = tmp_path / "note.md"
    path.write_text("# 标题\n\nalpha checkpoint\n中间内容\n", encoding="utf-8-sig")
    original = ingest(tmp_path)
    assert len(original) == 1
    chunk = original[0]
    lines = path.read_text(encoding="utf-8-sig").splitlines()
    assert chunk.text == "\n".join(lines[chunk.line_start - 1:chunk.line_end]).strip()
    assert chunk.source == "note.md" and chunk.citation == "note.md:L1-L4"
    assert ingest(tmp_path) == original
    path.write_text("# 标题\n\nchanged checkpoint\n中间内容\n", encoding="utf-8")
    assert ingest(tmp_path)[0].id != chunk.id


def test_long_line_has_bounded_chunks_and_original_line_numbers(tmp_path):
    (tmp_path / "long.md").write_text("a" * 601 + "\n" + "b" * 160, encoding="utf-8")
    chunks = ingest(tmp_path, max_chars=80, overlap_lines=2)
    assert chunks and all(len(c.text) <= 80 for c in chunks)
    assert all(c.line_start in (1, 2) and c.line_end in (1, 2) for c in chunks)
    assert len(chunks) < 30  # A large overlap must never prevent progress.
    assert "a" * 80 in chunks[0].text


def test_only_markdown_and_empty_files(tmp_path):
    (tmp_path / "empty.md").write_text("\n \n", encoding="utf-8")
    (tmp_path / "secret.txt").write_text("ignore this", encoding="utf-8")
    assert ingest(tmp_path) == []


def test_external_symlink_ignored(tmp_path):
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    outside = tmp_path / "outside.md"
    outside.write_text("outside confidential", encoding="utf-8")
    try:
        (corpus / "link.md").symlink_to(outside)
    except OSError:
        pytest.skip("Symlink creation requires developer mode on some Windows hosts")
    assert ingest(corpus) == []


@pytest.mark.parametrize("kwargs", [{"max_chars": 0}, {"overlap_lines": -1}])
def test_invalid_chunk_config(tmp_path, kwargs):
    with pytest.raises(ValueError):
        ingest(tmp_path, **kwargs)
