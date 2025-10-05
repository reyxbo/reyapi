# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-07-17 22:32:37
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Base methods.
"""


from reykit.rbase import Base


__all__ = (
    'ServerBase',
    'RequestAPI'
)


class ServerBase(Base):
    """
    Server base type.
    """


class RequestAPI(ServerBase):
    """
    Request API type.
    """
