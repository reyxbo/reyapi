# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-10-09
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Client methods.
"""


from typing import TypedDict, Literal
from datetime import datetime as Datetime
from reykit.ros import File, Folder, overload
from reykit.rnet import join_url, request, get_response_file_name

from .rbase import ServerBase


__all__ = (
    'ServerClient',
)


FileInfo = TypedDict('FileInfo', {'create_time': Datetime, 'md5': str, 'name': str | None, 'size': int, 'note': str | None})


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


    def create_session(
        self,
        account: str,
        password: str,
        account_type: Literal['name', 'email', 'phone'] = 'name'
    ) -> str:
        """
        Create session.

        Parameters
        ----------
        account : User account, name or email or phone.
        password : User password.
        account_type : User account type.

        Returns
        -------
        Token.
        """

        # Parameter.
        url = join_url(self.url, 'sessions')
        json = {
            'account': account,
            'password': password,
            'account_type': account_type
        }

        # Request.
        response = request(url, json=json, check=True)
        response_dict = response.json()
        print(response_dict)
        token = response_dict['token']

        return token


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
        url = join_url(self.url, 'files')
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

        # Request.
        data = {'name': file_name, 'note': note}
        files = {'file': file_bytes}
        response = request(url, data=data, files=files, check=True)

        ## Extract.
        response_json = response.json()
        file_id = response_json['file_id']

        return file_id


    @overload
    def download_file(
        self,
        file_id: int,
        path: None = None
    ) -> bytes: ...

    @overload
    def download_file(
        self,
        file_id: int,
        path: str
    ) -> str: ...

    def download_file(
        self,
        file_id: int,
        path: str | None = None
    ) -> bytes | str:
        """
        Download file.

        Parameters
        ----------
        file_id : File ID.
        path : File save path.
            - `None`: Not save and return file bytes.
            - `str`: Save and return file path.
                `File path`: Use this file path.
                `Folder path`: Use this folder path and original name.

        Returns
        -------
        File bytes or file path.
        """

        # Parameter.
        url = join_url(self.url, 'files', file_id, 'download')

        # Request.
        response = request(url, check=True)
        file_bytes = response.content

        # Not save.
        if path is None:
            return file_bytes

        # Save.
        else:
            folder = Folder(path)
            if folder:
                file_name = get_response_file_name(response)
                path = folder + file_name
            file = File(path)
            file(file_bytes)
            return file.path


    def get_file_info(
        self,
        file_id: int
    ) -> FileInfo:
        """
        Query file information.

        Parameters
        ----------
        file_id : File ID.

        Returns
        -------
        File information.
        """

        # Parameter.
        url = join_url(self.url, 'files', file_id)

        # Request.
        response = request(url, check=True)
        response_dict = response.json()

        return response_dict
