# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-10-06
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : File methods. Can create database used `self.build_db` function.
"""


from fastapi import APIRouter
from fastapi.responses import FileResponse
from reydb import rorm, DatabaseEngine, DatabaseEngineAsync
from reykit.ros import FileStore, get_md5

from .rbase import ServerConfig, Bind, exit_api


__all__ = (
    'DatabaseORMTableInfo',
    'DatabaseORMTableData',
    'build_file_db',
    'file_router'
)


class DatabaseORMTableInfo(rorm.Model, table=True):
    """
    Database `info` table ORM model.
    """

    __name__ = 'info'
    __comment__ = 'File information table.'
    create_time: rorm.Datetime = rorm.Field(field_default=':create_time', not_null=True, index_n=True, comment='Record create time.')
    file_id: int = rorm.Field(rorm.types_mysql.MEDIUMINT(unsigned=True), key_auto=True, comment='File ID.')
    md5: str = rorm.Field(rorm.types.CHAR(32), not_null=True, index_n=True, comment='File MD5.')
    name: str = rorm.Field(rorm.types.VARCHAR(260), index_n=True, comment='File name.')
    note: str = rorm.Field(rorm.types.VARCHAR(500), comment='File note.')


class DatabaseORMTableData(rorm.Model, table=True):
    """
    Database `data` table ORM model.
    """

    __name__ = 'data'
    __comment__ = 'File data table.'
    md5: str = rorm.Field(rorm.types.CHAR(32), key=True, comment='File MD5.')
    size: int = rorm.Field(rorm.types_mysql.INTEGER(unsigned=True), not_null=True, comment='File bytes size.')
    path: str = rorm.Field(rorm.types.VARCHAR(4095), not_null=True, comment='File disk storage path.')


def build_file_db(engine: DatabaseEngine | DatabaseEngineAsync) -> None:
    """
    Check and build `file` database tables.

    Parameters
    ----------
    db : Database engine instance.
    """

    # Set parameter.
    database = engine.database

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
    engine.sync_engine.build.build(tables=tables, views=views, views_stats=views_stats, skip=True)


file_router = APIRouter()
depend_file_sess = Bind.create_depend_db('file', 'sess')
depend_file_conn = Bind.create_depend_db('file', 'conn')


@file_router.get('/files/{file_id}')
async def get_file_info(
    file_id: int = Bind.i.path,
    sess: Bind.Sess = depend_file_sess
) -> DatabaseORMTableInfo:
    """
    Get file information.

    Parameters
    ----------
    file_id : File ID.

    Returns
    -------
    File information.
    """

    # Get.
    table_info = await sess.get(DatabaseORMTableInfo, file_id)

    # Check.
    if table_info is None:
        exit_api(404)

    return table_info


@file_router.post('/files')
async def upload_file(
    file: Bind.File = Bind.i.forms,
    name: str = Bind.i.forms_n,
    note: str = Bind.i.forms_n,
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

    # Handle parameter.
    file_store = FileStore(ServerConfig.server.api_file_dir)
    file_bytes = await file.read()
    file_md5 = get_md5(file_bytes)
    file_size = len(file_bytes)

    # Upload.
    file_path = file_store.index(file_md5)

    ## Data.
    if file_path is None:
        file_path = file_store.store(file_bytes)
        table_data = DatabaseORMTableData(
            md5=file_md5,
            size=file_size,
            path=file_path
        )
        await sess.add(table_data)

    ## Information.
    table_info = DatabaseORMTableInfo(
        md5=file_md5,
        name=name,
        note=note
    )
    await sess.add(table_info)

    # Get ID.
    await sess.flush()

    return table_info


@file_router.get('/files/{file_id}/download')
async def download_file(
    file_id: int = Bind.i.path,
    conn: Bind.Conn = depend_file_conn
) -> FileResponse:
    """
    Download file.

    Parameters
    ----------
    file_id : File ID.

    Returns
    -------
    File data.
    """

    # Search.
    sql = (
        'SELECT `name`, (\n'
        '    SELECT `path`\n'
        f'    FROM `{conn.engine.database}`.`data`\n'
        f'    WHERE `md5` = `info`.`md5`\n'
        '    LIMIT 1\n'
        ') AS `path`\n'
        f'FROM `{conn.engine.database}`.`info`\n'
        'WHERE `file_id` = :file_id\n'
        'LIMIT 1'
    )
    result = await conn.execute(sql, file_id=file_id)

    # Check.
    if result.empty:
        exit_api(404)
    file_name, file_path = result.first()

    # Response.
    response = FileResponse(file_path, filename=file_name)

    return response
