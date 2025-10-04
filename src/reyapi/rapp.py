# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-10-05 00:55:28
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : APP methods.
"""


from collections.abc import Sequence
from types import CoroutineType
from fastapi import FastAPI, Depends as get_depends
from fastapi.params import Depends

from .rbase import APIBase


class API(APIBase):
    """
    API type.
    Based on `fastapi` package.
    """


    def __init__(
        self,
        dependencies: Sequence[CoroutineType],
        before: CoroutineType,
        after: CoroutineType,
        debug: bool = False
    ) -> None:
        """
        Build instance attributes.
        """

        # Build.
        self.app = FastAPI()


    def add_api_all(): ...


    def add_api_base(): ...


    def add_api_file(): ...
