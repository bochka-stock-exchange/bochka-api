from typing import Union


class RepositoryError(Exception):
    """Base exception class for repository errors."""

    pass


class EntityCreateError(RepositoryError):
    """Raised when an entity cannot be created."""

    def __init__(self, repo_name: str, table_name: str, reason: str):
        """Initialize an EntityCreateError instance.
        
        This exception is raised when an entity cannot be created. It formats an error
        message using the repository name, table name, and the specific reason for failure.
        
        Args:
            repo_name (str): The name of the repository where creation was attempted.
            table_name (str): The table in which the entity creation was attempted.
            reason (str): An explanation of why the entity could not be created.
        """
        super().__init__(f"{repo_name} failed to create entity in {table_name}. Reason: {reason}")


class EntityReadError(RepositoryError):
    """Raised when an entity cannot be read."""

    def __init__(
        self,
        repo_name: str,
        table_name: str,
        read_param: Union[int, str],
        reason: str,
    ):
        """
        Initialize an EntityReadError with contextual error details.
        
        Constructs an error message that specifies the repository, table, reading parameter,
        and the reason for the failure, and passes it to the base Exception class.
        
        Args:
            repo_name (str): Name of the repository where the read operation failed.
            table_name (str): Name of the table from which the entity was attempted to be read.
            read_param (Union[int, str]): Identifier or value used to specify the entity to read.
            reason (str): Explanation for why the read operation failed.
        """
        super().__init__(
            f"{repo_name} failed to read entity from {table_name} "
            f"with reading parameters: {read_param}. Reason: {reason}"
        )


class EntityUpdateError(RepositoryError):
    """Raised when an entity cannot be updated."""

    def __init__(
        self,
        repo_name: str,
        table_name: str,
        read_param: Union[int, str],
        reason: str,
    ):
        """
        Initializes an EntityUpdateError exception.
        
        This exception is raised when an update operation on an entity fails. It constructs an
        error message incorporating the repository name, table name, a parameter used to identify
        the entity, and the reason for the failure.
        
        Args:
            repo_name: Name of the repository where the update was attempted.
            table_name: Name of the table containing the entity.
            read_param: Identifier or parameter used to locate the target entity.
            reason: Explanation for why the update operation failed.
        """
        super().__init__(
            f"{repo_name} failed to update entity in {table_name} "
            f"with reading parameters: {read_param}. Reason: {reason}"
        )


class EntityDeleteError(RepositoryError):
    """Raised when an entity cannot be deleted."""

    def __init__(
        self,
        repo_name: str,
        table_name: str,
        read_param: Union[int, str],
        reason: str,
    ):
        """
        Initialize an EntityDeleteError instance with repository and error details.
        
        Args:
            repo_name: The name of the repository where the deletion was attempted.
            table_name: The name of the table or collection involved.
            read_param: The value used to identify the entity.
            reason: A description explaining why the deletion failed.
        """
        super().__init__(
            f"{repo_name} failed to delete entity in {table_name} "
            f"with reading parameters: {read_param}. Reason: {reason}"  #
        )
