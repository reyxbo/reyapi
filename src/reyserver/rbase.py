# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-07-17
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Base methods.
"""


from typing import Sequence
from inspect import iscoroutinefunction
from contextlib import asynccontextmanager
from fastapi import FastAPI
from reykit.rbase import CoroutineFunctionSimple, Base, ConfigMeta

from . import rserver


__all__ = (
    'ServerBase',
    'ServerConfig',
    'create_lifespan',
    'create_depend_sess'
)


class ServerBase(Base):
    """
    Server base type.
    """


class ServerConfig(ServerBase, metaclass=ConfigMeta):
    """
    Config type.
    """

    server: 'rserver.Server'
    'Server instance.'


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


def create_depend_sess(database: str):
    """
    Create dependencie function of asynchronous database session.

    Parameters
    ----------
    database : Database name.

    Returns
    -------
    Dependencie function.
    """


    async def depend_sess():
        """
        Dependencie function of asynchronous database session.
        """

        # Parameter.
        engine = ServerConfig.server.db[database]

        # Context.
        async with engine.orm.session() as sess:
            yield sess


    return depend_sess
