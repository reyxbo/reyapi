# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-10-06 18:23:51
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : File methods.
"""


from fastapi import APIRouter
from reydb import rorm

from . import rserver
from .rbase import ServerAPI


__all__ = (
    'ServerAPIFile',
)


# class ServerAPIFile(ServerAPI):
#     """
#     Server File API type.
#     """


#     def __init__(self, server: 'rserver.Server') -> None:
#         """
#         Build instance attributes.

#         Parameters
#         ----------
#         server : Server instance.
#         """

#         # Build.
#         self.server = server



class DatabaseORMTableInfo(rorm.Model, table=True):
    """
    Database `info` table model.
    """

    __name__ = 'info'
    __comment__ = 'File information table.'
    create_time: rorm.Datetime = rorm.Field(field_default=':create_time', not_null=True, index_n=True, comment='Record create time.')
    field_id: int = rorm.Field(rorm.types_mysql.MEDIUMINT(unsigned=True), key_auto=True, comment='File self increase ID.')
    md5: str = rorm.Field(rorm.types.CHAR(32), not_null=True, index_n=True, comment='File MD5.')
    name: str = rorm.Field(rorm.types.VARCHAR(260), index_n=True, comment='File name.')
    note: str = rorm.Field(rorm.types.VARCHAR(500), comment='File note.')


class DatabaseORMTableData(rorm.Model, table=True):
    """
    Database `data` table model.
    """

    __name__ = 'data'
    __comment__ = 'File data table.'
    md5: str = rorm.Field(rorm.types.CHAR(32), key=True, comment='File MD5.')
    size: int = rorm.Field(rorm.types_mysql.INTEGER(unsigned=True), not_null=True, comment='File bytes size.')
    path: str = rorm.Field(rorm.types.VARCHAR(4095), not_null=True, comment='File disk storage path.')



router = APIRouter()


@router.get('/{file_id}')
def get_file_info(): ...

@router.get('/{}/bytes')
def get_file_bytes(): ...

