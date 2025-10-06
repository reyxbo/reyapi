# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-10-05 00:55:28
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Server methods.
"""


from typing import Literal
from collections.abc import Sequence, Callable, Coroutine
from types import CoroutineType
from inspect import iscoroutinefunction, iscoroutine
from fastapi import FastAPI, Depends as get_depends
from fastapi.params import Depends
# from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.staticfiles import StaticFiles
from uvicorn import run as uvicorn_run
from fastapi.responses import HTMLResponse
from reykit.ros import File, Folder
from reykit.rbase import CoroutineFunction

from .rbase import ServerBase


__all__ = (
    'Server',
)


type CoroutineFunction = Callable[[], Coroutine]


class Server(ServerBase):
    """
    Server type.
    Based on `fastapi` and `uvicorn` package.
    """


    def __init__(
        self,
        public: str | None = None,
        depend: CoroutineFunction | Sequence[CoroutineFunction] | None = None,
        before: CoroutineFunction | Sequence[CoroutineFunction] | None = None,
        after: CoroutineFunction | Sequence[CoroutineFunction] | None = None,
        ssl_cert: str | None = None,
        ssl_key: str | None = None,
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        public : Public directory.
        depend : Global api dependencies.
        before : Before 
        """

        # Parameter.
        if type(ssl_cert) != type(ssl_key):
            raise

        # Build.
        self.app = FastAPI()
        # self.index = Folder(public) + 'index.html'
        self.ssl_cert = ssl_cert
        self.ssl_key = ssl_key

        ## Middleware.
        self.app.add_middleware(GZipMiddleware)
        # self.app.add_middleware(TrustedHostMiddleware)
        # self.app.add_middleware(HTTPSRedirectMiddleware)

        ## Static.
        if public is not None:
            subapp = StaticFiles(directory=public, html=True)
            self.app.mount('/', subapp)


    def run(self):
        """
        Run.
        """

        # Run.
        uvicorn_run(
            self.app,
            ssl_certfile=self.ssl_cert,
            ssl_keyfile=self.ssl_key
        )


    def add_api_all(self):

        self.add_api_all()


    def add_api_base(self):

        # @self.app.get('/')
        # def index():
        #     file_bytes = File(self.index).bytes
        #     response = HTMLResponse(file_bytes)
        #     return response


        @self.app.get('/test')
        def test():
            return {'message': 'test'}


    def add_api_file(self): ...
