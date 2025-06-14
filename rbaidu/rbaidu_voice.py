# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2024-01-11 22:00:14
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Baidu API voice methods.
"""


from reykit.rexception import warn
from reykit.ros import RFile
from reykit.rtime import wait

from .rbaidu_base import RAPIBaidu


__all__ = (
    'RAPIBaiduVoice',
)


class RAPIBaiduVoice(RAPIBaidu):
    """
    Rey's `Baidu API voice` type.
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
            rfile = RFile(path)
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
            rfile = RFile(path)
            rfile.write(response.content)

        return url
