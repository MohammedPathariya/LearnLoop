import json
import os
from collections.abc import Callable
from typing import TypeVar

from openai import OpenAI
from pydantic import BaseModel, ValidationError

from ..schemas import FlashcardOutput, QuizOutput

_client = None
T = TypeVar("T", bound=BaseModel)
MAX_REPAIR_RETRIES = 2


def _strip_json_fence(raw_output: str) -> str:
    text = raw_output.strip()
    if text.startswith("```"):
        first_line, separator, remainder = text.partition("\n")
        if separator and first_line[3:].strip().lower() in {"", "json"}:
            text = remainder
        if text.rstrip().endswith("```"):
            text = text.rstrip()[:-3]
    return text.strip()


def _validation_feedback(error: Exception) -> str:
    if isinstance(error, ValidationError):
        return json.dumps(error.errors(), ensure_ascii=True)
    return str(error)


def _generate_validated_output(
    *,
    system_prompt: str,
    user_prompt: str,
    schema: type[T],
    normalize: Callable[[object], object],
    expected_count: int,
    max_retries: int = MAX_REPAIR_RETRIES,
) -> dict:
    prompt = user_prompt
    raw_output = ""
    last_error = ""
    attempts = 0

    for attempt in range(max_retries + 1):
        attempts = attempt + 1
        response = get_openai_client().chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            max_tokens=800,
            temperature=0.7,
        )
        raw_output = response.choices[0].message.content.strip()
        try:
            parsed = json.loads(_strip_json_fence(raw_output))
            validated = schema.model_validate(normalize(parsed))
            items = validated.quiz if isinstance(validated, QuizOutput) else validated.flashcards
            if len(items) != expected_count:
                raise ValueError(f"Expected exactly {expected_count} items, got {len(items)}")
            return validated.model_dump(exclude_none=True)
        except (json.JSONDecodeError, ValidationError, TypeError, ValueError) as error:
            last_error = _validation_feedback(error)
            if attempt < max_retries:
                prompt = (
                    f"{user_prompt}\n\nYour previous output was invalid. "
                    "Return only corrected JSON matching the requested shape. "
                    f"Validation feedback: {last_error}\n"
                    f"Previous output: {raw_output}"
                )

    return {
        "error": "Generated output failed validation after repair retries",
        "raw_output": raw_output,
        "validation_errors": last_error,
        "validation_attempts": attempts,
    }


def get_openai_client():
    global _client

    if _client is not None:
        return _client

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY in environment")

    _client = OpenAI(api_key=api_key)
    return _client


def generate_convo(topic: str, turns=3, style="natural", mode="student-first") -> str:
    style_desc = {
        "natural": "in a friendly, conversational tone",
        "formal": "in a formal, academic tone",
        "humorous": "with light humor and wit",
        "technical": "with precise, technical language",
    }.get(style, "in a friendly, conversational tone")

    starter = {
        "student-first": "The student starts by asking about the topic.",
        "teacher-first": "The teacher begins with a question or prompt to the student.",
    }[mode]

    system_prompt = (
        f"You are simulating a {style_desc} conversation between a curious student and a knowledgeable teacher. "
        f"{starter} "
        f"Have exactly {turns} back-and-forth exchanges (so {turns*2} messages), "
        "and end with a warm wrap-up."
    )

    resp = get_openai_client().chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Topic: {topic}"},
        ],
        max_tokens=512,
        temperature=0.8,
    )
    return resp.choices[0].message.content.strip()


def generate_quiz(content: str = None, topic: str = None, num_questions: int = 5) -> dict:
    if content:
        prompt_source = f"Here is a piece of content:\n\n{content}\n\n"
    else:
        prompt_source = f"Create a quiz about the following topic:\n\n{topic}\n\n"

    system_prompt = (
        "You are an AI quiz generator. *Respond with exactly one JSON object and nothing else--no additional text.*\n"
        f"Produce exactly {num_questions} questions in JSON format. "
        "Include a mix of MCQ, True/False, and Fill-in-the-blank questions. "
        "For each question, provide:\n"
        '  * type ("MCQ" / "True/False" / "Fill-in-the-blank"),\n'
        "  * question text,\n"
        "  * for MCQ: a list of exactly 4 options and the correct answer letter,\n"
        '  * for True/False: answer "True" or "False",\n'
        "  * for Fill-in-the-blank: the correct word/phrase,\n"
        "  * a short explanation (rationale) for the correct answer.\n"
        'Return a single JSON object with one key "quiz" whose value is a list of those question objects.'
    )

    return _generate_validated_output(
        system_prompt=system_prompt,
        user_prompt=prompt_source,
        schema=QuizOutput,
        normalize=lambda parsed: parsed,
        expected_count=num_questions,
    )


def generate_flashcards(
    topic: str | None = None,
    num_cards: int = 5,
    content: str | None = None,
) -> dict:
    subject = topic.strip() if topic else "the provided study material"
    source_prompt = (
        f"Create flashcards using only this study material:\n\n{content}"
        if content
        else subject
    )
    system_prompt = (
        "You are an AI flashcard generator. *Respond with only a JSON object and no extra text.*\n"
        f"Generate exactly {num_cards} flashcards about {subject}. "
        "Each flashcard should have a 'term' and a 'definition'. "
        "The definition should be clear and concise."
    )

    return _generate_validated_output(
        system_prompt=system_prompt,
        user_prompt=source_prompt,
        schema=FlashcardOutput,
        normalize=lambda parsed: {"flashcards": parsed} if isinstance(parsed, list) else parsed,
        expected_count=num_cards,
    )


def generate_grounded_answer(question: str, chunks: list[dict]) -> str:
    if not chunks:
        return "I do not have enough source material in this session to answer that."

    sources = "\n\n".join(
        f"[Source {index + 1}: {chunk['source_id']} chunk {chunk['chunk_index']}]\n{chunk['text']}"
        for index, chunk in enumerate(chunks)
    )
    system_prompt = (
        "Answer the student's question using only the provided source chunks. "
        "If the chunks do not contain the answer, say that the source material does not provide enough information. "
        "Cite sources inline with the provided source numbers."
    )

    resp = get_openai_client().chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Question: {question}\n\nSource chunks:\n{sources}"},
        ],
        max_tokens=512,
        temperature=0.2,
    )
    return resp.choices[0].message.content.strip()
