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
    'APIBase',
    'APIRequest'
)


class APIBase(Base):
    """
    API base type.
    """


class APIRequest(APIBase):
    """
    Request API type.
    """
