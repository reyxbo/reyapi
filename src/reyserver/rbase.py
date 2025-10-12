# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-07-17
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Base methods.
"""


from typing import Literal, NoReturn
from http import HTTPStatus
from fastapi import HTTPException, UploadFile as File
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
from reykit.rbase import Base, Exit, StaticMeta, ConfigMeta, Singleton, throw

from . import rserver


__all__ = (
    'ServerBase',
    'ServerConfig',
    'ServerExit',
    'ServerExitAPI',
    'exit_api',
    'ServerBind',
    'Bind'
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


class ServerBindInstance(ServerBase, Singleton):
    """
    Server API bind parameter build instance type.
    """


    @property
    def path(self) -> Path:
        """
        Path instance.
        """

        # Build.
        path = Path()

        return path


    @property
    def query(self) -> Query:
        """
        Query instance.
        """

        # Build.
        query = Query()

        return query


    @property
    def header(self) -> Header:
        """
        Header instance.
        """

        # Build.
        header = Header()

        return header


    @property
    def cookie(self) -> Cookie:
        """
        Cookie instance.
        """

        # Build.
        cookie = Cookie()

        return cookie


    @property
    def body(self) -> Body:
        """
        Body instance.
        """

        # Build.
        body = Body()

        return body


    @property
    def form(self) -> Form:
        """
        Form instance.
        """

        # Build.
        form = Form()

        return form


    @property
    def forms(self) -> Forms:
        """
        Forms instance.
        """

        # Build.
        forms = Forms()

        return forms


    @property
    def query_n(self) -> Query:
        """
        Query instance, default `None`.
        """

        # Build.
        query = Query(None)

        return query


    @property
    def header_n(self) -> Header:
        """
        Header instance, default `None`.
        """

        # Build.
        header = Header(None)

        return header


    @property
    def cookie_n(self) -> Cookie:
        """
        Cookie instance, default `None`.
        """

        # Build.
        cookie = Cookie(None)

        return cookie


    @property
    def body_n(self) -> Body:
        """
        Body instance, default `None`.
        """

        # Build.
        body = Body(None)

        return body


    @property
    def form_n(self) -> Form:
        """
        Form instance, default `None`.
        """

        # Build.
        form = Form(None)

        return form


    @property
    def forms_n(self) -> Forms:
        """
        Forms instance, default `None`.
        """

        # Build.
        forms = Forms(None)

        return forms


class ServerBind(ServerBase, metaclass=StaticMeta):
    """
    Server API bind parameter type.
    """


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
    i = ServerBindInstance()


Bind = ServerBind
