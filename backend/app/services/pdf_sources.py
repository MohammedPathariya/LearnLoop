from dataclasses import dataclass
from datetime import datetime
import uuid


@dataclass(frozen=True)
class EphemeralSource:
    id: str
    session_id: str
    title: str
    text: str
    chunk_count: int
    created_at: str
    source_type: str = "pdf"


_sources: dict[str, dict[str, EphemeralSource]] = {}


def register_source(
    session_id: str,
    title: str,
    text: str,
    chunk_count: int,
    source_id: str | None = None,
) -> EphemeralSource:
    source = EphemeralSource(
        id=source_id or str(uuid.uuid4()),
        session_id=session_id,
        title=title,
        text=text,
        chunk_count=chunk_count,
        created_at=datetime.utcnow().isoformat(),
    )
    _sources.setdefault(session_id, {})[source.id] = source
    return source


def get_sources(session_id: str) -> list[EphemeralSource]:
    return list(_sources.get(session_id, {}).values())


def get_source(source_id: str) -> EphemeralSource | None:
    for sources in _sources.values():
        if source_id in sources:
            return sources[source_id]
    return None


def remove_source(source_id: str):
    source = get_source(source_id)
    if source is None:
        return
    _sources[source.session_id].pop(source_id, None)
    if not _sources[source.session_id]:
        _sources.pop(source.session_id)


def clear_sources(session_id: str | None = None):
    if session_id is None:
        _sources.clear()
    else:
        _sources.pop(session_id, None)
