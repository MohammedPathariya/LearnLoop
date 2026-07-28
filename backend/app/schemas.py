from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class QuizQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)

    type: Literal["MCQ", "True/False", "Fill-in-the-blank"]
    question: str = Field(min_length=1)
    options: list[str] | None = Field(default=None, min_length=4, max_length=4)
    correct_answer: str = Field(min_length=1)
    explanation: str = Field(min_length=1)

    @model_validator(mode="before")
    @classmethod
    def normalize_fields(cls, data):
        if not isinstance(data, dict):
            return data
        normalized = dict(data)
        if isinstance(normalized.get("options"), list):
            normalized["options"] = [
                option.strip() if isinstance(option, str) else option
                for option in normalized["options"]
            ]
        if isinstance(normalized.get("correct_answer"), str):
            answer = normalized["correct_answer"].strip()
            if normalized.get("type") == "MCQ":
                answer = answer.upper()
            normalized["correct_answer"] = answer
        return normalized

    @model_validator(mode="after")
    def validate_type_specific_fields(self):
        if self.type == "MCQ":
            if self.options is None or len(self.options) != 4:
                raise ValueError("MCQ questions require exactly four options")
            if any(not option for option in self.options):
                raise ValueError("MCQ options must not be empty")
            if self.correct_answer.upper() not in {"A", "B", "C", "D"}:
                raise ValueError("MCQ correct_answer must be A, B, C, or D")
        elif self.type == "True/False":
            if self.options is not None:
                raise ValueError("True/False questions must not include options")
            if self.correct_answer not in {"True", "False"}:
                raise ValueError("True/False correct_answer must be True or False")
        elif self.options is not None:
            raise ValueError("Fill-in-the-blank questions must not include options")
        return self


class QuizOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)

    quiz: list[QuizQuestion] = Field(min_length=1)


class Flashcard(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)

    term: str = Field(min_length=1)
    definition: str = Field(min_length=1)


class FlashcardOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, str_strip_whitespace=True)

    flashcards: list[Flashcard] = Field(min_length=1)
