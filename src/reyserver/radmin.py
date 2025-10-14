# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-10-14
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Admin methods.
"""


from typing import Any, Type
from collections.abc import Sequence
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqladmin import Admin, ModelView
from reydb import DatabaseEngineAsync, rorm
from reykit.rbase import Singleton

from .rbase import ServerBase
from . import rserver


__all__ = (
    'ServerAdminModel',
    'ServerAdminModelView',
    'ServerAdminModelViewStats'
)


class ServerAdminModel(ModelView):
    """
    Server admin model type.
    """


class ServerAdminModelView(ServerAdminModel):
    """
    Server admin view model type.
    """

    category = 'View'
    can_view_details = can_edit = can_create = can_delete = False


class ServerAdminModelViewStats(ServerAdminModelView):
    """
    Server admin stats view model type.
    """

    column_list = ['item', 'value', 'comment']


class ServerAdmin(ServerBase, Singleton):
    """
    Server admin type, singleton mode.
    """


    def __init__(self, server: 'rserver.Server') -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        server : Server.
        """

        # Build.
        self.server = server

        ## Admin.
        self.api_admin_binds: dict[ServerAdminModel, DatabaseEngineAsync] = {}
        'Admin API model bind database engine dictionary.'
        Session = async_sessionmaker()
        Session.configure(binds=self.api_admin_binds)
        self.admin = Admin(self.server.app, session_maker=Session)


    def add_model(
        self,
        model: Type[ServerAdminModel] | type[rorm.Model],
        engine: DatabaseEngineAsync | str = None,
        label: str | None = None,
        name: str | None = None,
        column: str | Sequence[str] | None = None,
        **attrs: Any
    ) -> None:
        """
        Add admin model type.

        Parameters
        ----------
        model : Model type.
            - `type[rorm.Model]`: Define as `ServerAdminModel`.
        engine : Database engine or name.
        label : Admin model class label.
        name : Admin model name.
        column : Admin model display column names.
        attrs : Other admin model attributes.
        """

        # Parameter.
        if issubclass(model, rorm.Model):
            class ServerAdminModel_(ServerAdminModel, model=model): ...
            model = ServerAdminModel_
        if type(engine) == str:
            engine = self.server.db[engine]
        if label is not None:
            model.category = label
        if name is not None:
            model.name = model.name_plural = name
        if type(column) == str:
            column = [column]
        if column is not None:
            model.column_list = list(column)
        for key, value in attrs.items():
            setattr(model, key, value)

        # Add.
        self.api_admin_binds[model.model] = engine.engine
        self.admin.add_view(model)


# Simple path.

## Server admin model type.
View = ServerAdminModelView
ViewStats = ServerAdminModelViewStats
