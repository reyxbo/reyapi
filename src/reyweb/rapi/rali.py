# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-07-17 22:32:37
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Base methods.
"""


from typing import Any, TypedDict, Literal, Hashable, overload
from collections.abc import Iterable, Generator
from json import loads as json_loads
from reykit.rbase import throw
from reykit.rnet import request as reykit_request
from reykit.rtime import now

from ..rbase import API


__all__ = (
    'APIAli',
    'APIAliQwen'
)


# Key 'role' value 'system' only in first.
# Key 'role' value 'user' and 'assistant' can mix.
# Key 'name' is distinguish users.
type ChatRecordRole = Literal['system', 'user', 'assistant']
ChatRecordUsage = TypedDict('ChatRecordUsage', {'input': int, 'output': int, 'total': int, 'output_think': int | None})
ChatResponseWebItem = TypedDict('ChatResponseWebItem', {'site': str | None, 'icon': str | None, 'index': int, 'url': str, 'title': str})
type ChatResponseWeb = list[ChatResponseWebItem]
ChatRecord = TypedDict(
    'ChatRecord',
    {
        'time': int,
        'role': ChatRecordRole,
        'name': str | None,
        'content': str | None,
        'usage': ChatRecordUsage | None,
        'web': ChatResponseWeb | None,
        'think': str | None
    }
)
type ChatRecords = list[ChatRecord]
type ChatRecordsIndex = Hashable
type ChatRecordsData = dict[ChatRecordsIndex, ChatRecords]
ChatReplyGenerator = Generator[str, Any, None]
ChatThinkGenerator = Generator[str, Any, None]


class APIAli(API):
    """
    Ali API type.
    """


class APIAliQwen(APIAli):
    """
    Ali Ali QWen type.
    """

    url_api = 'https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation'
    url_document = 'https://help.aliyun.com/zh/model-studio/use-qwen-by-calling-api?spm=a2c4g.11186623.0.0.330e7d9dSBCaZQ'
    model = 'qwen-turbo-latest'


    def __init__(
        self,
        key: str,
        role: str | None = None,
        name: str | None = None,
        rand: float = 1
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        key : API key.
        role : AI role description.
        name : AI role name.
        rand : Randomness, value range is `[0,2)`.
        """

        # Check.
        if not 0 <= rand < 2:
            throw(ValueError, rand)

        # Build.
        self.key = key
        self.auth = 'Bearer ' + key
        self.role = role
        self.name = name
        self.rand = rand
        self.data: ChatRecordsData = {}


    @overload
    def request(self, json: dict, stream: Literal[True]) -> Iterable[str]: ...

    @overload
    def request(self, json: dict, stream: Literal[False]) -> dict: ...

    def request(self, json: dict, stream: bool) -> dict | Iterable[str]:
        """
        Request API.

        Parameters
        ----------
        json : Request body.
        stream : Whether use stream response.

        Returns
        -------
        Response json or iterable.
        """

        # Handle parameter.
        json['model'] = self.model
        json['temperature'] = self.rand
        headers = {'Authorization': self.auth, 'Content-Type': 'application/json'}
        if stream:
            headers['X-DashScope-SSE'] = 'enable'
            json_params = json.setdefault('parameters', {})
            json_params['incremental_output'] = True

        # Request.
        response = reykit_request(
            self.url_api,
            json=json,
            headers=headers,
            stream=stream,
            check=True
        )

        # Stream.
        if stream:
            iterable: Iterable[str] = response.iter_lines(decode_unicode=True)
            return iterable

        # Check.
        content_type = response.headers['Content-Type']
        if content_type.startswith('application/json'):
            response_json: dict = response.json()
            if 'code' in response_json:
                throw(AssertionError, response_json)
        else:
            throw(AssertionError, content_type)

        return response_json


    def extract_response_text(self, response_json: dict) -> str | None:
        """
        Extract reply text from response JSON.

        Parameters
        ----------
        response_json : Response JSON.

        Returns
        -------
        Reply text.
        """

        # Extract.
        response_text: str = response_json['output']['choices'][0]['message']['content']
        response_text = response_text or None

        return response_text


    def extract_response_usage(self, response_json: dict) -> ChatRecordUsage | None:
        """
        Extract usage token data from response JSON.

        Parameters
        ----------
        response_json : Response JSON.

        Returns
        -------
        Usage token data.
        """

        # Extract.
        usage_data: dict | None = response_json.get('usage')
        if usage_data is not None:
            usage_data_think: dict | None = usage_data.get('output_tokens_details', {})
            output_think: int | None = usage_data_think.get('reasoning_tokens')
            usage_data = {
                'input': usage_data['input_tokens'],
                'output': usage_data['output_tokens'],
                'total': usage_data['total_tokens'],
                'output_think': output_think
            }

        return usage_data


    def extract_response_web(self, response_json: dict) -> ChatResponseWeb | None:
        """
        Extract web data from response JSON.

        Parameters
        ----------
        response_json : Response JSON.

        Returns
        -------
        Web data.
        """

        # Extract.
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
        web_data = web_data or None

        return web_data


    def extract_response_think(self, response_json: dict) -> str | None:
        """
        Extract deep think text from response JSON.

        Parameters
        ----------
        response_json : Response JSON.

        Returns
        -------
        Deep think text.
        """

        # Extract.
        json_message: dict = response_json['output']['choices'][0]['message']
        response_think = json_message.get('reasoning_content')
        response_think = response_think or None

        return response_think


    def extract_response_record(self, response_json: dict) -> ChatRecord:
        """
        Extract reply record from response JSON.

        Parameters
        ----------
        response_json : Response JSON.

        Returns
        -------
        Reply record.
        """

        # Extract.
        response_text = self.extract_response_text(response_json)
        response_usage = self.extract_response_usage(response_json)
        response_web = self.extract_response_web(response_json)
        response_think = self.extract_response_think(response_json)
        chat_records_reply = {'time': now('timestamp'), 'role': 'assistant', 'content': response_text, 'name': self.name, 'usage': response_usage, 'web': response_web, 'think': response_think}

        return chat_records_reply


    def extract_response_generator(self, response_iter: Iterable[str]):
        """
        Extract reply generator from response JSON.

        Parameters
        ----------
        response_iter : Response iterable.

        Returns
        -------
        Reply Generator.
        """

        # First.
        response_line_first = None
        for response_line in response_iter:
            if not response_line.startswith(('data:{', 'data: {')):
                continue
            response_line_first = response_line
            break
        
        ## Check.
        if response_line_first is None:
            throw(AssertionError, response_line_first)

        response_line_first = response_line_first[5:].strip()
        response_json_first: dict = json_loads(response_line_first)
        chat_records_reply = self.extract_response_record(response_json_first)
        is_think_emptied = not bool(chat_records_reply['think'])

        ### Define.
        def _generator(mode: Literal['text', 'think']) -> Generator[str, Any, None]:
            """
            Generator function of stream response.

            Parameters
            ----------
            mode : Generate value type.
                - `Literal['text']`: Reply text.
                - `Literal['think']`: Deep think text.

            Returns
            -------
            Generator.
            """

            # Handle parameter.
            nonlocal is_think_emptied
            chat_records_reply['content'] = chat_records_reply['content'] or ''
            chat_records_reply['think'] = chat_records_reply['think'] or ''

            # Check.
            if (
                not is_think_emptied
                and mode == 'text'
            ):
                text = 'must first used up think generator'
                throw(AssertionError, text=text)

            # First.
            if mode == 'text':
                yield chat_records_reply['content']
            elif mode == 'think':
                yield chat_records_reply['think']

            # Next.
            for response_line in response_iter:

                ## Filter.
                if not response_line.startswith(('data:{', 'data: {')):
                    continue

                ## JSON.
                response_line = response_line[5:]
                response_line = response_line.strip()
                response_json: dict = json_loads(response_line)

                ## Usage.
                response_usage = self.extract_response_usage(response_json)
                chat_records_reply['usage'] = response_usage

                ## Web.
                if chat_records_reply['web'] is None:
                    response_web = self.extract_response_web(response_json)
                    chat_records_reply['web'] = response_web

                ## Text.
                if mode == 'text':
                    response_text = self.extract_response_text(response_json)
                    if response_text is None:
                        continue
                    chat_records_reply['content'] += response_text
                    yield response_text

                ## Think.
                elif mode == 'think':
                    response_think = self.extract_response_think(response_json)

                    ### Last.
                    if response_think is None:
                        is_think_emptied = True
                        chat_records_reply['content'] = self.extract_response_text(response_json)
                        break

                    chat_records_reply['think'] += response_think
                    yield response_think


        generator_text = _generator('text')
        generator_think = _generator('think')

        return chat_records_reply, generator_text, generator_think


    @overload
    def chat(
        self,
        text: str,
        name: str | None = None,
        index: ChatRecordsIndex | None = None,
        web: bool = False,
        think: bool = False
    ) -> ChatRecord: ...

    @overload
    def chat(
        self,
        text: str,
        name: str | None = None,
        index: ChatRecordsIndex | None = None,
        web: bool = False,
        *,
        stream: Literal[True]
    ) -> tuple[ChatRecord, ChatReplyGenerator]: ...

    @overload
    def chat(
        self,
        text: str,
        name: str | None = None,
        index: ChatRecordsIndex | None = None,
        web: bool = False,
        *,
        think: Literal[True],
        stream: Literal[True]
    ) -> tuple[ChatRecord, ChatReplyGenerator, ChatThinkGenerator]: ...

    def chat(
        self,
        text: str,
        name: str | None = None,
        index: ChatRecordsIndex | None = None,
        web: bool = False,
        think: bool = False,
        stream: bool = False
    ) -> ChatRecord | tuple[ChatRecord, ChatReplyGenerator] | tuple[ChatRecord, ChatReplyGenerator, ChatThinkGenerator]:
        """
        Chat with AI.

        Parameters
        ----------
        text : User chat text.
        name : User name.
        index : Chat records index.
            `None`: Not use record.
        web : Whether use web search.
        think : Whether use deep think.
        stream : Whether use stream response.

        Returns
        -------
        Response content.
        """

        # Check.
        if text == '':
            throw(ValueError, text)

        # Handle parameter.
        json = {'input': {}, 'parameters': {}}

        ## Message.
        chat_records_update: ChatRecords = []
        if index is not None:
            chat_records: ChatRecords = self.data.setdefault(index, [])
        else:
            chat_records: ChatRecords = []

        ### New.
        chat_record_role = None
        if (
            chat_records == []
            and self.role is not None
        ):
            chat_record_role = {'time': now('timestamp'), 'role': 'system', 'name': self.name, 'content': self.role, 'usage': None, 'web': None, 'think': None}
            chat_records_update.append(chat_record_role)

        ### Now.
        chat_record_now = {'time': now('timestamp'), 'role': 'user', 'name': name, 'content': text, 'usage': None, 'web': None, 'think': None}
        chat_records_update.append(chat_record_now)

        messages: ChatRecords = chat_records + chat_records_update
        records = [
            {
                'role': message['role'],
                'content': message['content']
            }
            for message in messages
        ]

        # Add.
        json['input']['messages'] = records
        json['parameters']['result_format'] = 'message'

        ## Web.
        if web:
            json['parameters']['enable_search'] = True
            json['parameters']['search_options'] = {
                'enable_source': True,
                'enable_citation': True,
                'citation_format': '[<number>]',
                'forced_search': False,
                'search_strategy': 'turbo'
            }
        else:
            json['parameters']['enable_search'] = False

        ## Think.
        json['parameters']['enable_thinking'] = think

        ## Stream.
        json['stream'] = stream

        # Request.
        response = self.request(json, stream)

        # Extract.

        ## Stream.
        if stream:
            response_iter: Iterable[str] = response
            chat_records_reply, generator_text, generator_think = self.extract_response_generator(response_iter)

        ## Not Stream.
        else:
            response_json: dict = response
            chat_records_reply = self.extract_response_record(response_json)

        # Record.
        if index is not None:
            chat_records_update.append(chat_records_reply)
            chat_records.extend(chat_records_update)

        # Return.
        if stream:
            if think:
                return chat_records_reply, generator_text, generator_think
            else:
                return chat_records_reply, generator_text
        else:
            return chat_records_reply


    def modify(self, text: str) -> str:
        """
        Let AI modify text.

        Parameters
        ----------
        text : Text.

        Returns
        -------
        Modified text.
        """

        # Handle parameter.
        text = '润色冒号后的内容（注意！只返回润色后的内容正文，之后会直接整段使用）：' + text
        record = self.chat(text)
        result: str = record['content']
        result = result.strip()

        return result


    __call__ = chat
