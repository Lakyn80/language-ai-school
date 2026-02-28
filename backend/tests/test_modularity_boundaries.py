from pathlib import Path


def test_comprehension_does_not_depend_on_lessons_cache():
    base = Path("backend/app/pedagogy/comprehension")

    for file in base.glob("*.py"):
        content = file.read_text(encoding="utf-8")
        assert "app.modules.lessons.cache" not in content
