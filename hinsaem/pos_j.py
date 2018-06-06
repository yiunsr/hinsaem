"""PosJ(조사 관련모듈) Module

이 모듈은 Krcorpus에서 조사분석을 담당하는 부분이다.
이 모듈의 가장 큰 역할은 어절내에 조사로 끝나는지 검사하는 부분이다.

조사의 종류는
1. JK* 격조사
  1) JKS 주격조사
  2) JKC 보격조사
  3) JKG 관형격조사
  4) JKO 목적격조사
  5) JKB 부사격조사
  6) JKV 호격조사
  7) JKQ 인용격조사
2. JC 접속조사
3. JX 보조사
* 서술격 조사의 경우 긍정지정사와 부정지정사로 분류한다.

"""
import csv
import copy
import traceback
import logging
from .config import CONFIG
from .pos_base import PosBase
from .eumjeol_util import check_phoneme_restriction, JONGSUNG_TYPE_NONE,\
    JONGSUNG_TYPE_LIEUL, JONGSUNG_TYPE_COMMON
from .eumjeol_util import get_jongsung_type, has_jongsung, parse_eumjeol,\
    build_eumjeol

logger = logging.getLogger(__name__)


class PosJ(PosBase):
    """
    조사 분석 Class
    """
    _GROUP_JOSA = ["JKS", "JKC", "JKG", "JKO", "JKB", "JKV", "JKQ", "JC", "JX"]

    # 받침이 있는 체언에 결합하는 조사
    _JOSA_PRE_BADCHIM_LIST = [u"이", u"은", u"을", u"과", u"아",
                              u"이여", u"이랑"]

    # 받침이 없는 체언에 결합하는 조사
    _JOSA_PRE_NONBADCHIM_LIST = [u"가", u"는", u"를", u"와", u"고",
                                 u"다", u"든", u"라", u"랑", u"며",
                                 u"야", u"여"]
    # ㄹ받침이 있거나 받침이 없는 체언에 결합하는 조사
    _JOSA_PRE_RIEUL_LIST = [u"로"]

    # ㄹ받침 외의 받침이 있는 체언에 결합하는 조사
    _JOSA_PRE_NONRIEUL_LIST = [u"으로"]

    # 고유명사와 결합할 때 '이'가 삽입되는 조사
    _JOSA_INSERT_YI_LIST = [u"이가"]

    # 복합조사 series
    _SERIES_POS = ["JSE"]

    #
    def __init__(self):
        config_dict = self._readDict()
        self._josa_list = config_dict["JOSA"]
        self._josa_last = config_dict["JOSA_LAST"]
        self._josa_jungjong = config_dict["JOSA_JUNGJONG"]
        self._josa_jungjong_start = config_dict["JOSA_JUNGJONG_START"]
        self._josa_jungjong_only = config_dict["JOSA_JUNGJONG_ONLY"]

    def _readDict(self):
        multi_dict = {}
        josa_jungjong = {}
        josa_jungjong_only = {}
        josa_jungjong_start = set({})
        josa_last = set({})

        file_path0 = CONFIG["res_dict_j"]
        with open(file_path0, 'r', encoding='UTF-8', newline='') as csvfile:
            # next(csvfile, None)
            for item in csv.DictReader(
                    csvfile, delimiter="\t", dialect="excel-tab"):
                try:
                    word = item["word"]
                    posinfo = {"pos": item["pos"], "pos2": item["pos2"],
                               "phoneme": item["phoneme"]}
                    if word[0] < u"가" and len(word) == 1:
                        # 중성,종성만으로 이루어진 조사(ex : ㄴ)
                        if word not in josa_jungjong_only:
                            josa_jungjong_only[word] = []
                        josa_jungjong_only[word].append(posinfo)
                        # 중성, 종성으로 시작하는 조사의 시작 중종성 저정
                        josa_jungjong_start.add(word[0])

                    elif word[0] < u"가":
                        # 이 경우 정상문자가 아니라 부분 문자이다. (ex : ㅁ)
                        if word not in josa_jungjong:
                            josa_jungjong[word] = []
                        josa_jungjong[word].append(posinfo)
                        # 중성, 종성으로 시작하는 조사의 시작 중종성 저정
                        josa_jungjong_start.add(word[0])

                    # # 조사음절 마지막 음절 Set을 따로 만든다.
                    josa_last.add(word[-1])
                    if word not in multi_dict:
                        multi_dict[word] = []
                    multi_dict[word].append(posinfo)

                except Exception:
                    tb = traceback.format_exc()
                    print(tb)

        config_dict = {"JOSA": multi_dict, "JOSA_LAST": josa_last,
                       "JOSA_JUNGJONG": josa_jungjong,
                       "JOSA_JUNGJONG_START": josa_jungjong_start,
                       "JOSA_JUNGJONG_ONLY": josa_jungjong_only}
        return config_dict

    def endswithj(self, eojeol):
        """
        조사로 종결하는지 검사하고, 조사와 그 외로 구별함

        Args :
            eojeol
        Returns:
            [ leftword, word, mark, meta ] or None
            leftword : 뒷 조사를 제외한 부분
            word : 조사로 추정되는 단어+형태소
            mark : 문장기호, 없으면 None
            meta : postag(word/pos)에 따른 기타정보
            ex) ["집", "으로/JKB, None, {"으로/JKB" :
                { "spoken" : 222.5219782, "writing" : 316.9873731 }}]
        """

        last_char = eojeol[-1]

        # 문장 종결 기호가 있는지 확인한다.
        if last_char in CONFIG["sentence_mark"]:
            mark = last_char
            last_char = eojeol[-2]
            new_eojeol = eojeol[:-1]
            pos_filter = ["JX"]
        else:
            mark = None
            new_eojeol = eojeol
            pos_filter = self._GROUP_JOSA

        # #### 마지막 어절의 음절이 조사마지막 음절리스트에 있는지 확인한다.
        if last_char not in self._josa_last:
            # 받침으로 결합하는 조사에 대한 예외처리한다.
            (_, _, jong) = parse_eumjeol(last_char)
            if jong not in self._josa_jungjong_only:
                return None

        # 여러 가능성을 고려한 체언후보, 조사 조합 분리
        # [ [분리index, 전체어절, 체언후보, 조사후보], [분리index, 전체어절, 체언후보, 조사후보], ... ]
        leftword_josa_list = []

        for index in range(1, len(new_eojeol)+1):
            leftword = new_eojeol[:index]
            josa = new_eojeol[index:]
            if leftword != "" and josa != "":
                leftword_josa_list.append(
                    [index, leftword, josa, leftword[-1]])

            # #  받침으로 시작하는 어미처리
            # # 체언후보 + 조사가 한 음절에서 합쳐지는 경우, leftword를 검사할 때 분리한다.
            (cho, jung, jong) = parse_eumjeol(leftword[-1])
            if jong in self._josa_jungjong_start:
                last_eumjeol_left = build_eumjeol(cho, jung, "")
                leftword = leftword[:-1] + last_eumjeol_left
                josa = jong + josa
                leftword_josa_list.append(
                    [index, leftword, josa, last_eumjeol_left])

        candiate_list = []
        # 최장 음절을 가정하고 최장음절부터 겹치는 조사가 있는지 검사한다.
        for item in leftword_josa_list:
            index = item[0]
            leftword = item[1]
            josa = item[2]
            last_eumjeol_left = item[3]

            new_candiate_list = self._get_candiate_info_list(
                index, eojeol, leftword, josa, last_eumjeol_left, mark,
                pos_filter)
            if len(new_candiate_list) > 0:
                candiate_list.extend(new_candiate_list)

        return candiate_list

    def _jungjong_only_josa(self, eojeol, mark):
        last_eumjeol = eojeol[-1]
        (cho, jung, jong) = parse_eumjeol(last_eumjeol)
        if jong not in self._josa_jungjong_only:
            return []
        leftword = eojeol[:-1] + build_eumjeol(cho, jung, "")
        candiate_list = []
        for posinfo in self._josa_jungjong_only[jong]:
            pos = posinfo["pos"]
            postag_tuple = [(jong, pos)]
            candiate_info = [leftword, postag_tuple,
                             mark, {tuple(postag_tuple): posinfo}]
            candiate_list.append(candiate_info)
        return candiate_list

    def _get_candiate_info_list(
            self, index, eojeol, candidate_leftword, candidate_josa,
            last_eumjeol_left, mark, pos_filter,):
        """
        전달된 어간후보, 어미후가가 적당한 후보가 맞는지 확인 하고 맞으면
        candiate_info_list 를 리턴한다.

        Args :
            index(int) : 어절의 어간과 어미를 분리하는 index
            eojeol (str) : 어절, 현재는 사용되지 않는다.
            candidate_leftword (str) : 검사하려는 어간후보
            candidate_josa (str) : 검사하려는 어미 후보
            last_eumjeol_left : 음운 조건을 확인해야 하는 나머지단어
            pos_filter : 어미후보의 가능한 pos 리스트
            mark : 문장기호(없는 경우 None)
        Returns:
            [ leftword, postag_tuple, mark, posinfo] or None
            leftword : 뒷 조사를 제외한 부분
            postag_tuple : postag tuple
            mark : 문장기호(없는 경우 None)
            posinfo : 해당 형태소의 meta 정보
        """
        candiate_list = []

        if candidate_josa in self._josa_list:
            for posinfo in self._josa_list[candidate_josa]:
                if check_phoneme_restriction(
                        last_eumjeol_left, posinfo["phoneme"]):
                    postag_tuple = self._pos_select(
                        candidate_josa, posinfo["pos"], posinfo["pos2"])
                    # 추출하려는 형태소가 아니면 패스
                    if postag_tuple[-1][1] not in pos_filter:
                        continue

                    candiate_info = [candidate_leftword,
                                     postag_tuple, mark, posinfo]
                    candiate_list.append(candiate_info)

        return candiate_list
