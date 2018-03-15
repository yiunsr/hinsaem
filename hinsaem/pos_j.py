from __future__ import print_function
#-*- coding: utf-8 -*-
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
from .eumjeol_util import check_phoneme_restriction, JONGSUNG_TYPE_NONE, JONGSUNG_TYPE_LIEUL, JONGSUNG_TYPE_COMMON
from .eumjeol_util import get_jongsung_type, has_jongsung, parse_eumjeol, build_eumjeol

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
            #next(csvfile, None) 
            for item in csv.DictReader(csvfile, delimiter="\t", dialect="excel-tab"):
                try:
                    word = item["word"]
                    posinfo = {"pos" : item["pos"], "pos2" : item["pos2"],
                               "phoneme" : item["phoneme"]
                              }
                    
                    if word[0] < u"가" and len(word) == 1: # 중성,종성만으로 이루어진 조사(ex : ㄴ)
                        if word not in josa_jungjong_only:
                            josa_jungjong_only[word] = []
                        josa_jungjong_only[word].append(posinfo)
                        # 중성, 종성으로 시작하는 조사의 시작 중종성 저정
                        josa_jungjong_start.add(word[0])

                    elif word[0] < u"가": #이 경우 정상문자가 아니라 부분 문자이다. (ex : ㅁ)
                        if word not in josa_jungjong:
                            josa_jungjong[word] = []
                        josa_jungjong[word].append(posinfo)
                        # 중성, 종성으로 시작하는 조사의 시작 중종성 저정
                        josa_jungjong_start.add(word[0])
                    
                    ## 조사음절 마지막 음절 Set을 따로 만든다. 
                    josa_last.add(word[-1])
                    if word not in multi_dict:
                        multi_dict[word] = []
                    multi_dict[word].append(posinfo)

                except Exception:
                    tb = traceback.format_exc()
                    print(tb)

        config_dict = {"JOSA" : multi_dict, "JOSA_LAST" : josa_last, 
                       "JOSA_JUNGJONG" : josa_jungjong, "JOSA_JUNGJONG_START" : josa_jungjong_start,
                       "JOSA_JUNGJONG_ONLY" : josa_jungjong_only
                      }
        return config_dict

    def endswithj(self, eojeol):
        """
        조사로 종결하는지 검사하고, 조사와 그 외로 구별함

        Args : 
            eojeol
        Returns:
            [ left_word, word, mark, meta ] or None
            left_word : 뒷 조사를 제외한 부분
            word : 조사로 추정되는 단어+형태소
            mark : 문장기호, 없으면 None
            meta : postag(word/pos)에 따른 기타정보
            ex) ["집", "으로/JKB, None, {"으로/JKB" : { "spoken" : 222.5219782, "writing" : 316.9873731 }}]
        """
        last_char = eojeol[-1]

        # 문장 종결 기호가 있는지 확인한다. 
        mark = None
        if last_char in CONFIG["sentence_mark"]:
            mark = last_char
            last_char = eojeol[-2]
            new_eojeol = eojeol[:-1]
        else:
            new_eojeol = eojeol

        #### 마지막 어절의 음절이 조사마지막 음절리스트에 있는지 확인한다. 
        if last_char not in self._josa_last:
            # 받침으로 결합하는 조사에 대한 예외처리한다. 
            (_, _, jong) = parse_eumjeol(last_char)
            if jong not in self._josa_jungjong_only:
                return None
        
        candiate_list = []
        #최장 음절을 가정하고 최장음절부터 겹치는 조사가 있는지 검사한다.
        #조사만으로 이루어진 어절은 없기 때문에 어절수-1을 최대 조사로 생각한다.
        for index in range(1, len(new_eojeol)):
            candidate_word = new_eojeol[index:]
            char_before_josa = new_eojeol[index-1]
            left_word = new_eojeol[:index]

            candiate_info = None

            # 받침으로 시작하는 조사
            # 조사 추정 앞 음절이 받침이라고 생각한다. 
            (cho, jung, jong) = parse_eumjeol(char_before_josa)
            if jong in self._josa_jungjong_start:
                candidate_word = jong + candidate_word
                char_before_josa = build_eumjeol(cho, jung, "")
                left_word = left_word[:index-1] + char_before_josa
                if candidate_word in self._josa_list:
                    for posinfo in self._josa_list[candidate_word]:
                        if check_phoneme_restriction(char_before_josa, posinfo["phoneme"]):
                            postag_tuple = self._pos_select(candidate_word, posinfo["pos"], posinfo["pos2"])
                            candiate_info = [left_word, postag_tuple, mark, {tuple(postag_tuple) : posinfo}]
                            candiate_list.append(candiate_info)
            
            # 받침으로 시작하는 조사가 매칭되었을 때는
            # 음절로 시작하는 조사가 매칭될 수 있는 경우가 많기 때문에
            # 그냥 무시한다. 예외 Case 가 있는지 확인 필요
            if candiate_info:
                continue
            
            candidate_word = new_eojeol[index:]
            char_before_josa = new_eojeol[index-1]
            left_word = new_eojeol[:index]
            if candidate_word in self._josa_list:
                for posinfo in self._josa_list[candidate_word]:
                    if check_phoneme_restriction(char_before_josa, posinfo["phoneme"]):
                        postag_list = self._pos_select(candidate_word, posinfo["pos"], posinfo["pos2"])
                        candiate_info = [left_word, postag_list, mark, {tuple(postag_list) : posinfo}]
                        candiate_list.append(candiate_info)
            
            
        
        # 받침으로만 이루어진 조사 체크
        # 조사가 없는 경우에만 검사한다. 
        if len(candiate_list) == 0:
            jong_candiate_list = self._jungjong_only_josa(new_eojeol, mark)
            if jong_candiate_list != []:
                candiate_list.extend(jong_candiate_list)
        
        if len(candiate_list) == 0:
            return None

        return candiate_list
    
    def _jungjong_only_josa(self, eojeol, mark):
        last_eumjeol = eojeol[-1]
        (cho, jung, jong) = parse_eumjeol(last_eumjeol)
        if jong not in self._josa_jungjong_only:
            return []
        left_word = eojeol[:-1] + build_eumjeol(cho, jung, "")
        candiate_list = []
        for posinfo in self._josa_jungjong_only[jong]:
            pos = posinfo["pos"]
            postag_tuple = [(jong, pos)]
            candiate_info = [left_word, postag_tuple, mark, {tuple(postag_tuple) : posinfo}]
            candiate_list.append(candiate_info)
        return candiate_list
