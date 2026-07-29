create extension if not exists pgcrypto;

create table public.profiles (
    id uuid primary key references auth.users(id) on delete cascade,
    display_name text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table public.learning_sessions (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    title text not null check (length(btrim(title)) > 0),
    domain text,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table public.study_messages (
    id bigint generated always as identity primary key,
    user_id uuid not null references auth.users(id) on delete cascade,
    session_id uuid not null references public.learning_sessions(id) on delete cascade,
    role text not null check (role in ('user', 'assistant')),
    content text not null,
    grounded boolean not null default false,
    source_refs jsonb not null default '[]'::jsonb,
    retrieval_latency_ms double precision,
    created_at timestamptz not null default now()
);

create table public.quiz_results (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    session_id uuid references public.learning_sessions(id) on delete set null,
    topic text,
    num_questions integer not null check (num_questions > 0),
    quiz jsonb not null,
    user_answers jsonb not null,
    correct_answers jsonb not null,
    score integer not null check (score >= 0 and score <= num_questions),
    created_at timestamptz not null default now()
);

create table public.flashcard_sets (
    id uuid primary key default gen_random_uuid(),
    user_id uuid not null references auth.users(id) on delete cascade,
    session_id uuid references public.learning_sessions(id) on delete set null,
    topic text not null,
    cards jsonb not null,
    created_at timestamptz not null default now()
);

create index learning_sessions_user_updated_idx
    on public.learning_sessions (user_id, updated_at desc);

create index study_messages_user_session_created_idx
    on public.study_messages (user_id, session_id, created_at);

create index quiz_results_user_created_idx
    on public.quiz_results (user_id, created_at desc);

create index flashcard_sets_user_created_idx
    on public.flashcard_sets (user_id, created_at desc);

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

create trigger profiles_set_updated_at
before update on public.profiles
for each row execute function public.set_updated_at();

create trigger learning_sessions_set_updated_at
before update on public.learning_sessions
for each row execute function public.set_updated_at();

create or replace function public.handle_new_user()
returns trigger
language plpgsql
security definer set search_path = public
as $$
begin
    insert into public.profiles (id, display_name)
    values (new.id, nullif(new.raw_user_meta_data ->> 'display_name', ''));
    return new;
end;
$$;

create trigger on_auth_user_created
after insert on auth.users
for each row execute function public.handle_new_user();

alter table public.profiles enable row level security;
alter table public.learning_sessions enable row level security;
alter table public.study_messages enable row level security;
alter table public.quiz_results enable row level security;
alter table public.flashcard_sets enable row level security;

create policy "Users can view their own profile"
on public.profiles for select to authenticated
using ((select auth.uid()) = id);

create policy "Users can update their own profile"
on public.profiles for update to authenticated
using ((select auth.uid()) = id)
with check ((select auth.uid()) = id);

create policy "Users can manage their own learning sessions"
on public.learning_sessions for all to authenticated
using ((select auth.uid()) = user_id)
with check ((select auth.uid()) = user_id);

create policy "Users can manage their own study messages"
on public.study_messages for all to authenticated
using (
    (select auth.uid()) = user_id
    and exists (
        select 1
        from public.learning_sessions
        where learning_sessions.id = study_messages.session_id
          and learning_sessions.user_id = (select auth.uid())
    )
)
with check (
    (select auth.uid()) = user_id
    and exists (
        select 1
        from public.learning_sessions
        where learning_sessions.id = study_messages.session_id
          and learning_sessions.user_id = (select auth.uid())
    )
);

create policy "Users can manage their own quiz results"
on public.quiz_results for all to authenticated
using ((select auth.uid()) = user_id)
with check (
    (select auth.uid()) = user_id
    and (
        session_id is null
        or exists (
            select 1
            from public.learning_sessions
            where learning_sessions.id = quiz_results.session_id
              and learning_sessions.user_id = (select auth.uid())
        )
    )
);

create policy "Users can manage their own flashcard sets"
on public.flashcard_sets for all to authenticated
using ((select auth.uid()) = user_id)
with check (
    (select auth.uid()) = user_id
    and (
        session_id is null
        or exists (
            select 1
            from public.learning_sessions
            where learning_sessions.id = flashcard_sets.session_id
              and learning_sessions.user_id = (select auth.uid())
        )
    )
);
