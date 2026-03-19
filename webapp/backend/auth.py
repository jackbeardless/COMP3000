"""
JWT authentication dependency for FastAPI routes.

The frontend sends the Supabase access token in the Authorization header.
We verify it by asking Supabase's auth API, which returns the user object.
"""
import asyncio
from fastapi import Header, HTTPException
from database import get_admin_client


async def get_current_user(authorization: str = Header(...)) -> dict:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header.")
    token = authorization[7:]
    loop = asyncio.get_event_loop()
    try:
        admin = get_admin_client()
        resp = await loop.run_in_executor(None, lambda: admin.auth.get_user(token))
        return {"id": resp.user.id, "email": resp.user.email}
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token.")
