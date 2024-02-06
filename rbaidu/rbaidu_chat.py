# !/usr/bin/env python
# -*- coding: utf-8 -*-

"""
@Time    : 2024-01-11 22:00:14
@Author  : Rey
@Contact : reyxbo@163.com
@Explain : Baidu API chat methods.
"""


from typing import Any, List, Dict, Literal, Union, Optional
from datetime import datetime, timedelta
from reytool.rrandom import randi
from reytool.rregex import search, findall, sub
from reytool.rsystem import catch_exc
from reytool.rtime import now

from .rbaidu_base import RAPIBaidu


class RAPIBaiduChat(RAPIBaidu):
    """
    Rey's `Baidu API chat` type.
    """

    # Character.
    characters = (
        "善良", "淳厚", "淳朴", "豁达", "开朗", "体贴", "活跃", "慈祥", "仁慈", "温和",
        "温存", "和蔼", "和气", "直爽", "耿直", "憨直", "敦厚", "正直", "爽直", "率直",
        "刚直", "正派", "刚正", "纯正", "廉政", "清廉", "自信", "信心", "新年", "相信",
        "老实", "谦恭", "谦虚", "谦逊", "自谦", "谦和", "坚强", "顽强", "建议", "刚毅",
        "刚强", "倔强", "强悍", "刚毅", "减震", "坚定", "坚韧", "坚决", "坚忍", "勇敢",
        "勇猛", "勤劳", "勤恳", "勤奋", "勤勉", "勤快", "勤俭", "辛勤", "刻苦", "节约",
        "狂妄", "骄横", "骄纵", "窘态", "窘迫", "困窘", "难堪", "害羞", "羞涩", "赧然",
        "无语", "羞赧"
    )


    def __init__(
        self,
        key: str,
        secret: str,
        character: Optional[str] = None
    ) -> None:
        """
        Build `Baidu API chat` instance.

        Parameters
        ----------
        key : API key.
        secret : API secret.
        Character : Character of language model.
        """

        # Set attribute.
        super().__init__(key, secret)
        self.chat_records: Dict[str, List[Dict[Literal["time", "send", "receive"], Any]]] = {}
        self.character=character


    def chat(
        self,
        text: str,
        character: Optional[Union[str, Literal[False]]] = None,
        history_key: Optional[str] = None,
        history_recent_seconds: float = 1800,
        history_max_word: int = 400
    ) -> bytes:
        """
        Chat with language model.

        Parameters
        ----------
        text : Text.
        Character : Character of language model.
            - `None` : Use `self.character` attribute.
            - `str` : Use this value.
            - `Literal[False]` : Do not set.

        Character : Character of language model.
        history_key : Chat history records key.
        history_recent_seconds : Limit recent seconds of chat history.
        history_max_word : Limit maximum word of chat history.

        Returns
        -------
        Reply text.
        """

        # Get parameter.
        url = "https://aip.baidubce.com/rpc/2.0/ai_custom/v1/wenxinworkshop/chat/completions_pro"
        params = {"access_token": self.token}
        headers = {"Content-Type": "application/json"}
        if history_key is None:
            messages = []
        else:
            messages = self.history_messages(
                history_key,
                history_recent_seconds,
                history_max_word
            )
        message = {"role": "user", "content": text}
        messages.append(message)
        json = {"messages": messages}
        if character is None:
            character = self.character
        elif character is False:
            character = None
        if character is not None:
            json["system"] = character

        # Request.
        try:
            response = self.request(
                url,
                params=params,
                json=json,
                headers=headers
            )

        ## Parameter "system" error.
        except:
            _, _, exc, _ = catch_exc()
            error_code = exc.args[1]["error_code"]
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
                raise exc

        # Extract.
        response_json: Dict = response.json()
        result: str = response_json["result"]

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
            "time": now(),
            "send": send,
            "receive": receive
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
    ) -> List[Dict[Literal["role", "content"], str]]:
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
            interval_time: timedelta = now_time - record["time"]
            interval_seconds = interval_time.total_seconds()
            if interval_seconds > recent_seconds:
                break

            ## Limit word.
            word_len = len(record["send"]) + len(record["receive"])
            character_len = len(self.character)
            word_count += word_len
            if word_count + character_len > max_word:
                break

            ## Append.
            message = [
                {"role": "user", "content": record["send"]},
                {"role": "assistant", "content": record["receive"]}
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
            last_time: datetime = records[-1]["time"]
        if self.call_records == []:
            last_time = self.start_time
        else:
            last_time: datetime = self.call_records[-1]["time"]

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
        pattern = "[\'\"‘’“”]"
        text_modify = sub(pattern, text)
        text_modify_len = len(text_modify)

        # Modify.
        text_modify = "%s的润色这句话“%s”" % (character, text_modify)
        text_modify = self.chat(text_modify)

        # Extract.
        pattern = "\'[^\']+\'|\"[^\"]+\"|‘[^‘]+’|“[^“]+”"
        re_texts = findall(pattern, text_modify)
        result = None
        result_len = 0
        for re_text in re_texts:
            re_text = re_text[1:-1]
            re_text_len = len(re_text)
            if re_text_len < text_modify_len:
                break
            if re_text_len > result_len:
                result = re_text
                result_len = re_text_len
        if result is None:
            if "润色" not in text_modify:
                result = text_modify
            else:
                result = text

        return result