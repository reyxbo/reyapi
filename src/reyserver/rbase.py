# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-07-17 22:32:37
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Base methods.
"""


from typing import Sequence
from inspect import iscoroutinefunction
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends

from reydb import DatabaseAsync
from reydb.rconn import DatabaseConnectionAsync
from reydb.rorm import DatabaseORMSessionAsync
from reykit.rbase import CoroutineFunctionSimple, Base, is_iterable


__all__ = (
    'ServerBase',
    'ServerAPI',
    'create_lifespan'
)


class ServerBase(Base):
    """
    Server base type.
    """


class ServerAPI(ServerBase):
    """
    Server API type.
    """


def create_lifespan(
    before: CoroutineFunctionSimple | Sequence[CoroutineFunctionSimple] | None = None,
    after: CoroutineFunctionSimple | Sequence[CoroutineFunctionSimple] | None = None,
):
    """
    Create function of lifespan manager.

    Parameters
    ----------
    before : Execute before server start.
    after : Execute after server end.
    """

    # Parameter.
    if before is None:
        before = ()
    elif iscoroutinefunction(before):
        before = (before,)
    if after is None:
        after = ()
    elif iscoroutinefunction(after):
        after = (after,)


    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """
        Server lifespan manager.

        Parameters
        ----------
        app : Server APP.
        """

        # Before.
        for task in before:
            await task()
        yield

        # After.
        for task in after:
            await after()


    return lifespan


# def create_depend_conn(db: DatabaseAsync):
#     """
#     Create dependencie function of asynchronous database connection.

#     Parameters
#     ----------
#     db : Asynchronous database instance.
#     """


#     @asynccontextmanager
#     async def lifespan(app: FastAPI):
#         """
#         Server lifespan manager.

#         Parameters
#         ----------
#         app : Server APP.
#         """

#         # Before.
#         for task in before:
#             await task()
#         yield

#         # After.
#         for task in after:
#             await after()


#     return lifespan
