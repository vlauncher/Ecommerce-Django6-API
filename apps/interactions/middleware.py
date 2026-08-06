from apps.users.auth import decode_jwt_token
from apps.users.selectors import aget_user_by_id


class JWTWebSocketMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        scope = dict(scope)
        scope["user"] = None
        headers = dict(scope.get("headers", []))
        raw = headers.get(b"authorization", b"").decode()
        if raw.lower().startswith("bearer "):
            try:
                payload = decode_jwt_token(raw.split(" ", 1)[1])
                scope["user"] = await aget_user_by_id(payload.get("user_id"))
            except Exception:
                scope["user"] = None
        return await self.app(scope, receive, send)
