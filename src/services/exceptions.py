class ServiceError(Exception):
    """Base exception class for service errors."""

    pass


class EntityCreateError(ServiceError):
    """Raised when an entity cannot be created in the service layer."""

    def __init__(self, service_name: str, reason: str):
        """
        Initialize an EntityCreateError with a formatted error message.
        
        Constructs the error message using the provided service name and failure reason,
        indicating that the creation of an entity for the specified service has failed.
        """
        super().__init__(f"{service_name} failed to create entity. Reason: {reason}")


class EntityReadError(ServiceError):
    """Raised when an entity cannot be read in the service layer."""

    def __init__(self, service_name: str, reason: str):
        """
        Initialize an entity read error with the provided service name and failure reason.
        
        Args:
            service_name: The name of the service that encountered the read error.
            reason: A description explaining why the entity could not be read.
        """
        super().__init__(f"{service_name} failed to read entity. Reason: {reason}")


class EntityNotFoundError(ServiceError):
    """Raised when an entity cannot be found for a given operation, such as update or delete."""

    def __init__(self, service_name: str, read_param: str):
        """
        Initializes the EntityNotFoundError.
        
        Constructs an exception with a message indicating that an entity could not be found
        using the provided read parameters for the specified service.
        
        Args:
            service_name: The name of the service where the lookup was attempted.
            read_param: The parameters used to search for the entity.
        """
        super().__init__(
            f"{service_name} couldn't find entity with reading parameters: {read_param}."
        )


class EntityUpdateError(ServiceError):
    """Raised when an entity cannot be updated in the service layer."""

    def __init__(self, service_name: str, reason: str):
        """
        Initializes an EntityUpdateError with a formatted error message.
        
        Constructs an error message by combining the service name and a reason to indicate
        that updating an entity has failed.
        
        Args:
            service_name (str): Name of the service where the update failed.
            reason (str): Explanation of why the update operation failed.
        """
        super().__init__(f"{service_name} failed to update entity. Reason: {reason}")


class EntityDeleteError(ServiceError):
    """Raised when an entity cannot be deleted in the service layer."""

    def __init__(self, service_name: str, reason: str):
        """
        Initialize an EntityDeleteError with a formatted message.
        
        Args:
            service_name (str): Name of the service where the deletion error occurred.
            reason (str): Detailed explanation of why the deletion failed.
        """
        super().__init__(f"{service_name} failed to delete entity. Reason: {reason}")


class PermissionDeniedError(ServiceError):
    """Raised when an action is forbidden for the user."""

    def __init__(self, service_name: str, reason: str):
        """Initialize a PermissionDeniedError with a formatted error message.
        
        Constructs an exception message using the provided service name and reason,
        indicating that the attempted action is forbidden.
        """
        super().__init__(f"Forbidden in {service_name}. Reason: {reason}")
