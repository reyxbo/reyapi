# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-10-09
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Client methods.
"""


from reykit.ros import File, get_md5
from reykit.rnet import join_url, request

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


    def upload_file(
        self,
        source: str | bytes,
        name: str | None = None,
        note: str | None = None
    ) -> int:
        """
        Upload file.

        Parameters
        ----------
        source : File path or file bytes.
        name : File name.
            - `None`: Automatic set.
                `parameter 'file' is 'str'`: Use path file name.
                `parameter 'file' is 'bytes'`: No name.
            - `str`: Use this name.
        note : File note.

        Returns
        -------
        File ID.
        """

        # Handle parameter.
        url = join_url(self.url, 'file', 'upload')
        match source:

            ## File path.
            case str():
                file = File(source)
                file_bytes = file.bytes
                file_name = file.name_suffix

            ## File bytes.
            case bytes() | bytearray():
                if type(source) == bytearray:
                    source = bytes(source)
                file_bytes = source
                file_name = None

        ## File name.
        if name is not None:
            file_name = name

        # Upload.
        data = {'name': file_name, 'note': note}
        files = {'file': file_bytes}
        response = request(url, data=data, files=files, check=True)

        ## Extract.
        response_json = response.json()
        file_id = response_json['file_id']

        return file_id


    def download_file(self): ...


    def index_file(self): ...
