# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-10-05
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Server methods.
"""


from collections.abc import Sequence
from inspect import iscoroutinefunction
from uvicorn import run as uvicorn_run
from fastapi import FastAPI, Depends
from fastapi.staticfiles import StaticFiles
from reydb import DatabaseAsync
from reykit.rbase import CoroutineFunctionSimple, Singleton, throw

from .rbase import ServerBase, ServerConfig, create_lifespan


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
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        db : Asynchronous database.
        public : Public directory.
        depend : Global api dependencies.
        before : Execute before server start.
        after : Execute after server end.
        ssl_cert : SSL certificate file path.
        ssl_key : SSL key file path.
        """

        # Parameter.
        if type(ssl_cert) != type(ssl_key):
            throw(AssertionError, ssl_cert, ssl_key)
        lifespan = create_lifespan(before, after)
        if depend is None:
            depend = ()
        elif iscoroutinefunction(depend):
            depend = (depend,)
        depend = [
            Depends(task)
            for task in depend
        ]

        # Build.
        ServerConfig.server = self
        self.db = db
        self.ssl_cert = ssl_cert
        self.ssl_key = ssl_key

        ## App.
        self.app = FastAPI(
            dependencies=depend,
            lifespan=lifespan,
            debug=True
        )

        ## Static.
        if public is not None:
            subapp = StaticFiles(directory=public, html=True)
            self.app.mount('/', subapp)

        ## API.

        ### File.
        self.api_file_dir: str


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


    def add_api_base(self):

        @self.app.get('/test')
        async def test():
            return {'message': 'test'}


    def add_api_file(self, file_dir: str = 'file') -> None:
        """
        Add file API.

        Parameters
        ----------
        file_dir : File API store directory path.
        prefix : File API path prefix.
        """

        from .rfile import file_router, build_file_db

        # Build database.
        build_file_db()

        # Add.
        self.api_file_dir = file_dir
        self.app.include_router(file_router, prefix='/files', tags=['file'])
