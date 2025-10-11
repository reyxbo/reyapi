# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-10-10
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Authentication methods.
"""


from typing import Literal
from fastapi import APIRouter
from reydb import rorm, DatabaseEngine, DatabaseEngineAsync
# from reykit.rdata import encode_jwt, is_hash_bcrypt
# from reykit.rtime import now

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
    api: str = rorm.Field(rorm.types.VARCHAR(1000), comment='API resource path regular expression "match" pattern.')


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
    account: str = Bind.i.body,
    password: str = Bind.i.body,
    account_type: Literal['name', 'email', 'phone'] = Bind.Body('name'),
    conn: Bind.Conn = depend_auth_conn
) -> dict:
    """
    Create session.

    Parameters
    ----------
    account : User account, name or email or phone.
    password : User password.
    account_type : User account type.

    Returns
    -------
    JSON with `token`.
    """

    # Parameter.
    key = ServerConfig.server.api_auth_key
    sess_seconds = ServerConfig.server.api_auth_sess_seconds

    # Check.
    sql = (
        'SELECT ANY_VALUE(`create_time`) AS `create_time`,\n'
        '    ANY_VALUE(`update_time`) AS `update_time`,\n'
        '    ANY_VALUE(`user`.`user_id`) AS `user_id`,\n'
        '    ANY_VALUE(`user`.`name`) AS `user_name`,\n'
        '    ANY_VALUE(`password`) AS `password`,\n'
        '    ANY_VALUE(`email`) AS `email`,\n'
        '    ANY_VALUE(`phone`) AS `phone`,\n'
        '    ANY_VALUE(`avatar`) AS `avatar`,\n'
        "    GROUP_CONCAT(DISTINCT `role`.`name` SEPARATOR ';') AS `role_names`,\n"
        "    GROUP_CONCAT(DISTINCT `perm`.`name` SEPARATOR ';') AS `perm_names`,\n"
        "    GROUP_CONCAT(DISTINCT `perm`.`api` SEPARATOR ';') AS `perm_apis`\n"
        'FROM (\n'
        '    SELECT `create_time`, `update_time`, `user_id`, `password`, `name`, `email`, `phone`, `avatar`\n'
        '    FROM `test`.`user`\n'
        f'    WHERE `{account_type}` = :account\n'
        '    LIMIT 1\n'
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
        "    SELECT `perm_id`, `name`, CONCAT(`method`, ':', `path`) as `api`\n"
        '    FROM `test`.`perm`\n'
        ') AS `perm`\n'
        'ON `role_perm`.`perm_id` = `perm`.`perm_id`'
    )
    print(1111111111111)
    result = await conn.execute(
        sql,
        account=account
    )
    print(result.fetchall())
    return {'message': 'ok'}

    # # Check.
    # table = result.to_table()
    # print(table)
    # if table == []:
    #     exit_api(401)
    # json = table[0]
    # if not is_hash_bcrypt(password, json['password']):
    #     exit_api(401)

    # # JWT.
    # now_timestamp_s = now('timestamp_s')
    # json['sub'] = json.pop('user_id')
    # json['iat'] = now_timestamp_s
    # json['nbf'] = now_timestamp_s
    # json['exp'] = now_timestamp_s + sess_seconds
    # json['role_names'] = json['role_names'].split(';')
    # json['perm_names'] = json['perm_names'].split(';')
    # perm_apis: list[str] = json['perm_apis'].split(';')
    # perm_api_dict = {}
    # for perm_api in perm_apis:
    #     for method, path in perm_api.split(':', 1):
    #         paths: list = perm_api_dict.setdefault(method, [])
    #         paths.append(path)
    # json['perm_apis'] = perm_api_dict
    # token = encode_jwt(json, key)
    # data = {'token': token}
    # print(111111, data)
    # return data
