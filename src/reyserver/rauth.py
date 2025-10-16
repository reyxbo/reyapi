# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-10-10
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Authentication methods.
"""


from typing import Any, TypedDict, NotRequired, Literal
from datetime import datetime as Datetime
from re import PatternError
from fastapi import APIRouter, Request
from fastapi.params import Depends
from fastapi.security import OAuth2PasswordBearer
from reydb import rorm, DatabaseEngine, DatabaseEngineAsync
from reykit.rdata import encode_jwt, decode_jwt, is_hash_bcrypt
from reykit.rre import search_batch
from reykit.rtime import now

from .rbase import Bind, exit_api


__all__ = (
    'DatabaseORMTableUser',
    'DatabaseORMTableRole',
    'DatabaseORMTablePerm',
    'DatabaseORMTableUserRole',
    'DatabaseORMTableRolePerm',
    'build_db_auth',
    'router_auth'
)


UserInfo = TypedDict(
    'UserInfo',
    {
        'create_time': float,
        'udpate_time': float,
        'user_id': int,
        'user_name': str,
        'role_names': list[str],
        'perm_names': list[str],
        'perm_apis': list[str],
        'email': str | None,
        'phone': str | None,
        'avatar': int | None,
        'password': NotRequired[str]
    }
)
TokenInfo = TypedDict(
    'TokenInfo',
    {
        'sub': int,
        'iat': int,
        'nbf': int,
        'exp': int,
        'user': UserInfo
    }
)
Token = str
ResponseToken = TypedDict(
    'ResponseToken',
    {
        'access_token': Token,
        'token_type': Literal['Bearer']
    }
)


class DatabaseORMTableUser(rorm.Table):
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


class DatabaseORMTableRole(rorm.Table):
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


class DatabaseORMTablePerm(rorm.Table):
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
    api: str = rorm.Field(
        rorm.types.VARCHAR(1000),
        comment=r'API method and resource path regular expression "match" pattern, case insensitive, format is "{method} {path}" (e.g. "GET /users").'
    )


class DatabaseORMTableUserRole(rorm.Table):
    """
    Database `user_role` table ORM model.
    """

    __name__ = 'user_role'
    __comment__ = 'User and role association table.'
    create_time: rorm.Datetime = rorm.Field(field_default=':create_time', not_null=True, index_n=True, comment='Record create time.')
    update_time: rorm.Datetime = rorm.Field(field_default=':update_time', not_null=True, index_n=True, comment='Record update time.')
    user_id: int = rorm.Field(rorm.types_mysql.MEDIUMINT(unsigned=True), key=True, comment='User ID.')
    role_id: int = rorm.Field(rorm.types_mysql.SMALLINT(unsigned=True), key=True, comment='Role ID.')


class DatabaseORMTableRolePerm(rorm.Table):
    """
    Database `role_perm` table ORM model.
    """

    __name__ = 'role_perm'
    __comment__ = 'role and permission association table.'
    create_time: rorm.Datetime = rorm.Field(field_default=':create_time', not_null=True, index_n=True, comment='Record create time.')
    update_time: rorm.Datetime = rorm.Field(field_default=':update_time', not_null=True, index_n=True, comment='Record update time.')
    role_id: int = rorm.Field(rorm.types_mysql.SMALLINT(unsigned=True), key=True, comment='Role ID.')
    perm_id: int = rorm.Field(rorm.types_mysql.SMALLINT(unsigned=True), key=True, comment='Permission ID.')


def build_db_auth(engine: DatabaseEngine | DatabaseEngineAsync) -> None:
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


bearer = OAuth2PasswordBearer(
    tokenUrl='/token',
    scheme_name='RBACBearer',
    description='Global authentication of based on RBAC model and Bearer framework.',
    auto_error=False
)


async def depend_auth(
    request: Request,
    server: Bind.Server = Bind.server,
    token: Token | None = Depends(bearer)
) -> UserInfo:
    """
    Dependencie function of authentication.
    If the verification fails, then response status code is 401 or 403.

    Parameters
    ----------
    request : Request.
    server : Server.
    token : Authentication token.

    Returns
    -------
    User information
    """

    # Check.
    if not server.is_started_auth:
        return
    if bearer is None:
        exit_api(401)

    # Parameter.
    key = server.api_auth_key
    api_path = f'{request.method} {request.url.path}'

    # Cache.
    user: UserInfo | None = getattr(request.state, 'user', None)

    # Decode.
    if user is None:
        json: TokenInfo | None = decode_jwt(token, key)
        if json is None:
            exit_api(401)
        user = json['user']
        request.state.user = user

    # Authentication.
    perm_apis = json['user']['perm_apis']
    perm_apis = [
        f'^{pattern}$'
        for pattern in perm_apis
    ]
    result = search_batch(api_path, *perm_apis)
    if result is None:
        exit_api(403)

    return user


router_auth = APIRouter()


async def get_user_info(
    conn: Bind.Conn,
    account: str,
    account_type: Literal['name', 'email', 'phone'],
    filter_invalid: bool = True
) -> UserInfo | None:
    """
    Get user information.

    Parameters
    ----------
    conn: Asyncronous database connection.
    account : User account.
    account_type : User account type.
        - `Literal['name']`: User name.
        - `Literal['email']`: User Email.
        - `Literal['phone']`: User phone mumber.
    filter_invalid : Whether filter invalid user.

    Returns
    -------
    User information or null.
    """

    # Parameters.
    if filter_invalid:
        sql_where = (
            '    WHERE (\n'
            f'        `{account_type}` = :account\n'
            '        AND `is_valid` = 1\n'
            '    )\n'
        )
    else:
        sql_where = '    WHERE `{account_type}` = :account\n'

    # Get.
    sql = (
        'SELECT ANY_VALUE(`create_time`) AS `create_time`,\n'
        '    ANY_VALUE(`phone`) AS `phone`,\n'
        '    ANY_VALUE(`update_time`) AS `update_time`,\n'
        '    ANY_VALUE(`user`.`user_id`) AS `user_id`,\n'
        '    ANY_VALUE(`user`.`name`) AS `user_name`,\n'
        '    ANY_VALUE(`password`) AS `password`,\n'
        '    ANY_VALUE(`email`) AS `email`,\n'
        '    ANY_VALUE(`avatar`) AS `avatar`,\n'
        "    GROUP_CONCAT(DISTINCT `role`.`name` SEPARATOR ';') AS `role_names`,\n"
        "    GROUP_CONCAT(DISTINCT `perm`.`name` SEPARATOR ';') AS `perm_names`,\n"
        "    GROUP_CONCAT(DISTINCT `perm`.`api` SEPARATOR ';') AS `perm_apis`\n"
        'FROM (\n'
        '    SELECT `create_time`, `update_time`, `user_id`, `password`, `name`, `email`, `phone`, `avatar`\n'
        '    FROM `test`.`user`\n'
        f'{sql_where}'
        ') as `user`\n'
        'LEFT JOIN (\n'
        '    SELECT `user_id`, `role_id`\n'
        '    FROM `test`.`user_role`\n'
        ') as `user_role`\n'
        'ON `user_role`.`user_id` = `user`.`user_id`\n'
        'LEFT JOIN (\n'
        '    SELECT `role_id`, `name`\n'
        '    FROM `test`.`role`\n'
        ') AS `role`\n'
        'ON `user_role`.`role_id` = `role`.`role_id`\n'
        'LEFT JOIN (\n'
        '    SELECT `role_id`, `perm_id`\n'
        '    FROM `test`.`role_perm`\n'
        ') as `role_perm`\n'
        'ON `role_perm`.`role_id` = `role`.`role_id`\n'
        'LEFT JOIN (\n'
        "    SELECT `perm_id`, `name`, `api`\n"
        '    FROM `test`.`perm`\n'
        ') AS `perm`\n'
        'ON `role_perm`.`perm_id` = `perm`.`perm_id`\n'
        'GROUP BY `user_id`'
    )
    result = await conn.execute(
        sql,
        account=account
    )

    # Extract.
    if result.empty:
        info = None
    else:
        row: dict[str, Datetime | Any] = result.to_row()
        info: UserInfo = {
            'create_time': row['create_time'].timestamp(),
            'udpate_time': row['update_time'].timestamp(),
            'user_id': row['user_id'],
            'user_name': row['user_name'],
            'role_names': row['role_names'].split(';'),
            'perm_names': row['perm_names'].split(';'),
            'perm_apis': row['perm_apis'].split(';'),
            'email': row['email'],
            'phone': row['phone'],
            'avatar': row['avatar'],
            'password': row['password']
        }

    return info


@router_auth.post('/token')
async def create_sessions(
    username: str = Bind.i.form,
    password: str = Bind.i.form,
    conn: Bind.Conn = Bind.conn.auth,
    server: Bind.Server = Bind.server
) -> ResponseToken:
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
    key = server.api_auth_key
    sess_seconds = server.api_auth_sess_seconds

    # User information.
    info = await get_user_info(conn, username)

    # Check.
    if info is None:
        exit_api(401)
    password_hash = info.pop('password')
    if not is_hash_bcrypt(password, password_hash):
        exit_api(401)

    # Response.
    now_timestamp_s = now('timestamp_s')
    user_id = info.pop('user_id')
    data: TokenInfo = {
        'sub': str(user_id),
        'iat': now_timestamp_s,
        'nbf': now_timestamp_s,
        'exp': now_timestamp_s + sess_seconds,
        'user': info
    }
    token = encode_jwt(data, key)
    response = {
        'access_token': token,
        'token_type': 'Bearer'
    }

    return response
