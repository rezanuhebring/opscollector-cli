from __future__ import annotations

import secrets
import hashlib
from datetime import datetime

from sqlalchemy import select

from server.db import SessionLocal
from server.models import Client


def issue_token(client_id: str, client_name: str | None = None) -> str:
    """Issue a new token for client_id and return the plaintext token."""
    token = secrets.token_hex(16)
    digest = hashlib.sha256(token.encode()).hexdigest()

    with SessionLocal() as db:
        client = db.get(Client, client_id)
        now = datetime.utcnow()
        if not client:
            client = Client(
                client_id=client_id,
                name=client_name,
                api_token=digest,
                token_issued_at=now,
            )
            db.add(client)
        else:
            client.api_token = digest
            client.token_issued_at = now
            client.token_rotated_at = None
            client.revoked = False
        db.commit()
    return token


def validate_token(bearer: str | None):
    if bearer is None or not bearer.strip():
        return None
    token = bearer.strip()
    if " " in token:
        token = token.split(" ", 1)[-1].strip()
    digest = hashlib.sha256(token.encode()).hexdigest()

    with SessionLocal() as db:
        client = db.scalar(select(Client).where(Client.api_token == digest, Client.revoked.is_(False)))
        return client


def rotate_token(client_id: str) -> str:
    with SessionLocal() as db:
        client = db.get(Client, client_id)
        if not client:
            raise ValueError("client not found")
        if client.revoked:
            raise ValueError("client revoked")
        token = secrets.token_hex(16)
        client.api_token = hashlib.sha256(token.encode()).hexdigest()
        client.token_issued_at = datetime.utcnow()
        client.token_rotated_at = datetime.utcnow()
        db.commit()
    return token


def revoke(client_id: str) -> None:
    with SessionLocal() as db:
        client = db.get(Client, client_id)
        if not client:
            return
        client.revoked = True
        db.commit()
