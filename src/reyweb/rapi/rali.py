# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-08-01 19:46:08
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Ali API methods.
"""


from ..rbase import API, APILikeOpenAI


__all__ = (
    'APIAli',
    'APIAliQWen'
)


class APIAli(API):
    """
    Ali API type.
    """


class APIAliQWen(APIAli, APILikeOpenAI):
    """
    Ali Ali QWen type.
    """

    url_api = 'https://qianfan.baidubce.com/v2/chat/completions'
    url_document = 'https://cloud.baidu.com/doc/qianfan-api/s/3m7of64lb'
    model = 'qwen-turbo'
