import logging

from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_fixed,
    wait_random,
)

from src import core


def is_unexpected_error(exception: BaseException) -> bool:
    if not (
        isinstance(
            exception,
            core.repositories.exceptions.RepositoryError | core.services.exceptions.ServiceError,
        )
    ):
        logger = logging.getLogger("retry")
        logger.error("Retry error", extra={"original_error": str(exception)})
        return True
    return False


def retry_on_serialization():
    return retry(
        reraise=False,
        stop=stop_after_attempt(5),
        wait=wait_fixed(0.1) + wait_random(0.3, 1),
        retry=retry_if_exception(is_unexpected_error),
    )
