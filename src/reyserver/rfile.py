# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-10-06 18:23:51
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : File methods. Can create database used `self.build_db` function.
"""


from fastapi import APIRouter
from reydb import rorm
from reydb.rdb import DatabaseAsync

from . import rserver
from .rbase import ServerAPI


__all__ = (
    'file_router',
    'DatabaseORMTableInfo',
    'DatabaseORMTableData',
    'build_file_db'
)


file_router = APIRouter()


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


def build_file_db(db: DatabaseAsync) -> None:
    """
    Check and build all standard databases and tables, by `self.db_names`.

    Parameters
    db : Asynchronous database instance.
    """

    # Set parameter.
    database = db.database

    ## Table.
    tables = [DatabaseORMTableInfo, DatabaseORMTableData]

    ## View.
    views = [
        {
            'path': 'data_info',
            'select': (
                'SELECT `b`.`last_time`, `a`.`md5`, `a`.`size`, `b`.`names`, `b`.`notes`\n'
                f'FROM `{database}`.`data` AS `a`\n'
                'LEFT JOIN (\n'
                '    SELECT\n'
                '        `md5`,\n'
                "        GROUP_CONCAT(DISTINCT(`name`) ORDER BY `create_time` DESC SEPARATOR ' | ') AS `names`,\n"
                "        GROUP_CONCAT(DISTINCT(`note`) ORDER BY `create_time` DESC SEPARATOR ' | ') AS `notes`,\n"
                '        MAX(`create_time`) as `last_time`\n'
                f'    FROM `{database}`.`info`\n'
                '    GROUP BY `md5`\n'
                '    ORDER BY `last_time` DESC\n'
                ') AS `b`\n'
                'ON `a`.`md5` = `b`.`md5`\n'
                'ORDER BY `last_time` DESC'
            )
        }
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
    db.build.build(tables=tables, views=views, views_stats=views_stats)


@file_router.post('/upload')
def upload(
    source: bytes,
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
    conn = self.db.connect()
    match source:

        ## File path.
        case str():
            file = File(source)
            file_bytes = file.bytes
            file_md5 = get_md5(file_bytes)
            file_name = file.name_suffix

        ## File bytes.
        case bytes() | bytearray():
            if type(source) == bytearray:
                source = bytes(source)
            file_bytes = source
            file_md5 = get_md5(file_bytes)
            file_name = None

    ## File name.
    if name is not None:
        file_name = name

    ## File size.
    file_size = len(file_bytes)

    # Exist.
    exist = conn.execute.exist(
        (self.db_names['file'], self.db_names['file.data']),
        '`md5` = :file_md5',
        file_md5=file_md5
    )

    # Upload.

    ## Data.
    if not exist:
        data = {
            'md5': file_md5,
            'size': file_size,
            'bytes': file_bytes
        }
        conn.execute.insert(
            (self.db_names['file'], self.db_names['file.data']),
            data,
            'ignore'
        )

    ## Information.
    data = {
        'md5': file_md5,
        'name': file_name,
        'note': note
    }
    conn.execute.insert(
        (self.db_names['file'], self.db_names['file.information']),
        data
    )

    # Get ID.
    file_id = conn.insert_id

    # Commit.
    conn.commit()

    return file_id