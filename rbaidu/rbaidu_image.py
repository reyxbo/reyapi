# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2024-01-11 22:00:14
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Baidu API image methods.
"""


from reykit.ros import RFile
from reykit.rtime import wait

from .rbaidu_base import RAPIBaidu


__all__ = (
    'RAPIBaiduImage',
)


class RAPIBaiduImage(RAPIBaidu):
    """
    Rey's `Baidu API image` type.
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
            rfile = RFile(path)
            rfile.write(response.content)

        return url
