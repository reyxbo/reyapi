# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-10-09
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Client methods.
"""


from .rbase import ServerBase


__all__ = (
    'ServerClient',
)


class ServerClient(ServerBase):
    """
    Server client type.
    """


    def __init__(self, url: str) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        url : Server url.
        """

        # Build.
        self.url = url


    def upload_file(self): ...


    def download_file(self): ...


    def index_file(self): ...
