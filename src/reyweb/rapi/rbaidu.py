# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2024-01-11 21:56:56
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Baidu API methods.
"""


from typing import TypedDict
from enum import StrEnum
from reydb import rorm
from reydb.rdb import Database
from reykit.rbase import throw
from reykit.rnet import request as reykit_request
from reykit.ros import get_md5
from reykit.rrand import randn
from reykit.rtext import is_zh
from reykit.rtime import now

from ..rbase import API
from .rdb import APIDatabaseBuild, APIDatabaseRecord


__all__ = (
    'DatabaseTableBaiduTrans',
    'APIBaidu',
    'APIBaiduFanyiLangEnum',
    'APIBaiduFanyiLangAutoEnum',
    'APIBaiduTranslate'
)


FanyiResponseResult = TypedDict('FanyiResponseResult', {'src': str, 'dst': str})
FanyiResponse = TypedDict('FanyiResponse', {'from': str, 'to': str, 'trans_result': list[FanyiResponseResult]})


class DatabaseTableBaiduTrans(rorm.Model, table=True):
    """
    Database `baidu_trans` table model.
    """

    __comment__ = 'Baidu API translate request record table.'
    id: int = rorm.Field(rorm.types_mysql.INTEGER(unsigned=True), key_auto=True, comment='ID.')
    request_time: rorm.Datetime = rorm.Field(not_null=True, comment='Request time.')
    response_time: rorm.Datetime = rorm.Field(not_null=True, comment='Response time.')
    input: str = rorm.Field(rorm.types.VARCHAR(6000), not_null=True, comment='Input original text.')
    output: str = rorm.Field(rorm.types.TEXT, not_null=True, comment='Output translation text.')
    input_lang: str = rorm.Field(rorm.types.VARCHAR(4), not_null=True, comment='Input original text language.')
    output_lang: str = rorm.Field(rorm.types.VARCHAR(3), not_null=True, comment='Output translation text language.')


class APIBaidu(API):
    """
    Baidu API type.
    """


class APIBaiduFanyiLangEnum(APIBaidu, StrEnum):
    """
    Baidu Fanyi APT language enumeration type.
    """

    ZH = 'zh'
    EN = 'en'
    YUE = 'yue'
    KOR = 'kor'
    TH = 'th'
    PT = 'pt'
    EL = 'el'
    BUL = 'bul'
    FIN = 'fin'
    SLO = 'slo'
    CHT = 'cht'
    WYW = 'wyw'
    FRA = 'fra'
    ARA = 'ara'
    DE = 'de'
    NL = 'nl'
    EST = 'est'
    CS = 'cs'
    SWE = 'swe'
    VIE = 'vie'
    JP = 'jp'
    SPA = 'spa'
    RU = 'ru'
    IT = 'it'
    PL = 'pl'
    DAN = 'dan'
    ROM = 'rom'
    HU ='hu'


class APIBaiduFanyiLangAutoEnum(APIBaidu, StrEnum):
    """
    Baidu Fanyi APT language auto type enumeration.
    """

    AUTO = 'auto'


class APIBaiduTranslate(APIBaidu, APIDatabaseBuild):
    """
    Baidu translate API type.
    Can create database used `self.build_db` method.

    Attributes
    ----------
    url_api : API request URL.
    url_doc : API document URL.
    LangEnum : Baidu Fanyi APT language enumeration type.
    LangEnum : Baidu Fanyi APT language auto type enumeration.
    db_names : Database table name mapping dictionary.
    """

    url_api = 'http://api.fanyi.baidu.com/api/trans/vip/translate'
    url_doc = 'https://fanyi-api.baidu.com/product/113'
    LangEnum = APIBaiduFanyiLangEnum
    LangAutoEnum = APIBaiduFanyiLangAutoEnum
    db_names = {
        'baidu_trans': 'baidu_trans',
        'stats_baidu_trans': 'stats_baidu_trans'
    }


    def __init__(
        self,
        appid: str,
        appkey: str,
        db: Database | None = None,
        max_len: int = 6000
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        appid : APP ID.
        appkey : APP key.
        db : `Database` instance, insert request record to table.
        max_len : Maximun length.
        """

        # Build.
        self.appid = appid
        self.appkey = appkey
        self.db = db
        self.max_len = max_len

        # Database.
        self.db_record = APIDatabaseRecord(self, 'api', 'baidu_trans')


    def sign(self, text: str, num: int) -> str:
        """
        Get signature.

        Parameters
        ----------
        text : Text.
        num : Number.

        Returns
        -------
        Signature.
        """

        # Check.
        if text == '':
            throw(ValueError, text)

        # Set parameter.
        num_str = str(num)

        # Sign.
        data = ''.join(
            (
                self.appid,
                text,
                num_str,
                self.appkey
            )
        )
        md5 = get_md5(data)

        return md5


    def request(
        self,
        text: str,
        from_lang: APIBaiduFanyiLangEnum | APIBaiduFanyiLangAutoEnum,
        to_lang: APIBaiduFanyiLangEnum
    ) -> FanyiResponse:
        """
        Request translate API.

        Parameters
        ----------
        text : Text.
        from_lang : Source language.
        to_lang : Target language.

        Returns
        -------
        Response dictionary.
        """

        # Set parameter.
        rand_num = randn(32768, 65536)
        sign = self.sign(text, rand_num)
        params = {
            'q': text,
            'from': from_lang.value,
            'to': to_lang.value,
            'appid': self.appid,
            'salt': rand_num,
            'sign': sign
        }
        headers = {'Content-Type': 'application/x-www-form-urlencoded'}

        # Request.
        response = reykit_request(
            self.url_api,
            params,
            headers=headers,
            check=True
        )

        # Check.
        content_type = response.headers['Content-Type']
        if content_type.startswith('application/json'):
            response_json: dict = response.json()
            if 'error_code' in response_json:
                throw(AssertionError, response_json)
        else:
            throw(AssertionError, content_type)

        return response_json


    def get_lang(self, text: str) -> APIBaiduFanyiLangEnum | None:
        """
        Judge and get text language type.

        Parameters
        ----------
        text : Text.

        Returns
        -------
        Language type or null.
        """

        # Hangle parameter.
        en_chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'

        # Judge.
        for char in text:
            if char in en_chars:
                return APIBaiduFanyiLangEnum.EN
            elif is_zh(char):
                return APIBaiduFanyiLangEnum.ZH


    def trans(
        self,
        text: str,
        from_lang: APIBaiduFanyiLangEnum | APIBaiduFanyiLangAutoEnum | None = None,
        to_lang: APIBaiduFanyiLangEnum | None = None
    ) -> str:
        """
        Translate.

        Parameters
        ----------
        text : Text.
            - `self.is_auth is True`: Maximum length is 6000.
            - `self.is_auth is False`: Maximum length is 3000.
        from_lang : Source language.
            - `None`: Automatic judgment.
        to_lang : Target language.
            - `None`: Automatic judgment.

        Returns
        -------
        Translated text.
        """

        # Check.
        text_len = len(text)
        if len(text) > self.max_len:
            throw(AssertionError, self.max_len, text_len)

        # Set parameter.
        text = text.strip()
        if from_lang is None:
            from_lang = self.get_lang(text)
            from_lang = from_lang or APIBaiduFanyiLangAutoEnum.AUTO
        if to_lang is None:
            if from_lang == APIBaiduFanyiLangEnum.EN:
                to_lang = APIBaiduFanyiLangEnum.ZH
            else:
                to_lang = APIBaiduFanyiLangEnum.EN

        # Request.
        self.db_record['request_time'] = now()
        response_dict = self.request(text, from_lang, to_lang)
        self.db_record['response_time'] = now()

        # Extract.
        trans_text = '\n'.join(
            [
                trans_text_line_dict['dst']
                for trans_text_line_dict in response_dict['trans_result']
            ]
        )

        # Database.
        self.db_record['input'] = text
        self.db_record['output'] = trans_text
        self.db_record['input_lang'] = from_lang
        self.db_record['output_lang'] = to_lang
        self.db_record.record()

        return trans_text


    def build_db(self) -> None:
        """
        Check and build database tables, by `self.db_names`.
        """

        # Check.
        if self.db is None:
            throw(ValueError, self.db)

        # Set parameter.

        ## Table.
        tables = [DatabaseTableBaiduTrans]
        DatabaseTableBaiduTrans._set_name(self.db_names['baidu_trans'])

        ## View stats.
        views_stats = [
            {
                'path': self.db_names['stats_baidu_trans'],
                'items': [
                    {
                        'name': 'count',
                        'select': (
                            'SELECT COUNT(1)\n'
                            f'FROM `{self.db.database}`.`{self.db_names['baidu_trans']}`'
                        ),
                        'comment': 'Request count.'
                    },
                    {
                        'name': 'past_day_count',
                        'select': (
                            'SELECT COUNT(1)\n'
                            f'FROM `{self.db.database}`.`{self.db_names['baidu_trans']}`'
                            'WHERE TIMESTAMPDIFF(DAY, `request_time`, NOW()) = 0'
                        ),
                        'comment': 'Request count in the past day.'
                    },
                    {
                        'name': 'past_week_count',
                        'select': (
                            'SELECT COUNT(1)\n'
                            f'FROM `{self.db.database}`.`{self.db_names['baidu_trans']}`'
                            'WHERE TIMESTAMPDIFF(DAY, `request_time`, NOW()) <= 6'
                        ),
                        'comment': 'Request count in the past week.'
                    },
                    {
                        'name': 'past_month_count',
                        'select': (
                            'SELECT COUNT(1)\n'
                            f'FROM `{self.db.database}`.`{self.db_names['baidu_trans']}`'
                            'WHERE TIMESTAMPDIFF(DAY, `request_time`, NOW()) <= 29'
                        ),
                        'comment': 'Request count in the past month.'
                    },
                    {
                        'name': 'total_input',
                        'select': (
                            'SELECT FORMAT(SUM(LENGTH(`input`)), 0)\n'
                            f'FROM `{self.db.database}`.`{self.db_names['baidu_trans']}`'
                        ),
                        'comment': 'Input original text total character.'
                    },
                    {
                        'name': 'total_output',
                        'select': (
                            'SELECT FORMAT(SUM(LENGTH(`output`)), 0)\n'
                            f'FROM `{self.db.database}`.`{self.db_names['baidu_trans']}`'
                        ),
                        'comment': 'Output translation text total character.'
                    },
                    {
                        'name': 'avg_input',
                        'select': (
                            'SELECT FORMAT(AVG(LENGTH(`input`)), 0)\n'
                            f'FROM `{self.db.database}`.`{self.db_names['baidu_trans']}`'
                        ),
                        'comment': 'Input original text average character.'
                    },
                    {
                        'name': 'avg_output',
                        'select': (
                            'SELECT FORMAT(AVG(LENGTH(`output`)), 0)\n'
                            f'FROM `{self.db.database}`.`{self.db_names['baidu_trans']}`'
                        ),
                        'comment': 'Output translation text average character.'
                    },
                    {
                        'name': 'last_time',
                        'select': (
                            'SELECT MAX(`request_time`)\n'
                            f'FROM `{self.db.database}`.`{self.db_names['baidu_trans']}`'
                        ),
                        'comment': 'Last record request time.'
                    }
                ]
            }
        ]

        # Build.
        self.db.build.build(tables=tables, views_stats=views_stats, skip=True)


    __call__ = trans
