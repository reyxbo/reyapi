# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-10-06
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : File methods. Can create database used `self.build_db` function.
"""


from typing import Annotated
from fastapi import APIRouter, Form, File, UploadFile, Depends
from reydb import rorm, DatabaseEngineAsync
from reykit.ros import FileStore, get_md5

from .rbase import ServerAPI


__all__ = (
    'DatabaseORMTableInfo',
    'DatabaseORMTableData',
    'ServerAPIFile'
)


class DatabaseORMTableInfo(rorm.Model, table=True):
    """
    Database `info` table ORM model.
    """

    __name__ = 'info'
    __comment__ = 'File information table.'
    create_time: rorm.Datetime = rorm.Field(field_default=':create_time', not_null=True, index_n=True, comment='Record create time.')
    file_id: int = rorm.Field(rorm.types_mysql.MEDIUMINT(unsigned=True), key_auto=True, comment='File self increase ID.')
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


class ServerAPIFile(ServerAPI):
    """
    Server File API type.
    Can create database used `self.build_db` method.
    """


    def __init__(
        self,
        db_engine: DatabaseEngineAsync,
        path: str = 'file'
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        db_engine : Asynchronous database instance.
        path: File store directory.
        """

        # Build.
        self.db_engine = db_engine
        self.path = path

        ## Router.
        self.router = self.__create_router()

        ## Build Database.
        self.build_db()


    async def depend_sess(self):
        """
        Dependencie function of asynchronous database session.
        """

        # Context.
        async with self.db_engine.orm.session() as sess:
            yield sess


    def __create_router(self) -> APIRouter:
        """
        Add APIs to router.

        Returns
        -------
        Router.
        """

        # Parameter.
        router = APIRouter()


        @router.post('/upload')
        async def upload(
            file: Annotated[UploadFile, File()],
            note: Annotated[str, Form()],
            sess: Annotated[rorm.DatabaseORMSessionAsync, Depends(self.depend_sess)]
        ):
            """
            Upload file.

            Parameters
            ----------
            file : File instance.
            note : File note.
            sess : Asynchronous database session.
            """

            # Handle parameter.
            file_store = FileStore(self.path)
            file_name = file.filename
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
                name=file_name,
                note=note
            )
            await sess.add(table_info)

            # Get ID.
            await sess.flush()
            file_id = table_info.file_id

            return {'file_id': file_id}


        return router


    def build_db(self) -> None:
        """
        Check and build database tables.
        """

        # Set parameter.
        database = self.db_engine.database

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
        self.db_engine.sync_database.build.build(tables=tables, views=views, views_stats=views_stats, skip=True)
