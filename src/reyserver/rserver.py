# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-10-05
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Server methods.
"""


from typing import Literal
from collections.abc import Sequence, Callable, Coroutine
from inspect import iscoroutinefunction
from contextlib import asynccontextmanager, _AsyncGeneratorContextManager
from uvicorn import run as uvicorn_run
from starlette.middleware.base import _StreamingResponse
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from reydb import DatabaseAsync
from reykit.rbase import CoroutineFunctionSimple, Singleton, throw
from reykit.rrand import randchar

from .rbase import ServerBase, ServerConfig, Bind


__all__ = (
    'Server',
)


class Server(ServerBase, Singleton):
    """
    Server type, singleton mode.
    Based on `fastapi` and `uvicorn` package.
    Can view document api '/docs', '/redoc', '/openapi.json'.
    """


    def __init__(
        self,
        db: DatabaseAsync,
        public: str | None = None,
        depend: CoroutineFunctionSimple | Sequence[CoroutineFunctionSimple] | None = None,
        before: CoroutineFunctionSimple | Sequence[CoroutineFunctionSimple] | None = None,
        after: CoroutineFunctionSimple | Sequence[CoroutineFunctionSimple] | None = None,
        ssl_cert: str | None = None,
        ssl_key: str | None = None,
        db_warm: bool = False,
        debug: bool = False
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        db : Asynchronous database, must include database engines with APIs.
        public : Public directory.
        depend : Global api dependencies.
        before : Execute before server start.
        after : Execute after server end.
        ssl_cert : SSL certificate file path.
        ssl_key : SSL key file path.
        db_warm : Whether database pre create connection to warm all pool.
        debug : Whether use development mode debug server.
        """

        # Parameter.
        if type(ssl_cert) != type(ssl_key):
            throw(AssertionError, ssl_cert, ssl_key)
        if depend is None:
            depend = ()
        elif iscoroutinefunction(depend):
            depend = (depend,)
        depend = [
            Bind.Depend(task)
            for task in depend
        ]
        lifespan = self.__create_lifespan(before, after, db_warm)

        # Build.
        ServerConfig.server = self
        self.db = db
        self.ssl_cert = ssl_cert
        self.ssl_key = ssl_key

        ## App.
        self.app = FastAPI(
            dependencies=depend,
            lifespan=lifespan,
            debug=debug
        )

        if public is not None:
            subapp = StaticFiles(directory=public, html=True)
            self.app.mount('/', subapp)
        self.wrap_middleware = self.app.middleware('http')
        'Decorator, add middleware to APP.'

        # Middleware
        self.app.add_middleware(GZipMiddleware)
        if not debug:
            self.app.add_middleware(HTTPSRedirectMiddleware)
        self.__add_default_middleware()

        # API.
        self.api_auth_key: str
        'Authentication API JWT encryption key.'
        self.api_auth_sess_seconds: int
        'Authentication API session valid seconds.'
        self.api_file_dir: str
        'File API store directory path.'


    def __create_lifespan(
        self,
        before: CoroutineFunctionSimple | Sequence[CoroutineFunctionSimple] | None,
        after: CoroutineFunctionSimple | Sequence[CoroutineFunctionSimple] | None,
        db_warm: bool
    ) -> _AsyncGeneratorContextManager[None, None]:
        """
        Create asynchronous function of lifespan manager.

        Parameters
        ----------
        before : Execute before server start.
        after : Execute after server end.
        db_warm : Whether database pre create connection to warm all pool.

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

            ## Databse.
            if db_warm:
                await self.db.warm_all()

            # Runing.
            yield

            # After.
            for task in after:
                await after()

            ## Database.
            await self.db.dispose_all()


        return lifespan


    def __add_default_middleware(self) -> None:
        """
        Add default handle middleware.
        """

        # Add.
        @self.wrap_middleware
        async def foo(
            request: Request,
            call_next: Callable[[Request], Coroutine[None, None, _StreamingResponse]]
        ) -> _StreamingResponse:
            """
            Default handle middleware.

            Parameters
            ----------
            Reqeust : Request instance.
            call_next : Next middleware.
            """

            # Before.
            ...

            # Next.
            response = await call_next(request)

            # After.
            if (
                response.status_code == 200
                and request.method == 'POST'
            ):
                response.status_code = 201

            return response


    def run(self) -> None:
        """
        Run server.
        """

        # Run.
        uvicorn_run(
            self.app,
            ssl_certfile=self.ssl_cert,
            ssl_keyfile=self.ssl_key
        )


    def set_doc(
        self,
        version: str | None = None,
        title: str | None = None,
        summary: str | None = None,
        desc: str | None = None,
        contact: dict[Literal['name', 'email', 'url'], str] | None = None
    ) -> None:
        """
        Set server document.

        Parameters
        ----------
        version : Server version.
        title : Server title.
        summary : Server summary.
        desc : Server description.
        contact : Server contact information.
        """

        # Parameter.
        set_dict = {
            'version': version,
            'title': title,
            'summary': summary,
            'description': desc,
            'contact': contact
        }

        # Set.
        for key, value in set_dict.items():
            if value is not None:
                setattr(self.app, key, value)


    def add_api_auth(self, key: str | None = None, sess_seconds: int = 28800) -> None:
        """
        Add authentication API.
        Note: must include database engine of `auth` name.

        Parameters
        ----------
        key : JWT encryption key.
            - `None`: Random 32 length string.
        sess_seconds : Session valid seconds.
        """

        from .rauth import build_auth_db, auth_router

        # Parameter.
        if key is None:
            key = randchar(32)

        # Build database.
        engine = self.db.auth
        build_auth_db(engine)

        # Add.
        self.api_auth_key = key
        self.api_auth_sess_seconds = sess_seconds
        self.app.include_router(auth_router, tags=['auth'])


    def add_api_file(self, file_dir: str = 'file') -> None:
        """
        Add file API.
        Note: must include database engine of `file` name.

        Parameters
        ----------
        file_dir : File API store directory path.
        prefix : File API path prefix.
        """

        from .rfile import build_file_db, file_router

        # Build database.
        engine = self.db.file
        build_file_db(engine)

        # Add.
        self.api_file_dir = file_dir
        self.app.include_router(file_router, tags=['file'])
