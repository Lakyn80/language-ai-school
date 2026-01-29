from app.modules.lessons.schema import LessonResponse


def test_valid_schema():
    data = {
        "level": "A2",
        "story": "Short story.",
        "vocabulary": [
            {"word": "tree", "meaning": "a plant"}
        ],
        "questions": ["What happened?"],
        "writing_task": "Write 3 sentences."
    }

    lesson = LessonResponse(**data)

    assert lesson.level == "A2"
    assert len(lesson.vocabulary) == 1
    assert lesson.vocabulary[0].word == "tree"
