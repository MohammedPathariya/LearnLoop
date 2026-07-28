import json
import os
import re

from openai import OpenAI

_client = None


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

    resp = get_openai_client().chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt_source},
        ],
        max_tokens=800,
        temperature=0.7,
    )
    raw_text = resp.choices[0].message.content.strip()
    sanitized = re.sub(r",\s*]", "]", raw_text)
    sanitized = re.sub(r",\s*}", "}", sanitized)

    try:
        return json.loads(sanitized)
    except Exception:
        return {"error": "Failed to parse GPT output as JSON", "raw_output": raw_text}


def generate_flashcards(topic: str, num_cards: int = 5) -> dict:
    system_prompt = (
        "You are an AI flashcard generator. *Respond with only a JSON object and no extra text.*\n"
        f"Generate exactly {num_cards} flashcards for the topic: '{topic}'. "
        "Each flashcard should have a 'term' and a 'definition'. "
        "The definition should be clear and concise."
    )

    resp = get_openai_client().chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": topic},
        ],
        max_tokens=512,
        temperature=0.7,
    )
    raw = resp.choices[0].message.content.strip()

    if raw.startswith("```"):
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

    raw = re.sub(r",\s*]", "]", raw)
    raw = re.sub(r",\s*}", "}", raw)

    try:
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return {"flashcards": parsed}
        if isinstance(parsed, dict) and "flashcards" in parsed:
            return parsed
        return {"error": "Unexpected format", "raw_output": raw}
    except Exception:
        return {"error": "Failed to parse GPT output as JSON", "raw_output": raw}
