# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2025-07-17 22:32:37
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Base methods.
"""


from typing import Any, TypedDict, Literal, Hashable, overload
from collections.abc import Iterable, Generator, Callable
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
type ChatRecordRole = Literal['system', 'user', 'assistant']
ChatRecordUsage = TypedDict('ChatRecordUsage', {'input': int, 'output': int, 'total': int})
ChatResponseWebItem = TypedDict('ChatResponseWebItem', {'site': str | None, 'icon': str | None, 'index': int, 'url': str, 'title': str})
type ChatResponseWeb = list[ChatResponseWebItem]
ChatRecord = TypedDict('ChatRecord', {'role': ChatRecordRole, 'name': str | None, 'content': str, 'usage': ChatRecordUsage | None, 'web': ChatResponseWeb | None})
type ChatRecords = list[ChatRecord]
type ChatRecordsIndex = Hashable
type ChatRecordsData = dict[ChatRecordsIndex, ChatRecords]


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
    add_json_message: Callable[[dict, ChatRecords], Any]
    add_json_web: Callable[[dict], Any]
    add_json_stream: Callable[[dict], Any]
    handle_request: Callable[[dict], Any] | None
    extrac_response_reply: Callable[[dict], str]
    extrac_response_web: Callable[[dict], ChatResponseWeb | None]
    extrac_response_usage: Callable[[dict], ChatRecordUsage | None]


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
        if self.handle_request is not None:
            self.handle_request(headers, json)

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
        index: ChatRecordsIndex | None = None,
        web: bool = False
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
    ) -> tuple[ChatRecord, Generator[str, Any, None]]: ...

    def chat(
        self,
        text: str,
        name: str | None = None,
        index: ChatRecordsIndex | None = None,
        web: bool = False,
        stream: bool = False
    ) -> ChatRecord | tuple[ChatRecord, Generator[str, Any, None]]:
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

        # Get parameter.
        json = {}

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
            chat_record_role = {'role': 'system', 'name': self.name, 'content': self.role, 'usage': None, 'web': None}
            chat_records_update.append(chat_record_role)

        ### Now.
        chat_record_now = {'role': 'user', 'name': name, 'content': text, 'usage': None, 'web': None}
        chat_records_update.append(chat_record_now)
        json_messages: ChatRecords = chat_records + chat_records_update

        self.add_json_message(json, json_messages)

        ## Web.
        if web:
            self.add_json_web(json)

        ## Stream.
        if stream:
            json['stream'] = True

        # Request.
        response = self.request(json)

        # Return.

        ## Stream.
        if stream:
            response_iter: Iterable[str] = response

            ### First.
            for response_line in response_iter:
                if not response_line.startswith(('data:{', 'data: {')):
                    continue
                response_line_first = response_line
                break
            response_line_first = response_line_first[5:]
            response_line_first = response_line_first.strip()
            response_json_first: dict = json_loads(response_line_first)
            response_reply_first = self.extrac_response_reply(response_json_first)
            response_usage_first = self.extrac_response_usage(response_json_first)
            response_web_first = self.extrac_response_web(response_json_first)
            chat_records_reply = {'role': 'assistant', 'content': response_reply_first, 'name': self.name, 'usage': response_usage_first, 'web': response_web_first}

            ### Record.
            if index is not None:
                chat_records_update.append(chat_records_reply)
                chat_records.extend(chat_records_update)


            ### Defin.
            def _generator() -> Generator[str, Any, None]:
                """
                Generator function.

                Returns
                -------
                Generator
                """

                # First.
                yield response_reply_first

                # Next.
                for response_line in response_iter:
                    if not response_line.startswith(('data:{', 'data: {')):
                        continue
                    response_line = response_line[5:]
                    response_line = response_line.strip()
                    response_json: dict = json_loads(response_line)
                    response_reply = self.extrac_response_reply(response_json)
                    response_usage = self.extrac_response_usage(response_json)

                    ## Record.
                    chat_records_reply['content'] += response_reply
                    chat_records_reply['usage'] = response_usage

                    yield response_reply


            generator = _generator()

            return chat_records_reply, generator

        ## Not Stream.
        else:
            response_json: dict = response
            response_reply = self.extrac_response_reply(response_json)
            response_usage = self.extrac_response_usage(response_json)
            response_web = self.extrac_response_web(response_json)
            chat_records_reply = {'role': 'assistant', 'content': response_reply, 'name': self.name, 'usage': response_usage, 'web': response_web}

            ### Record.
            if index is not None:
                chat_records_update.append(chat_records_reply)
                chat_records.extend(chat_records_update)

            return chat_records_reply
