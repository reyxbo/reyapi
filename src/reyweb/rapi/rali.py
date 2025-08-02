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

    url_api = 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions'
    url_document = 'https://help.aliyun.com/zh/model-studio/use-qwen-by-calling-api?spm=a2c4g.11186623.0.0.330e7d9dSBCaZQ'
    model = 'qwen-turbo'
