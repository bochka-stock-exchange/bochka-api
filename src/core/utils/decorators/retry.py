from sqlalchemy.exc import OperationalError, DBAPIError
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential
import asyncpg


def is_retryable_db_error(exc: BaseException) -> bool:
    if isinstance(exc, (OperationalError, DBAPIError)):
        orig = getattr(exc, "orig", None)
        if isinstance(orig, asyncpg.exceptions.SerializationError):
            return True
        if isinstance(orig, asyncpg.exceptions.DeadlockDetectedError):
            return True
        if isinstance(orig, asyncpg.exceptions.LockNotAvailableError):
            return True
        if isinstance(orig, asyncpg.exceptions.InFailedSQLTransactionError):
            return True
    if isinstance(exc, asyncpg.exceptions.LockNotAvailableError):
        return True
    if isinstance(exc, asyncpg.exceptions.InFailedSQLTransactionError):
        return True

    if hasattr(exc, "__cause__") and exc.__cause__ is not None:
        return is_retryable_db_error(exc.__cause__)

    return False
