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
from reykit.rbase import throw
from reykit.rnet import request as reykit_request
from reykit.ros import get_md5
from reykit.rrand import randn

from .rbase import API, APILikeOpenAI, ChatRecordUsage, ChatResponseWeb, ChatRecords


__all__ = (
    'APIBaidu',
    'APIBaiduFanyiLangEnum',
    'APIBaiduFanyiLangAutoEnum',
    'APIBaiduFanyi',
    'APIBaiduErnie'
)


FanyiResponseResult = TypedDict('FanyiResponseResult', {'src': str, 'dst': str})
FanyiResponse = TypedDict('FanyiResponse', {'from': str, 'to': str, 'trans_result': list[FanyiResponseResult]})


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


class APIBaiduFanyi(APIBaidu):
    """
    Baidu Fanyi API type.
    API description: https://fanyi-api.baidu.com/product/113.
    """

    url_api = 'http://api.fanyi.baidu.com/api/trans/vip/translate'
    url_document = 'https://fanyi-api.baidu.com/product/113'
    LangEnum = APIBaiduFanyiLangEnum
    LangAutoEnum = APIBaiduFanyiLangAutoEnum


    def __init__(
        self,
        appid: str,
        appkey: str,
        is_auth: bool = True
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        appid : APP ID.
        appkey : APP key.
        is_auth : Is authorized.
        """

        # Build.
        self.appid = appid
        self.appkey = appkey
        self.is_auth = is_auth


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

        # Get parameter.
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

        # Get parameter.
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


    def translate(
        self,
        text: str,
        from_lang: APIBaiduFanyiLangEnum | APIBaiduFanyiLangAutoEnum = APIBaiduFanyiLangAutoEnum.AUTO,
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
        to_lang : Target language.
            - `None`: When text first character is letter, then is chinese, otherwise is english.

        Returns
        -------
        Translated text.
        """

        # Check.
        max_len = (3000, 6000)[self.is_auth]
        text_len = len(text)
        if len(text) > max_len:
            throw(AssertionError, max_len, text_len)

        # Handle parameter.
        text = text.strip()
        if to_lang is None:
            prefix = tuple('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ')
            if text[0].startswith(prefix):
                to_lang = APIBaiduFanyiLangEnum.ZH
            else:
                to_lang = APIBaiduFanyiLangEnum.EN

        # Request.
        response_dict = self.request(text, from_lang, to_lang)

        # Extract.
        trans_text = '\n'.join(
            [
                trans_text_line_dict['dst']
                for trans_text_line_dict in response_dict['trans_result']
            ]
        )

        return trans_text


    __call__ = translate


class APIBaiduErnie(APIBaidu, APILikeOpenAI):
    """
    Baidu ernie API type.
    """

    url_api = 'https://qianfan.baidubce.com/v2/chat/completions'
    url_document = 'https://cloud.baidu.com/doc/qianfan-api/s/3m7of64lb'
    model = 'ernie-4.5-turbo-32k'


    def add_json_message(self, json: dict, records: ChatRecords) -> None:
        """
        Add messages parameter to request json.

        Parameters
        ----------
        json : Request JSON.
        records : Chat records.
        """

        # Handle parameter.
        records = [
            {
                'role': record['role'],
                **(
                    {}
                    if record['name'] is None
                    else {'name': record['name']}
                ),
                'content': record['content']
            }
            for record in records
        ]

        # Add.
        json['messages'] = records


    def add_json_web(self, json: dict) -> None:
        """
        Add web parameter to request json.

        Parameters
        ----------
        json : Request JSON.
        """

        # Add.
        json['web_search'] = {
            'enable': True,
            'enable_citation': True,
            'enable_trace': True,
            'enable_status': False
        }


    def handle_request(self, headers: dict, json: dict) -> None:
        """
        Handle request headers and json.

        Parameters
        ----------
        headers : Request headers.
        json : Request JOSN.
        """

        # Handle.
        if json.get('stream'):
            json['stream_options'] = {'include_usage': True}


    def extrac_response_reply(self, response_json: dict) -> str:
        """
        Extrac reply text from response JSON.

        Parameters
        ----------
        response_json : Response JSON.

        Returns
        -------
        Reply text.
        """

        # Extrac.
        response_choice: dict = response_json['choices'][0]
        if 'message' in response_choice:
            response_reply: str = response_choice['message']['content']
        elif 'delta' in response_choice:
            response_reply: str = response_choice['delta']['content']
        else:
            throw(AssertionError, response_choice)

        return response_reply


    def extrac_response_web(self, response_json: dict) -> ChatResponseWeb | None:
        """
        Extrac web data from response JSON.

        Parameters
        ----------
        response_json : Response JSON.

        Returns
        -------
        Web data.
        """

        # Extrac.
        web_data: list[dict] = response_json.get('search_results', [])
        for item in web_data:
            item['site'] = None
            item['icon'] = None
        if web_data == []:
            web_data = None

        return web_data


    def extrac_response_usage(self, response_json: dict) -> ChatRecordUsage | None:
        """
        Extrac usage token data from response JSON.

        Parameters
        ----------
        response_json : Response JSON.

        Returns
        -------
        Usage token data.
        """

        # Extrac.
        usage_data: dict | None = response_json.get('usage')
        if usage_data is not None:
            usage_data = {
                'input': usage_data['prompt_tokens'],
                'output': usage_data['completion_tokens'],
                'total': usage_data['total_tokens']
            }

        return usage_data
