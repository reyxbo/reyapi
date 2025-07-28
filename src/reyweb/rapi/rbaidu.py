# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2024-01-11 21:56:56
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Baidu API methods.
"""


from typing import Any, TypedDict, Literal
from datetime import datetime, timedelta
from requests import Response
from uuid import uuid1
from reykit.rbase import Base, warn, catch_exc
from reykit.rnet import request as reytool_request
from reykit.ros import File
from reykit.rrand import randi
from reykit.rtime import now, wait

from ..rbase import API


__all__ = (
    'APIBaidu',
    'APIBaiduChat',
    'APIBaiduImage',
    'APIBaiduVoice'
)


CallRecord = TypedDict('CallRecord', {'time': datetime, 'data': Any})
ChatRecord = TypedDict('ChatRecord', {'time': datetime, 'send': str, 'receive': str})
HistoryMessage = TypedDict('HistoryMessage', {'role': str, 'content': str})


class APIBaidu(API):
    """
    Baidu API type.
    """


    def __init__(
        self,
        key: str,
        secret: str,
        token_valid_seconds: float = 43200
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        key : API key.
        secret : API secret.
        token_valid_seconds : Authorization token vaild seconds.
        """

        # Set attribute.
        self.key = key
        self.secret = secret
        self.token_valid_seconds = token_valid_seconds
        self.cuid = uuid1()
        self.call_records: list[CallRecord] = []
        self.start_time = now()


    def get_token(self) -> str:
        """
        Get token.

        Returns
        -------
        Token.
        """

        # Get parameter.
        url = 'https://aip.baidubce.com/oauth/2.0/token'
        params = {
            'grant_type': 'client_credentials',
            'client_id': self.key,
            'client_secret': self.secret
        }

        # Request.
        response = self.request(
            url,
            params,
            method='post'
        )

        # Extract.
        response_json = response.json()
        token = response_json['access_token']

        return token


    @property
    def token(self) -> str:
        """
        Get authorization token.
        """

        # Get parameter.
        if hasattr(self, 'token_time'):
            token_time: datetime = getattr(self, 'token_time')
        else:
            token_time = None
        if (
            token_time is None
            or (now() - token_time).seconds > self.token_valid_seconds
        ):
            self.token_time = now()
            self._token = self.get_token()

        return self._token


    def request(
        self,
        *args: Any,
        **kwargs: Any
    ) -> Response:
        """
        Request.

        Parameters
        ----------
        args : Position arguments of function.
        kwargs : Keyword arguments of function.

        Returns
        -------
        `Response` instance.
        """

        # Request.
        response = reytool_request(*args, **kwargs)

        # Check.
        content_type = response.headers['Content-Type']
        if content_type.startswith('application/json'):
            response_json: dict = response.json()
            if 'error_code' in response_json:
                raise AssertionError('Baidu API request failed', response_json)

        return response


    def record_call(
        self,
        **data: Any
    ) -> None:
        """
        Record call.

        Parameters
        ----------
        data : Record data.
        """

        # Get parameter.
        record = {
            'time': now(),
            'data': data
        }

        # Record.
        self.call_records.append(record)


    @property
    def interval(self) -> float:
        """
        Return the interval seconds from last call.
        When no record, then return the interval seconds from start.

        Returns
        -------
        Interval seconds.
        """

        # Get parameter.
        if self.call_records == []:
            last_time = self.start_time
        else:
            last_time: datetime = self.call_records[-1]['time']

        # Count.
        now_time = now()
        interval_time = now_time - last_time
        interval_seconds = interval_time.total_seconds()

        return interval_seconds


class APIBaiduChat(APIBaidu):
    """
    Baidu API chat type.
    """

    # Character.
    characters = (
        '善良', '淳厚', '淳朴', '豁达', '开朗', '体贴', '活跃', '慈祥', '仁慈', '温和',
        '温存', '和蔼', '和气', '直爽', '耿直', '憨直', '敦厚', '正直', '爽直', '率直',
        '刚直', '正派', '刚正', '纯正', '廉政', '清廉', '自信', '信心', '新年', '相信',
        '老实', '谦恭', '谦虚', '谦逊', '自谦', '谦和', '坚强', '顽强', '建议', '刚毅',
        '刚强', '倔强', '强悍', '刚毅', '减震', '坚定', '坚韧', '坚决', '坚忍', '勇敢',
        '勇猛', '勤劳', '勤恳', '勤奋', '勤勉', '勤快', '勤俭', '辛勤', '刻苦', '节约',
        '狂妄', '骄横', '骄纵', '窘态', '窘迫', '困窘', '难堪', '害羞', '羞涩', '赧然',
        '无语', '羞赧'
    )


    def __init__(
        self,
        key: str,
        secret: str,
        character: str | None = None
    ) -> None:
        """
        Build instance attributes.

        Parameters
        ----------
        key : API key.
        secret : API secret.
        Character : Character of language model.
        """

        # Set attribute.
        super().__init__(key, secret)
        self.chat_records: dict[str, ChatRecord] = {}
        self.character=character


    def chat(
        self,
        text: str,
        character: str | Literal[False] | None = None,
        history_key: str | None = None,
        history_recent_seconds: float = 1800,
        history_max_word: int = 400
    ) -> bytes:
        """
        Chat with language model.

        Parameters
        ----------
        text : Text.
        Character : Character of language model.
            - `None`, Use `self.character`: attribute.
            - `str`: Use this value.
            - `Literal[False]`: Do not set.
        Character : Character of language model.
        history_key : Chat history records key.
        history_recent_seconds : Limit recent seconds of chat history.
        history_max_word : Limit maximum word of chat history.

        Returns
        -------
        Reply text.
        """

        # Get parameter.
        url = 'https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions_pro'
        params = {'access_token': self.token}
        headers = {'Content-Type': 'application/json'}
        if history_key is None:
            messages = []
        else:
            messages = self.history_messages(
                history_key,
                history_recent_seconds,
                history_max_word
            )
        message = {'role': 'user', 'content': text}
        messages.append(message)
        json = {'messages': messages}
        match character:
            case None:
                character = self.character
            case False:
                character = None
        if character is not None:
            json['system'] = character

        # Request.
        try:
            response = self.request(
                url,
                params=params,
                json=json,
                headers=headers
            )

        ## Parameter 'system' error.
        except:
            *_, exc_instance, _ = catch_exc()
            error_code = exc_instance.args[1]['error_code']
            if error_code == 336104:
                result = self.chat(
                    text,
                    False,
                    history_key,
                    history_recent_seconds,
                    history_max_word
                )
                return result
            else:
                raise

        # Extract.
        response_json: dict = response.json()
        result: str = response_json['result']

        # Record.
        self.record_call(
            messages=messages,
            character=character
        )
        if history_key is not None:
            self.record_chat(
                text,
                result,
                history_key
            )

        return result


    def record_chat(
        self,
        send: str,
        receive: str,
        key: str
    ) -> None:
        """
        Record chat.

        Parameters
        ----------
        send : Send text.
        receive : Receive text.
        key : Chat history records key.
        """

        # Generate.
        record = {
            'time': now(),
            'send': send,
            'receive': receive
        }

        # Record.
        reocrds = self.chat_records.get(key)
        if reocrds is None:
            self.chat_records[key] = [record]
        else:
            reocrds.append(record)


    def history_messages(
        self,
        key: str,
        recent_seconds: float,
        max_word: int
    ) -> list[HistoryMessage]:
        """
        Return history messages.

        Parameters
        ----------
        key : Chat history records key.
        recent_seconds : Limit recent seconds of chat history.
        max_word : Limit maximum word of chat history.

        Returns
        -------
        History messages.
        """

        # Get parameter.
        records = self.chat_records.get(key, [])
        now_time = now()

        # Generate.
        messages = []
        word_count = 0
        for record in records:

            ## Limit time.
            interval_time: timedelta = now_time - record['time']
            interval_seconds = interval_time.total_seconds()
            if interval_seconds > recent_seconds:
                break

            ## Limit word.
            word_len = len(record['send']) + len(record['receive'])
            character_len = len(self.character)
            word_count += word_len
            if word_count + character_len > max_word:
                break

            ## Append.
            message = [
                {'role': 'user', 'content': record['send']},
                {'role': 'assistant', 'content': record['receive']}
            ]
            messages.extend(message)

        return messages


    def interval_chat(
        self,
        key: str
    ) -> float:
        """
        Return the interval seconds from last chat.
        When no record, then return the interval seconds from start.

        Parameters
        ----------
        key : Chat history records key.

        Returns
        -------
        Interval seconds.
        """

        # Get parameter.
        records = self.chat_records.get(key)
        if records is None:
            last_time = self.start_time
        else:
            last_time: datetime = records[-1]['time']
        if self.call_records == []:
            last_time = self.start_time
        else:
            last_time: datetime = self.call_records[-1]['time']

        # Count.
        now_time = now()
        interval_time = now_time - last_time
        interval_seconds = interval_time.total_seconds()

        return interval_seconds


    def modify(
        self,
        text: str
    ) -> str:
        """
        Modify text.
        """

        # Get parameter.
        character = randi(self.characters)

        # Modify.
        text = '用%s的语气，润色以下这句话\n%s' % (character, text)
        text_modify = self.chat(text)

        return text_modify


class APIBaiduImage(APIBaidu):
    """
    Baidu API image type.
    """


    def _to_url_create_task(
        self,
        text: str
    ) -> str:
        """
        Create task of generate image URL from text.

        Parameters
        ----------
        text : Text, length cannot exceed 60.

        Returns
        -------
        Task ID.
        """

        # Get parameter.
        url = 'https://aip.baidubce.com/rpc/2.0/ernievilg/v1/txt2imgv2'
        params = {'access_token': self.token}
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        json = {
            'prompt': text,
            'width': 1024,
            'height': 1024
        }

        # Request.
        response = self.request(
            url,
            params=params,
            json=json,
            headers=headers
        )

        # Record.
        self.record_call(text=text)

        # Extract.
        response_json: dict = response.json()
        task_id: str = response_json['data']['task_id']

        return task_id


    def _to_url_query_task(
        self,
        task_id: str
    ) -> dict:
        """
        Query task of generate image URL from text.

        Parameters
        ----------
        task_id : Task ID.

        Returns
        -------
        Task information.
        """

        # Get parameter.
        url = 'https://aip.baidubce.com/rpc/2.0/ernievilg/v1/getImgv2'
        params = {'access_token': self.token}
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        json = {'task_id': task_id}

        # Request.
        response = self.request(
            url,
            params=params,
            json=json,
            headers=headers
        )

        # Extract.
        response_json: dict = response.json()
        task_info: dict = response_json['data']

        return task_info


    def to_url(
        self,
        text: str,
        path: str | None = None
    ) -> str:
        """
        Generate image URL from text.

        Parameters
        ----------
        text : Text, length cannot exceed 60.
        path : File save path.
            - `None`: Not save.

        Returns
        -------
        Image URL.
        """

        # Create.
        task_id = self._to_url_create_task(text)

        # Wait.
        store = {}


        ## Define.
        def is_task_success() -> bool:
            """
            Whether if is task successed.

            Returns
            -------
            Judge result.
            """

            # Query.
            task_info = self._to_url_query_task(task_id)

            # Judge.
            match task_info['task_status']:
                case 'RUNNING':
                    return False
                case 'SUCCESS':
                    store['url'] = task_info['sub_task_result_list'][0]['final_image_list'][0]['img_url']
                    return True
                case _:
                    raise AssertionError('Baidu API text to image task failed')


        ## Start.
        wait(
            is_task_success,
            _interval=0.5,
            _timeout=600
        )

        ## Extract.
        url = store['url']

        # Save.
        if path is not None:
            response = self.request(url)
            rfile = File(path)
            rfile.write(response.content)

        return url


class APIBaiduVoice(APIBaidu):
    """
    Baidu API voice type.
    """


    def to_file(
        self,
        text: str,
        path: str | None = None
    ) -> bytes:
        """
        Generate voice file from text.

        Parameters
        ----------
        text : Text, length cannot exceed 60.
        path : File save path.
            - `None`: Not save.

        Returns
        -------
        Voice bytes data.
        """

        # Check.
        if len(text) > 60:
            text = text[:60]
            warn('parameter "text" length cannot exceed 60')

        # Get parameter.
        url = 'https://tsn.baidu.com/text2audio'
        headers = {
            'Accept': '*/*',
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        data = {
            'tok': self.token,
            'tex': text,
            'cuid': self.cuid,
            'ctp': 1,
            'lan': 'zh',
            'spd': 5,
            'pit': 5,
            'vol': 5,
            'per': 4,
            'aue': 3
        }

        # Request.
        response = self.request(
            url,
            data=data,
            headers=headers
        )

        # Record.
        self.record_call(
            text=text,
            path=path
        )

        # Extract.
        file_bytes = response.content

        # Save.
        if path is not None:
            rfile = File(path)
            rfile.write(file_bytes)

        return file_bytes


    def _to_url_create_task(
        self,
        text: str
    ) -> str:
        """
        Create task of generate voice URL from text.

        Parameters
        ----------
        text : Text, length cannot exceed 60.

        Returns
        -------
        Task ID.
        """

        # Get parameter.
        url = 'https://aip.baidubce.com/rpc/2.0/tts/v1/create'
        params = {'access_token': self.token}
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        json = {
            'text': text,
            'format': 'mp3-16k',
            'voice': 4,
            'lang': 'zh',
            'speed': 5,
            'pitch': 5,
            'volume': 5,
            'enable_subtitle': 0
        }

        # Request.
        response = self.request(
            url,
            params=params,
            json=json,
            headers=headers
        )

        # Record.
        self.record_call(text=text)

        # Extract.
        response_json: dict = response.json()
        task_id: str = response_json['task_id']

        return task_id


    def _to_url_query_task(
        self,
        task_id: str
    ) -> dict:
        """
        Query task of generate voice URL from text.

        Parameters
        ----------
        task_id : Task ID.

        Returns
        -------
        Task information.
        """

        # Get parameter.
        url = 'https://aip.baidubce.com/rpc/2.0/tts/v1/query'
        params = {'access_token': self.token}
        headers = {
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        json = {'task_ids': [task_id]}

        # Request.
        response = self.request(
            url,
            params=params,
            json=json,
            headers=headers
        )

        # Extract.
        response_json: dict = response.json()
        task_info: dict = response_json['tasks_info'][0]

        return task_info


    def to_url(
        self,
        text: str,
        path: str | None = None
    ) -> str:
        """
        Generate voice URL from text.

        Parameters
        ----------
        text : Text, length cannot exceed 60.
        path : File save path.
            - `None`: Not save.

        Returns
        -------
        Voice URL.
        """

        # Create.
        task_id = self._to_url_create_task(text)

        # Wait.
        store = {}


        ## Define.
        def is_task_success() -> bool:
            """
            Whether if is task successed.

            Returns
            -------
            Judge result.
            """

            # Query.
            task_info = self._to_url_query_task(task_id)

            # Judge.
            match task_info['task_status']:
                case 'Running':
                    return False
                case 'Success':
                    store['url'] = task_info['task_result']['speech_url']
                    return True
                case _:
                    raise AssertionError('Baidu API text to voice task failed', task_info)


        ## Start.
        wait(
            is_task_success,
            _interval=0.5,
            _timeout=600
        )

        ## Extract.
        url = store['url']

        # Save.
        if path is not None:
            response = self.request(url)
            rfile = File(path)
            rfile.write(response.content)

        return url
