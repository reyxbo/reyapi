# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-07-17
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Base methods.
"""


from typing import Sequence, Literal
from inspect import iscoroutinefunction
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from reykit.rbase import CoroutineFunctionSimple, Base, ConfigMeta, Exit

from . import rserver


__all__ = (
    'ServerBase',
    'ServerConfig',
    'ServerExit',
    'ServerExitHTTP',
    'ServerExitHTTP404',
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


class ServerExit(ServerBase, Exit):
    """
    Server exit type.
    """


class ServerExitHTTP(ServerExit, HTTPException):
    """
    Server HTTP exit type.
    """

    status_code: int


    def __init__(self, text: str | None = None):
        """
        Build instance attributes.

        Parameters
        ----------
        text : Explain text.
        """

        # Super.
        super().__init__(self.status_code, text)


class ServerExitHTTP404(ServerExitHTTP):
    """
    Server HTTP 404 exit type.
    """

    status_code = status.HTTP_404_NOT_FOUND


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


def create_depend_db(database: str, mode: Literal['sess', 'conn']):
    """
    Create dependencie function of asynchronous database.

    Parameters
    ----------
    database : Database name.
    mode : Mode.
        - `Literl['sess']`: Create ORM session instance.
        - `Literl['conn']`: Create connection instance.

    Returns
    -------
    Dependencie function.
    """


    async def depend():
        """
        Dependencie function of asynchronous database.
        """

        # Parameter.
        engine = ServerConfig.server.db[database]

        # Context.
        if mode == 'sess':
            async with engine.orm.session() as sess:
                yield sess
        elif mode == 'conn':
            async with engine.connect() as conn:
                yield conn


    return depend
