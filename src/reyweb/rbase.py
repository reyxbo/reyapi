# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-07-17 22:32:37
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Base methods.
"""


from typing import Any, TypedDict, NotRequired, Literal, Hashable, overload
from collections.abc import Iterable, Generator
from json import loads as json_loads
from reykit.rbase import throw
from reykit.rnet import request as reykit_request

from reykit.rbase import Base


__all__ = (
    'BaseWeb',
    'API',
    'APILikeOpenAI'
)


# Key 'role' value 'system' only in first.
# Key 'role' value 'user' and 'assistant' can mix.
# Key 'name' is distinguish users.
ChatRecord = TypedDict('ChatRecord', {'role': Literal['system', 'user', 'assistant'], 'content': str, 'name': NotRequired[str]})
type ChatRecords = list[ChatRecord]
type ChatRecordsIndex = Hashable
type ChatRecordsData = dict[ChatRecordsIndex, ChatRecords]
ChatResponseWebItem = TypedDict('ChatResponseWebItem', {'index': int, 'url': str, 'title': str})
type ChatResponseWeb = list[ChatResponseWebItem]


class BaseWeb(Base):
    """
    Web base type.
    """


class API(BaseWeb):
    """
    External API type.
    """


class APILikeOpenAI(API):
    """
    Like OpenAI API type.
    """

    url_api: str
    url_document: str
    model: str


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
            throw(AssertionError, rand)

        # Build.
        self.key = key
        self.auth = 'Bearer ' + key
        self.role = role
        self.name = name
        self.rand = rand
        self.data: ChatRecordsData = {}


    def request(self, json: dict) -> dict | Iterable[str]:
        """
        Request API.

        Parameters
        ----------
        json : Request body.

        Returns
        -------
        Response json or iterable.
            - `Contain key 'stream' value True`: Return `Iterable[bytes]`.
        """

        # Get parameter.
        json['model'] = self.model
        rand: int | None = getattr(self, 'rand', None)
        if rand is not None:
            json['temperature'] = rand
        stream: bool = json.get('stream', False)
        headers = {'Authorization': self.auth, 'Content-Type': 'application/json'}

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


    @overload
    def chat(
        self,
        text: str,
        name: str | None = None,
        index: ChatRecordsIndex | None = None
    ) -> str: ...

    @overload
    def chat(
        self,
        text: str,
        name: str | None = None,
        index: ChatRecordsIndex | None = None,
        *,
        web: Literal[True]
    ) -> tuple[str, ChatResponseWeb]: ...

    @overload
    def chat(
        self,
        text: str,
        name: str | None = None,
        index: ChatRecordsIndex | None = None,
        *,
        stream: Literal[True]
    ) -> Iterable[str]: ...

    @overload
    def chat(
        self,
        text: str,
        name: str | None = None,
        index: ChatRecordsIndex | None = None,
        *,
        web: Literal[True],
        stream: Literal[True]
    ) -> tuple[Iterable[str], ChatResponseWeb]: ...

    def chat(
        self,
        text: str,
        name: str | None = None,
        index: ChatRecordsIndex | None = None,
        web: bool = False,
        stream: bool = False
    ) -> str | tuple[str, ChatResponseWeb] | Iterable[str] | tuple[Iterable[str], ChatResponseWeb]:
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
            - `Literal[True]`: Will not update records, need manual update.

        Returns
        -------
        Response content.
        """

        # Get parameter.
        chat_records_update = []

        ## Record.
        if index is not None:
            chat_records: ChatRecords = self.data.setdefault(index, [])
        else:
            chat_records: ChatRecords = []

        ## New.
        chat_record_role = None
        if (
            chat_records == []
            and self.role is not None
        ):
            chat_record_role = {'role': 'system', 'content': self.role}
            if self.name is not None:
                chat_record_role['name'] = self.name
            chat_records_update.append(chat_record_role)

        ## Now.
        chat_record_now = {'role': 'user', 'content': text}
        if name is not None:
            chat_record_now['name'] = name
        chat_records_update.append(chat_record_now)

        chat_record_role = [chat_record_role]
        json = {'messages': [*chat_records, *chat_records_update]}
        if web:
            json['web_search'] = {
                'enable': True,
                'enable_citation': True,
                'enable_trace': True
            }
        if stream:
            json['stream'] = True

        # Request.
        response = self.request(json)

        # Return.

        ## Stream.
        if stream:
            response_iter: Iterable[str] = response
            response_line_first: str = next(response_iter)
            response_line_first = response_line_first[6:]
            response_json_first: dict = json_loads(response_line_first)
            response_web: ChatResponseWeb = response_json_first.get('search_results', [])
            response_content_first: str = response_json_first['choices'][0]['delta']['content']


            ### Defin.
            def _generator() -> Generator[str, Any, None]:
                """
                Generator function.

                Returns
                -------
                Generator
                """

                # First.
                yield response_content_first

                # Next.
                for response_line in response_iter:
                    if response_line == '':
                        continue
                    elif response_line == 'data: [DONE]':
                        break
                    response_line = response_line[6:]
                    response_json: dict = json_loads(response_line)
                    response_content: str = response_json['choices'][0]['delta']['content']
                    yield response_content


            ### Web.
            generator = _generator()
            if web:
                return generator, response_web

            return generator

        ## Not Stream.
        else:
            response_json: dict = response
            response_content: str = response_json['choices'][0]['message']['content']

            ### Record.
            if index is not None:
                chat_records_reply = {'role': 'assistant', 'content': response_content}
                if self.name is not None:
                    chat_records_reply['name'] = self.name
                chat_records_update.append(chat_records_reply)
                chat_records.extend(chat_records_update)

            ### Web.
            if web:
                response_web: ChatResponseWeb = response_json.get('search_results', [])
                return response_content, response_web

            return response_content
