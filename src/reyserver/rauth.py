# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-10-10
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Authentication methods.
"""


from fastapi import APIRouter
from reydb import rorm

from .rbase import ServerConfig, Bind, exit_api


__all__ = (
    'DatabaseORMTableInfo',
    'DatabaseORMTableData',
    'build_file_db',
    'file_router'
)


class DatabaseORMTableUser(rorm.Model, table=True):
    """
    Database `user` table ORM model.
    """

    __name__ = 'user'
    __comment__ = 'User information table.'
    create_time: rorm.Datetime = rorm.Field(field_default=':create_time', not_null=True, index_n=True, comment='Record create time.')
    update_time: rorm.Datetime = rorm.Field(field_default=':update_time', not_null=True, index_n=True, comment='Record update time.')
    user_id: int = rorm.Field(rorm.types_mysql.MEDIUMINT(unsigned=True), key_auto=True, comment='User ID.')
    name: str = rorm.Field(rorm.types.VARCHAR(50), not_null=True, index_u=True, comment='User name.')
    password: str
    email: rorm.Email
    phone: int
    head: int
    is_valid: bool = rorm.Field(rorm.types_mysql.TINYINT(unsigned=True), field_default='1', not_null=True, comment='Is the valid.')


class DatabaseORMTableRole(rorm.Model, table=True):
    """
    Database `role` table ORM model.
    """

    __name__ = 'role'
    __comment__ = 'Role information table.'
    create_time: rorm.Datetime = rorm.Field(field_default=':create_time', not_null=True, index_n=True, comment='Record create time.')
    update_time: rorm.Datetime = rorm.Field(field_default=':update_time', not_null=True, index_n=True, comment='Record update time.')
    role_id: int = rorm.Field(rorm.types_mysql.SMALLINT(unsigned=True), key_auto=True, comment='Role ID.')
    name: str = rorm.Field(rorm.types.VARCHAR(50), not_null=True, index_u=True, comment='Role name.')
    desc: str = rorm.Field(rorm.types.VARCHAR(500), comment='Role description.')


class DatabaseORMTablePerm(rorm.Model, table=True):
    """
    Database `perm` table ORM model.
    """

    __name__ = 'perm'
    __comment__ = 'Permission information table.'
    create_time: rorm.Datetime = rorm.Field(field_default=':create_time', not_null=True, index_n=True, comment='Record create time.')
    update_time: rorm.Datetime = rorm.Field(field_default=':update_time', not_null=True, index_n=True, comment='Record update time.')
    perm_id: int = rorm.Field(rorm.types_mysql.SMALLINT(unsigned=True), key_auto=True, comment='Permission ID.')
    name: str = rorm.Field(rorm.types.VARCHAR(50), not_null=True, index_u=True, comment='Permission name.')
    desc: str = rorm.Field(rorm.types.VARCHAR(500), comment='Permission description.')
    code: str


class DatabaseORMTableUserRole(rorm.Model, table=True):
    """
    Database `user_role` table ORM model.
    """

    __name__ = 'user_role'
    __comment__ = 'User and role association table.'
    create_time: rorm.Datetime = rorm.Field(field_default=':create_time', not_null=True, index_n=True, comment='Record create time.')
    update_time: rorm.Datetime = rorm.Field(field_default=':update_time', not_null=True, index_n=True, comment='Record update time.')
    user_id: int = rorm.Field(rorm.types_mysql.MEDIUMINT(unsigned=True), key=True, comment='User ID.')
    role_id: int = rorm.Field(rorm.types_mysql.SMALLINT(unsigned=True), key=True, comment='Role ID.')


class DatabaseORMTableRolePerm(rorm.Model, table=True):
    """
    Database `role_perm` table ORM model.
    """

    __name__ = 'role_perm'
    __comment__ = 'role and permission association table.'
    create_time: rorm.Datetime = rorm.Field(field_default=':create_time', not_null=True, index_n=True, comment='Record create time.')
    update_time: rorm.Datetime = rorm.Field(field_default=':update_time', not_null=True, index_n=True, comment='Record update time.')
    role_id: int = rorm.Field(rorm.types_mysql.SMALLINT(unsigned=True), key=True, comment='Role ID.')
    perm_id: int = rorm.Field(rorm.types_mysql.SMALLINT(unsigned=True), key=True, comment='Permission ID.')


def build_file_db() -> None:
    """
    Check and build `file` database tables.
    """

    # Set parameter.
    engine = ServerConfig.server.db.file
    database = engine.database

    ## Table.
    tables = [
        DatabaseORMTableUser,
        DatabaseORMTableRole,
        DatabaseORMTablePerm,
        DatabaseORMTableUserRole,
        DatabaseORMTableRolePerm
    ]

    ## View stats.
    views_stats = [
        {
            'path': 'stats',
            'items': [
                {
                    'name': 'count',
                    'select': (
                        'SELECT COUNT(1)\n'
                        f'FROM `{database}`.`info`'
                    ),
                    'comment': 'File information count.'
                },
                {
                    'name': 'past_day_count',
                    'select': (
                        'SELECT COUNT(1)\n'
                        f'FROM `{database}`.`info`\n'
                        'WHERE TIMESTAMPDIFF(DAY, `create_time`, NOW()) = 0'
                    ),
                    'comment': 'File information count in the past day.'
                },
                {
                    'name': 'past_week_count',
                    'select': (
                        'SELECT COUNT(1)\n'
                        f'FROM `{database}`.`info`\n'
                        'WHERE TIMESTAMPDIFF(DAY, `create_time`, NOW()) <= 6'
                    ),
                    'comment': 'File information count in the past week.'
                },
                {
                    'name': 'past_month_count',
                    'select': (
                        'SELECT COUNT(1)\n'
                        f'FROM `{database}`.`info`\n'
                        'WHERE TIMESTAMPDIFF(DAY, `create_time`, NOW()) <= 29'
                    ),
                    'comment': 'File information count in the past month.'
                },
                {
                    'name': 'data_count',
                    'select': (
                        'SELECT COUNT(1)\n'
                        f'FROM `{database}`.`data`'
                    ),
                    'comment': 'File data unique count.'
                },
                {
                    'name': 'total_size',
                    'select': (
                        'SELECT FORMAT(SUM(`size`), 0)\n'
                        f'FROM `{database}`.`data`'
                    ),
                    'comment': 'File total byte size.'
                },
                {
                    'name': 'avg_size',
                    'select': (
                        'SELECT FORMAT(AVG(`size`), 0)\n'
                        f'FROM `{database}`.`data`'
                    ),
                    'comment': 'File average byte size.'
                },
                {
                    'name': 'max_size',
                    'select': (
                        'SELECT FORMAT(MAX(`size`), 0)\n'
                        f'FROM `{database}`.`data`'
                    ),
                    'comment': 'File maximum byte size.'
                },
                {
                    'name': 'last_time',
                    'select': (
                        'SELECT MAX(`create_time`)\n'
                        f'FROM `{database}`.`info`'
                    ),
                    'comment': 'File last record create time.'
                }
            ]
        }
    ]

    # Build.
    engine.sync_engine.build.build(tables=tables, views=views, views_stats=views_stats, skip=True)


file_router = APIRouter()
depend_file_sess = Bind.create_depend_db('file', 'sess')
depend_file_conn = Bind.create_depend_db('file', 'conn')


@file_router.post('/')
async def upload_file(
    file: Bind.File = Bind.forms,
    name: str = Bind.forms_n,
    note: str = Bind.forms_n,
    sess: Bind.Sess = depend_file_sess
) -> DatabaseORMTableInfo:
    """
    Upload file.

    Parameters
    ----------
    file : File instance.
    name : File name.
    note : File note.

    Returns
    -------
    File information.
    """