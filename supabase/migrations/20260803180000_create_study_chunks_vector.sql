create extension if not exists vector;

create table if not exists public.study_chunk (
    id text primary key,
    session_id text not null,
    source_id text not null,
    chunk_index integer not null check (chunk_index >= 0),
    text text not null,
    token_count integer not null default 0 check (token_count >= 0),
    embedding vector(384) not null,
    created_at timestamptz not null default now(),
    unique (session_id, source_id, chunk_index)
);

create index if not exists study_chunk_session_idx
    on public.study_chunk (session_id);

comment on table public.study_chunk is
    'Durable LearnLoop RAG chunks and MiniLM embeddings. Access is enforced by the Flask API in the current deployment.';
