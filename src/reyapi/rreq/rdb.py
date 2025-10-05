# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-08-17 22:12:34
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : API database methods.
"""


from typing import Any
from types import MethodType
from threading import get_ident as threading_get_ident
from reydb.rdb import Database

from ..rbase import RequestAPI


__all__ = (
    'APIReuqestDatabaseBuild',
    'APIRequestDatabaseRecord'
)


class APIReuqestDatabaseBuild(RequestAPI):
    """
    Reuqest external API with database build method type.
    Can create database used `self.build_db` method.
    """

    db: Database | None
    db_names: dict[str, str]
    build_db: MethodType


class APIRequestDatabaseRecord(RequestAPI):
    """
    Request external API database record type, can multi threaded.
    """


    def __init__(
        self,
        api: APIReuqestDatabaseBuild | None = None,
        database: str | None = None,
        table: str | None = None
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        api : `API` instance.
            - `None`: Not record.
        database : Index `API.db_names` database name.
        table : Index `API.db_names` table name.
        """

        # Build.
        self.api = api
        self.database = database
        self.table = table
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
        if self.api.db is None:
            return

        # Parameter.
        thread_id = threading_get_ident()
        record = self.data.setdefault(thread_id, {})

        # Update.
        record[key] = value


    def record(self) -> None:
        """
        Insert record to table of database.
        """

        # Check.
        if self.api.db is None:
            return

        # Parameter.
        thread_id = threading_get_ident()
        record = self.data.setdefault(thread_id, {})
        table = self.api.db_names[self.table]

        # Insert.
        self.api.db.execute.insert(table, record)

        # Delete.
        del self.data[thread_id]
