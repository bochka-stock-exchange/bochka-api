from sqlalchemy.exc import OperationalError
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_exponential


def is_serialization_failure(exception: BaseException) -> bool:
    if isinstance(exception, OperationalError):
        orig = getattr(exception, "orig", None)

        if orig and getattr(orig, "pgcode", None) == "40001":
            return True

        return "40001" in str(exception)
    return False


def retry_on_serialization():
    return retry(
        reraise=False,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=0.1, min=0.1, max=1),
        retry=retry_if_exception(is_serialization_failure),
    )
