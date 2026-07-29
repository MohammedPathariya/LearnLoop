import os

import httpx
from flask import g, request


def register_auth(app):
    @app.before_request
    def load_authenticated_user():
        g.learnloop_user = None
        authorization = request.headers.get("Authorization", "")
        if not authorization:
            return None
        if not authorization.startswith("Bearer "):
            return {"error": "Authorization must use a Bearer token"}, 401

        token = authorization.removeprefix("Bearer ").strip()
        user = verify_access_token(token)
        if user is None:
            return {"error": "Invalid or expired authentication token"}, 401
        g.learnloop_user = user
        return None

    @app.get("/auth/me")
    def auth_me():
        user = getattr(g, "learnloop_user", None)
        if user is None:
            return {"authenticated": False}, 200
        return {
            "authenticated": True,
            "id": user["id"],
            "email": user.get("email"),
        }, 200


def verify_access_token(token):
    supabase_url = os.getenv("SUPABASE_URL", "").rstrip("/")
    publishable_key = os.getenv("SUPABASE_PUBLISHABLE_KEY", "")
    if not supabase_url or not publishable_key:
        return None

    try:
        response = httpx.get(
            f"{supabase_url}/auth/v1/user",
            headers={
                "apikey": publishable_key,
                "Authorization": f"Bearer {token}",
            },
            timeout=5,
        )
    except httpx.HTTPError:
        return None

    if response.status_code != 200:
        return None
    user = response.json()
    return user if isinstance(user, dict) and user.get("id") else None


def current_user():
    return getattr(g, "learnloop_user", None)
