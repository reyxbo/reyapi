# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-10-05 00:55:28
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Server methods.
"""


from typing import Literal
from inspect import iscoroutinefunction
from collections.abc import Sequence, Callable, Coroutine
from fastapi import FastAPI, Depends
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from uvicorn import run as uvicorn_run
from contextlib import asynccontextmanager
from reykit.rbase import CoroutineFunctionSimple

from .rbase import ServerBase, generate_lifespan


__all__ = (
    'Server',
)


class Server(ServerBase):
    """
    Server type.
    Based on `fastapi` and `uvicorn` package.
    """


    def __init__(
        self,
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
        public : Public directory.
        depend : Global api dependencies.
        before : Execute before server start.
        after : Execute after server end.
        """

        # Parameter.
        if type(ssl_cert) != type(ssl_key):
            raise
        lifespan = generate_lifespan(before, after)
        if iscoroutinefunction(depend):
            depend = (depend,)
        dependencies = [
            Depends(depend)
            for task in depend
        ]

        # Build.
        self.ssl_cert = ssl_cert
        self.ssl_key = ssl_key

        ## App.
        self.app = FastAPI(
            dependencies=dependencies,
            lifespan=lifespan
        )

        ## Static.
        if public is not None:
            subapp = StaticFiles(directory=public, html=True)
            self.app.mount('/', subapp)

        ## Middleware.
        self.app.add_middleware(GZipMiddleware)
        # self.app.add_middleware(TrustedHostMiddleware)
        # self.app.add_middleware(HTTPSRedirectMiddleware)


    def run(self) -> None:
        """
        Run.
        """

        # Run.
        uvicorn_run(
            self.app,
            ssl_certfile=self.ssl_cert,
            ssl_keyfile=self.ssl_key
        )


    def add_api_file(self): ...
