"""PosNR(수사 관련모듈) Module

이 모듈은 Krcorpus에서 수사분석을 담당하는 부분이다. 수사의 경우 단어사전으로
만들기에는 그 수가 끝이 없기 때문에 자주사용하거나 특별한 단어 이외에는
수사가 맞는지 체크해야 한다.

수사의 형태는
1. 고유어 양수사
  하나, 둘, 셋, 넷, 다섯, 여섯, 일곱, 여덟, 아홉,
  열, 스물, 서른, 마흔, 쉰, 예순, 일흔, 여든, 아흔
  온, 즈믄
  한두, 두셋, 너더댓, 너덧, 네댓, 대여섯, 예닐곱, 엳아홉,

2. 한자어 양수사
 영, 공, 일, 이, 삼, 사, 오, 육, 칠, 팔, 구,
 십, 백, 천, 만, 억, 조, 경, 해

3. 고유어 서수사
    첫째, 둘째, 셋째, 넷째...

4. 한자어 서수사
    제일, 제이, 제삼, ...



Todo:
    *


"""
import csv
import copy
import traceback
import logging
from .config import CONFIG
from .eumjeol_util import get_jongsung_type, JONGSUNG_TYPE_NONE,\
    JONGSUNG_TYPE_LIEUL, JONGSUNG_TYPE_COMMON
from .eumjeol_util import has_jongsung, parse_eumjeol, build_eumjeol

logger = logging.getLogger(__name__)


class PosNR(object):
    """
    수사 분석 Class
    """

    # 고유어 양수사
    _PURE_KOR_NUMBER = {
        "하나": 1, "한": 1, "둘": 2, "두": 2, "셋": 3, "세": 3, "넷": 4, "네": 5,
        "다섯": 5, "여섯": 6, "일곱": 7, "여덟": 8, "여덜": 8, "여덞": 8,
        "아홉": 9}

    _PURE_KOR_NUMBER_TEN = {
        "열": 10, "스물": 20, "서른": 30, "설흔": 30, "마흔": 40, "쉰": 50,
        "쉬흔": 50, "예순": 60, "일흔": 70, "여든": 80, u"아흔": 90}

    _PURE_KOR_NUMBERS = {
        "한두": [1, 2], "하나둘": [1, 2], "두세": [2, 3], "두셋": [2, 3],
        "서너": [3, 4], "네다섯째": [4, 5], "두세너": [2, 4], "너더댓": [4, 5],
        "너덧": [4, 5], u"네댓": [4, 5], u"대여섯": [5, 6], "예닐곱": [6, 7],
        "엳아홉": [8, 9]}

    # 한자어 양수사
    _HANJA_NUMBER = {
        "일": 1, "이": 2, "삼": 3, "사": 4, "오": 5,
        "육": 6, "칠": 7, "팔": 8, "구": 9}
    _HANJA_NUMBER_DEC = {
        "십": 10, "시": 10, "백": 100, "천": 100, "만": 10000, "십만": 100000,
        "백만": 1000000, "천만": 10000000, "억": 100000000,
        "십억": 1000000000, "백억": 10000000000, "천억": 100000000000,
        "조": 1000000000000, "십조": 10000000000000, "백조": 100000000000000,
        "천조": 1000000000000000, "경": 10000000000000000,
        "십경": 100000000000000000, "백경": 1000000000000000000,
        "천경": 10000000000000000000, "해": 100000000000000000000
        }

    _ALL_NUMBER = copy.deepcopy(_PURE_KOR_NUMBER)
    _ALL_NUMBER.update(_PURE_KOR_NUMBER_TEN)
    _ALL_NUMBER.update(_PURE_KOR_NUMBERS)
    _ALL_NUMBER.update(_HANJA_NUMBER)

    # 고유어 접미사
    _PURE_KOR_POSTFIX = [u"째"]

    # 한자어 접두사
    # 제일,  기천만, 수천
    _HANJA_ORDINAL_PRE = [u"제", u"기", u"수", u"몇"]

    def __init__(self):
        self._nr_multi_dict = self._readDict()

    def _readDict(self):
        multi_dict = {}
        file_path0 = CONFIG["res_dict_nr"]
        with open(file_path0, 'r', encoding='UTF-8', newline='') as csvfile:
            # next(csvfile, None)
            for item in csv.DictReader(
                    csvfile, delimiter="\t", dialect="excel-tab"):
                try:
                    word = item["word"]
                    morpheme = item["pos"]
                    if word not in multi_dict:
                        multi_dict[word] = []
                    multi_dict[word].append(morpheme)

                except Exception:
                    tb = traceback.format_exc()
                    print(tb)

        return multi_dict

    def check(self, word):
        """
        Args :
            word (str) : 검사하려는 단어(형태소)
        Returns:
            [ left_word, word, mark ] or None

            left_word : 뒷 조사를 제외한 부분
            word : 어미로 추정되는 단어+형태소
            mark : 문장기호, 없으면 None

            ex) ["달리", "다/EF, "."]
        """
        if word in self._ALL_NUMBER:
            return True

        subword = ""
        for index, ch in enumerate(word):
            if index == len(word) - 1:
                lastch = True
            else:
                lastch = False
            subword = subword + ch
            if subword in self._HANJA_ORDINAL_PRE:
                subword = ""
                continue
            elif subword in self._HANJA_NUMBER_DEC:
                subword = ""
                continue
            elif subword in self._HANJA_NUMBER:
                subword = ""
                continue
            elif subword in self._PURE_KOR_NUMBER:
                subword = ""
                continue
            elif subword in self._PURE_KOR_NUMBER_TEN:
                subword = ""
                continue
            elif subword in self._PURE_KOR_NUMBERS:
                subword = ""
                continue

            # # 마지막 문자인데 매치되지 않는 남는 문자가 남으면 오류다.
            elif lastch:
                return False
        return True
