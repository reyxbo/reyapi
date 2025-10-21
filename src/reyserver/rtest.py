# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-10-21
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Test methods.
"""


from typing import Literal
from fastapi import APIRouter

from .rbase import Bind


__all__ = (
    'router_test',
)


router_test = APIRouter()


@router_test.get('/test')
def test() -> Literal['test']:
    """
    Test.

    Returns
    -------
    Text `test`.
    """

    # Resposne.
    response = 'test'

    return response


@router_test.post('/test/echo')
def test_echo(data: dict = Bind.i.body) -> dict:
    """
    Echo test.

    Paremeters
    ----------
    data : Echo data.

    Returns
    -------
    Echo data.
    """

    # Resposne.

    return data
