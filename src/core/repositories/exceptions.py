class RepositoryError(Exception):
    """Base exception class for repository errors."""


class EntityCreateError(RepositoryError):
    """Raised when an entity cannot be created."""

    def __init__(self, repo_name: str, table_name: str, reason: str):
        super().__init__(f"{repo_name} failed to create entity in {table_name}. Reason: {reason}")


class EntityReadError(RepositoryError):
    """Raised when an entity cannot be read."""

    def __init__(
        self,
        repo_name: str,
        table_name: str,
        identifier: int | str,
        reason: str,
    ):
        super().__init__(
            f"{repo_name} failed to read entity from {table_name} "
            f"with ID: {identifier}. Reason: {reason}",
        )


class EntityUpdateError(RepositoryError):
    """Raised when an entity cannot be updated."""

    def __init__(
        self,
        repo_name: str,
        table_name: str,
        identifier: int | str,
        reason: str,
    ):
        super().__init__(
            f"{repo_name} failed to update entity in {table_name} "
            f"with ID: {identifier}. Reason: {reason}",
        )


class EntityDeleteError(RepositoryError):
    """Raised when an entity cannot be deleted."""

    def __init__(
        self,
        repo_name: str,
        table_name: str,
        identifier: int | str,
        reason: str,
    ):
        super().__init__(
            f"{repo_name} failed to delete entity in {table_name} "
            f"with ID: {identifier}. Reason: {reason}",
        )


class DatabaseError(RepositoryError):
    """Database error 500 status code"""

    def __init__(self, repo_name: str, reason: str):
        super().__init__(f"{repo_name} had a database error. Reason: {reason}")
