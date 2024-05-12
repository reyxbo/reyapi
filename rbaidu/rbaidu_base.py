# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2024-01-11 21:56:56
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Baidu API base methods.
"""


from typing import Any, List, Dict, Literal, Optional
from datetime import datetime
from requests import Response
from uuid import uuid1
from reytool.rcomm import request as reytool_request
from reytool.rtime import now


__all__ = (
    "RAPIBaidu",
)


class RAPIBaidu(object):
    """
    Rey's `Baidu API` type.
    """


    def __init__(
        self,
        key: str,
        secret: str,
        token_valid_seconds: float = 43200
    ) -> None:
        """
        Build `Baidu API` instance.

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
        self.call_records: List[Dict[Literal["time", "data"], Any]] = []
        self.start_time = now()


    def get_token(self) -> str:
        """
        Get token.

        Returns
        -------
        Token.
        """

        # Get parameter.
        url = "https://aip.baidubce.com/oauth/2.0/token"
        params = {
            "grant_type": "client_credentials",
            "client_id": self.key,
            "client_secret": self.secret
        }

        # Request.
        response = self.request(
            url,
            params,
            method="post"
        )

        # Extract.
        response_json = response.json()
        token = response_json["access_token"]

        return token


    @property
    def token(self) -> str:
        """
        Get authorization token.
        """

        # Get parameter.
        if hasattr(self, "token_time"):
            token_time: datetime = getattr(self, "token_time")
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
        content_type = response.headers["Content-Type"]
        if content_type.startswith("application/json"):
            response_json: Dict = response.json()
            if "error_code" in response_json:
                raise AssertionError("Baidu API request failed", response_json)

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
            "time": now(),
            "data": data
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
            last_time: datetime = self.call_records[-1]["time"]

        # Count.
        now_time = now()
        interval_time = now_time - last_time
        interval_seconds = interval_time.total_seconds()

        return interval_seconds