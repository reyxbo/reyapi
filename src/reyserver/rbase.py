# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-07-17
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Base methods.
"""


from typing import Sequence, Literal, NoReturn
from inspect import iscoroutinefunction
from contextlib import asynccontextmanager, _AsyncGeneratorContextManager
from http import HTTPStatus
from fastapi import FastAPI, HTTPException, UploadFile as File
from fastapi.params import (
    Depends,
    Path,
    Query,
    Header,
    Cookie,
    Body,
    Form,
    File as Forms
)
from reydb.rconn import DatabaseConnectionAsync
from reydb.rorm import DatabaseORMModel, DatabaseORMSessionAsync
from reykit.rwrap import wrap_cache
from reykit.rbase import CoroutineFunctionSimple, Base, Exit, StaticMeta, ConfigMeta, throw

from . import rserver


__all__ = (
    'ServerBase',
    'ServerConfig',
    'ServerExit',
    'ServerExitAPI',
    'exit_api',
    'ServerBind'
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


class ServerExitAPI(ServerExit, HTTPException):
    """
    Server exit API type.
    """


def exit_api(code: int = 400, text: str | None = None) -> NoReturn:
    """
    Throw exception to exit API.

    Parameters
    ----------
    code : Response status code.
    text : Explain text.
        `None`: Use Default text.
    """

    # Parameter.
    if not 400 <= code <= 499:
        throw(ValueError, code)
    if text is None:
        status = HTTPStatus(code)
        text = status.description

    # Throw exception.
    raise ServerExitAPI(code, text)


class ServerBind(ServerBase, metaclass=StaticMeta):
    """
    Server API bind parameter type.
    """


    def create_lifespan(
        before: CoroutineFunctionSimple | Sequence[CoroutineFunctionSimple] | None = None,
        after: CoroutineFunctionSimple | Sequence[CoroutineFunctionSimple] | None = None,
    ) -> _AsyncGeneratorContextManager[None, None]:
        """
        Create asynchronous function of lifespan manager.

        Parameters
        ----------
        before : Execute before server start.
        after : Execute after server end.

        Returns
        -------
        Asynchronous function.
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


    @wrap_cache
    def create_depend_db(database: str, mode: Literal['sess', 'conn']) -> Depends:
        """
        Create dependencie type of asynchronous database.

        Parameters
        ----------
        database : Database name.
        mode : Mode.
            - `Literl['sess']`: Create ORM session instance.
            - `Literl['conn']`: Create connection instance.

        Returns
        -------
        Dependencie type.
        """


        async def depend_db():
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


        # Create.
        depend = Depends(depend_db)

        return depend


    Depend = Depends
    Path = Path
    Query = Query
    Header = Header
    Cookie = Cookie
    Body = Body
    Form = Form
    Forms = Forms
    File = File
    JSON = DatabaseORMModel
    Conn = DatabaseConnectionAsync
    Sess = DatabaseORMSessionAsync
    path = Path()
    'Path instance.'
    query = Query()
    'Query instance.'
    header = Header()
    'Header instance.'
    cookie = Cookie()
    'Cookie instance.'
    body = Body()
    'Body instance.'
    form = Form()
    'Form instance.'
    forms = Forms()
    'Forms instance.'
    query_n = Query(None)
    'Query instance, default `None`.'
    header_n = Header(None)
    'Header instance, default `None`.'
    cookie_n = Cookie(None)
    'Cookie instance, default `None`.'
    body_n = Body(None)
    'Body instance, default `None`.'
    form_n = Form(None)
    'Form instance, default `None`.'
    forms_n = Forms(None)
    'Forms instance, default `None`.'


Bind = ServerBind
