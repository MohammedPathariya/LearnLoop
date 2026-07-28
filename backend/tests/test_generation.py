from types import SimpleNamespace
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.schemas import FlashcardOutput, QuizOutput, QuizQuestion
from app.services import generation


def completion(content):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=content))])


class FakeCompletions:
    def __init__(self, outputs):
        self.outputs = iter(outputs)
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        return completion(next(self.outputs))


class FakeClient:
    def __init__(self, outputs):
        self.chat = SimpleNamespace(completions=FakeCompletions(outputs))


VALID_QUIZ = '{"quiz": [{"type": "MCQ", "question": "Q?", "options": ["A", "B", "C", "D"], "correct_answer": "A", "explanation": "Because."}]}'
VALID_CARDS = '{"flashcards": [{"term": "FAISS", "definition": "A vector index."}]}'


def test_valid_quiz_output_is_returned(monkeypatch):
    monkeypatch.setattr(generation, "_client", FakeClient([VALID_QUIZ]))
    result = generation.generate_quiz(topic="retrieval", num_questions=1)
    assert result["quiz"][0]["correct_answer"] == "A"
    QuizOutput.model_validate(result)


def test_mcq_answers_are_normalized_and_empty_options_are_rejected():
    question = QuizQuestion.model_validate({
        "type": "MCQ",
        "question": "Q?",
        "options": [" A ", "B", "C", "D"],
        "correct_answer": "a",
        "explanation": "Because.",
    })
    assert question.correct_answer == "A"
    assert question.options[0] == "A"

    with pytest.raises(ValidationError):
        QuizQuestion.model_validate({
            "type": "MCQ",
            "question": "Q?",
            "options": ["", "B", "C", "D"],
            "correct_answer": "A",
            "explanation": "Because.",
        })


def test_whitespace_only_flashcard_fields_are_rejected():
    with pytest.raises(ValidationError):
        FlashcardOutput.model_validate({
            "flashcards": [{"term": " ", "definition": "Definition"}],
        })


def test_malformed_json_is_repaired(monkeypatch):
    client = FakeClient(['{"quiz": [', VALID_QUIZ])
    monkeypatch.setattr(generation, "_client", client)
    result = generation.generate_quiz(topic="retrieval", num_questions=1)
    assert result["quiz"]
    assert len(client.chat.completions.calls) == 2
    assert "Validation feedback" in client.chat.completions.calls[1]["messages"][1]["content"]


def test_schema_invalid_json_is_repaired(monkeypatch):
    invalid = '{"flashcards": [{"term": "FAISS"}]}'
    client = FakeClient([invalid, VALID_CARDS])
    monkeypatch.setattr(generation, "_client", client)
    result = generation.generate_flashcards("retrieval", num_cards=1)
    assert result == {"flashcards": [{"term": "FAISS", "definition": "A vector index."}]}
    with pytest.raises(ValidationError):
        FlashcardOutput.model_validate({"flashcards": [{"term": "FAISS"}]})


def test_retry_exhaustion_returns_clear_error(monkeypatch):
    client = FakeClient(["not json", "still not json", "nope"])
    monkeypatch.setattr(generation, "_client", client)
    result = generation.generate_flashcards("retrieval", num_cards=1)
    assert result["error"] == "Generated output failed validation after repair retries"
    assert result["raw_output"] == "nope"
    assert result["validation_attempts"] == 3
    assert len(client.chat.completions.calls) == generation.MAX_REPAIR_RETRIES + 1
