# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-08-17 22:12:34
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : API base methods.
"""


from typing import Any
from threading import get_ident as threading_get_ident
from reydb.rdb import Database

from ..rbase import BaseWeb


__all__ = (
    'BaseAPI',
    'API',
    'APIDBRecord'
)


class BaseAPI(BaseWeb):
    """
    External API base type.
    """


class API(BaseAPI):
    """
    External API type.
    """

    url_api: str
    url_document: str
    database: Database | None
    db_names: dict[str, str]


class APIDBRecord(BaseAPI):
    """
    External API database record type, can multi threaded.
    """


    def __init__(
        self,
        api: API | None = None,
        database_index: str | None = None,
        table_index: str | None = None
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        api : `API` instance.
            - `None`: Not record.
        database_index : Index `API.db_names` database name.
        table_index : Index `API.db_names` table name.
        """

        # Build.
        self.api = api
        self.database = database_index
        self.table = table_index
        self.data: dict[int, dict[str, Any]] = {}


    def __setitem__(self, key: str, value: Any) -> None:
        """
        Update record data parameter.

        Parameters
        ----------
        key : Parameter key.
        value : Parameter value.
        """

        # Check.
        if self.api.database is None:
            return

        # Handle parameter.
        thread_id = threading_get_ident()
        record = self.data.setdefault(thread_id, {})

        # Update.
        record[key] = value


    def insert(self) -> None:
        """
        Insert record to table of database.
        """

        # Check.
        if self.api.database is None:
            return

        # Handle parameter.
        thread_id = threading_get_ident()
        record = self.data.setdefault(thread_id, {})
        path = (
            self.api.db_names[self.database],
            self.api.db_names[self.table]
        )

        # Insert.
        self.api.database.execute_insert(path, record)

        # Delete.
        del self.data[thread_id]
