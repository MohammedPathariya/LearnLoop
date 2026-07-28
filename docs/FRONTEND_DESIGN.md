# LearnLoop Frontend Design

This document records the implemented Day 6 design system and product boundaries.

## Brand

- Wordmark: `learnloop`
- Mark: open book with a centered four-point compass star
- Theme: light
- Page background: `#F4F2EC`
- Surface: `#FFFFFF`
- Learner accent: aurora ivy `#1F4D33`
- Primary text: `#2C2C2A`
- Secondary text: `#5F5E5A`
- Muted text: `#888780`
- Border: `#DBE4DC`
- Correct: teal `#0F6E56`
- Incorrect: coral `#993C1D`
- Warning: amber `#854F0B`
- Technical benchmark accent: blue `#185FA5`

Cards use a thin border, 12px radius, and no shadow or gradient. Aurora ivy
means learner-facing brand or action state. It must not mean a correct answer.

## Information Architecture

- Home
- Learn
- Progress
- History
- Benchmarks
- System information

Home, Learn, and Progress are the primary navigation. History, Benchmarks,
System information, and the GitHub repository live under More. Materials,
quizzes, and flashcards are contextual modes inside Learn rather than competing
top-level destinations.

The avatar was removed because the product has no authentication. System
information contains app-level status and demo reset controls, not account
settings.

## Product Flow

The primary flow is:

`Home -> Study journey -> Add material -> Ask grounded question -> Inspect sources -> Generate quiz -> Review result -> Generate flashcards -> View progress`

Study replaces the old ThinkMate dialogue interface. It uses persistent study
sessions and source-grounded question answering.

## Honesty Rules

- Grounded answers display a source-count indicator. Ungrounded answers do not.
- Text paste is the only material input. File upload is not shown as available.
- Flashcard review supports flip, previous, and next. Knowledge tracking is
  labeled as coming soon.
- Progress uses saved quiz scores and topic-level averages. It does not claim
  concept mastery.
- Benchmarks show checked-in measured results and the local-only load-test
  limitation inline.
- Learner screens avoid exposing vector-search implementation terminology.

## Demo Journey

The public demo is Machine Learning Foundations. It includes:

- three seeded study materials
- grounded conversation history
- three quiz attempts with a real score trend
- one flashcard set
- strong and weak topics derived from saved quiz scores
- an isolated browser-scoped copy for each visitor
- a reset action that restores the canonical seed

The demo does not represent a user account. A random browser identifier keeps
each visitor's persistent sessions separate without implying authentication.

## Responsive Behavior

Desktop uses Home, Learn, Progress, and More in the top navigation. Mobile uses
Home, Learn, Progress, and More in a bottom navigation bar. The Learn workspace
shows one primary task at a time, while materials and supporting evidence open
contextually. Its panels stack into touch-friendly sections on narrow screens.
