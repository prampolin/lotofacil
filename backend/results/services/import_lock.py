"""Session advisory lock shared by all three CLI entrypoints, without migrations."""

import logging
import sys
from contextlib import contextmanager
from contextvars import ContextVar
from functools import wraps

from django.core.management.base import CommandError
from django.db import DatabaseError, connection

LOCK_ID = 710110233
_depth = ContextVar("lotofacil_import_depth", default=0)


@contextmanager
def import_lock():
    if _depth.get():
        yield
        return
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_try_advisory_lock(%s)", [LOCK_ID])
        if not cursor.fetchone()[0]:
            raise CommandError("Outro importador está em execução; tente mais tarde.")
    token = _depth.set(1)
    try:
        yield
    finally:
        _depth.reset(token)
        # A broken transaction cannot run unlock SQL; closing releases session locks.
        if connection.needs_rollback:
            connection.close()
        elif connection.connection is not None:
            original_error = sys.exc_info()[0] is not None
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_advisory_unlock(%s)", [LOCK_ID])
            except DatabaseError:
                connection.close()
                if not original_error:
                    raise
                logging.getLogger(__name__).exception("Failed to release import lock")


def serialized_import(function):
    @wraps(function)
    def wrapped(*args, **kwargs):
        with import_lock():
            return function(*args, **kwargs)

    return wrapped
