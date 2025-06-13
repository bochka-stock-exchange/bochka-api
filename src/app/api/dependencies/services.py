from typing import Annotated

from fastapi import Depends

from src.app import services

Users = Annotated[services.Users, Depends()]
Instruments = Annotated[services.Instruments, Depends()]
Auth = Annotated[services.Authentication, Depends()]
Balances = Annotated[services.Balances, Depends()]
Orders = Annotated[services.Orders, Depends()]
Transactions = Annotated[services.Transactions, Depends()]
