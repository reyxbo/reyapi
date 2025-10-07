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
from fastapi import FastAPI
from reykit.rbase import CoroutineFunctionSimple, Base, is_iterable


__all__ = (
    'ServerBase',
    'ServerAPI',
    'generate_lifespan'
)


class ServerBase(Base):
    """
    Server base type.
    """


class ServerAPI(ServerBase):
    """
    Server API type.
    """


def generate_lifespan(
    before: CoroutineFunctionSimple | Sequence[CoroutineFunctionSimple] | None = None,
    after: CoroutineFunctionSimple | Sequence[CoroutineFunctionSimple] | None = None,
):
    """
    Generate function of lifespan manager.

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

    # Define.
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
