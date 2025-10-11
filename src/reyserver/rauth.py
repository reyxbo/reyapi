# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-10-10
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Authentication methods.
"""


from fastapi import APIRouter
from reydb import rorm, DatabaseEngine, DatabaseEngineAsync
from reykit.rdata import encode_jwt, decode_jwt, hash_bcrypt, is_hash_bcrypt
from reykit.rtime import now

from .rbase import ServerConfig, Bind, exit_api


__all__ = (
    'DatabaseORMTableUser',
    'DatabaseORMTableRole',
    'DatabaseORMTablePerm',
    'DatabaseORMTableUserRole',
    'DatabaseORMTableRolePerm',
    'build_auth_db',
    'auth_router'
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
    password: str = rorm.Field(rorm.types.CHAR(60), not_null=True, comment='User password, encrypted with "bcrypt".')
    email: rorm.Email = rorm.Field(rorm.types.VARCHAR(255), index_u=True, comment='User email.')
    phone: str = rorm.Field(rorm.types.CHAR(11), index_u=True, comment='User phone.')
    avatar: int = rorm.Field(rorm.types_mysql.MEDIUMINT(unsigned=True), comment='User avatar file ID.')
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
    __comment__ = 'API permission information table.'
    create_time: rorm.Datetime = rorm.Field(field_default=':create_time', not_null=True, index_n=True, comment='Record create time.')
    update_time: rorm.Datetime = rorm.Field(field_default=':update_time', not_null=True, index_n=True, comment='Record update time.')
    perm_id: int = rorm.Field(rorm.types_mysql.SMALLINT(unsigned=True), key_auto=True, comment='Permission ID.')
    name: str = rorm.Field(rorm.types.VARCHAR(50), not_null=True, index_u=True, comment='Permission name.')
    desc: str = rorm.Field(rorm.types.VARCHAR(500), comment='Permission description.')
    method: str = rorm.Field(rorm.types.VARCHAR(7), comment='API request method regular expression "match" pattern.')
    path: str = rorm.Field(rorm.types.VARCHAR(1000), comment='API resource path regular expression "match" pattern.')


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


def build_auth_db(engine: DatabaseEngine | DatabaseEngineAsync) -> None:
    """
    Check and build `auth` database tables.

    Parameters
    ----------
    db : Database engine instance.
    """

    # Set parameter.
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
                    'name': 'user_count',
                    'select': (
                        'SELECT COUNT(1)\n'
                        f'FROM `{database}`.`user`'
                    ),
                    'comment': 'User information count.'
                },
                {
                    'name': 'role_count',
                    'select': (
                        'SELECT COUNT(1)\n'
                        f'FROM `{database}`.`role`'
                    ),
                    'comment': 'Role information count.'
                },
                {
                    'name': 'perm_count',
                    'select': (
                        'SELECT COUNT(1)\n'
                        f'FROM `{database}`.`perm`'
                    ),
                    'comment': 'Permission information count.'
                },
                {
                    'name': 'user_day_count',
                    'select': (
                        'SELECT COUNT(1)\n'
                        f'FROM `{database}`.`user`\n'
                        'WHERE TIMESTAMPDIFF(DAY, `create_time`, NOW()) = 0'
                    ),
                    'comment': 'User information count in the past day.'
                },
                {
                    'name': 'user_week_count',
                    'select': (
                        'SELECT COUNT(1)\n'
                        f'FROM `{database}`.`user`\n'
                        'WHERE TIMESTAMPDIFF(DAY, `create_time`, NOW()) <= 6'
                    ),
                    'comment': 'User information count in the past week.'
                },
                {
                    'name': 'user_month_count',
                    'select': (
                        'SELECT COUNT(1)\n'
                        f'FROM `{database}`.`user`\n'
                        'WHERE TIMESTAMPDIFF(DAY, `create_time`, NOW()) <= 29'
                    ),
                    'comment': 'User information count in the past month.'
                },
                {
                    'name': 'user_last_time',
                    'select': (
                        'SELECT MAX(`create_time`)\n'
                        f'FROM `{database}`.`user`'
                    ),
                    'comment': 'User last record create time.'
                }
            ]
        }
    ]

    # Build.
    engine.sync_engine.build.build(tables=tables, views_stats=views_stats, skip=True)


auth_router = APIRouter()
depend_auth_sess = Bind.create_depend_db('auth', 'sess')
depend_auth_conn = Bind.create_depend_db('auth', 'conn')


@auth_router.post('/sessions')
async def create_sessions(
    username: str = Bind.body,
    password: str = Bind.body,
    conn: Bind.Conn = depend_auth_conn
) -> dict:
    """
    Create session.

    Parameters
    ----------
    username : User name.
    password : User password.

    Returns
    -------
    JSON with `token`.
    """

    # Parameter.
    key = ServerConfig.server.api_auth_key
    password_hash = hash_bcrypt(password)

    # Check.
    sql = (
        ''
    )
    result = await conn.execute(
        sql,
        username=username,
        password_hash=password_hash
    )

    # Check.
    if result.empty:
        exit_api(401)

    # Response.
    json = {
        'time': now('timestamp'),
        'sub': username,
        'iat': now('timestamp'),
        'nbf': now('timestamp'),
        'exp': now('timestamp') + 28800000
    }
    token = encode_jwt(json, key)
    data = {'token': token}

    return data
