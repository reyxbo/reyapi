# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-08-01 19:46:08
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Ali API methods.
"""


from .rbase import API, APILikeOpenAI, ChatRecordUsage, ChatResponseWeb, ChatRecords


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

    url_api = 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation'
    url_document = 'https://help.aliyun.com/zh/model-studio/use-qwen-by-calling-api?spm=a2c4g.11186623.0.0.330e7d9dSBCaZQ'
    model = 'qwen-turbo'


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
                'content': record['content']
            }
            for record in records
        ]

        # Add.
        json_input = json.setdefault('input', {})
        json_input['messages'] = records
        json_params = json.setdefault('parameters', {})
        json_params['result_format'] = 'message'


    def add_json_web(self, json: dict) -> None:
        """
        Add web parameter to request json.

        Parameters
        ----------
        json : Request JSON.
        """

        # Add.
        json_params = json.setdefault('parameters', {})
        json_params['enable_search'] = True
        json_params['search_options'] = {
            'enable_source': True,
            'enable_citation': True,
            'citation_format': '[<number>]',
            'forced_search': False,
            'search_strategy': 'turbo'
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
            headers['X-DashScope-SSE'] = 'enable'
            json_params = json.setdefault('parameters', {})
            json_params['incremental_output'] = True 


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
        response_reply: str = response_json['output']['choices'][0]['message']['content']

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
        json_output: dict = response_json['output']
        search_info: dict = json_output.get('search_info', {})
        web_data: list[dict] = search_info.get('search_results', [])
        for item in web_data:
            item.setdefault('site_name', None)
            item.setdefault('icon', None)
            item['site'] = item.pop('site_name')
            if item['site'] == '':
                item['site'] = None
            if item['icon'] == '':
                item['icon'] = None
        if web_data == []:
            web_data = None

        return web_data


    def extrac_response_usage(self, response_json: dict) -> ChatRecordUsage:
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
        json_usage = response_json['usage']
        usage_data = {
            'input': json_usage['input_tokens'],
            'output': json_usage['output_tokens'],
            'total': json_usage['total_tokens']
        }

        return usage_data
