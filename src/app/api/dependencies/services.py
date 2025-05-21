from typing import Annotated

from fastapi import Depends

from src.app import services

Users = Annotated[services.Users, Depends()]
Instruments = Annotated[services.Instruments, Depends()]
Auth = Annotated[services.Authentication, Depends()]
