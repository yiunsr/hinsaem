from __future__ import print_function
#-*- coding: utf-8 -*-
"""PosN0(체언형 관련모듈) Module

이 모듈은 Krcorpus에서 체언형태분석을 담당하는 부분이다.
이 모듈의 가장 큰 역할은 어절이 체언형인지 검사하는 부분이다. 

체언형의 종류는 
1. 체언 단일어 : NNG(일반명사), NNP(고유명사), NNB(의존명사), NR(수사), NP(대명사)
2. 관형형 결합형 : MM + 체언,  체언 + [XSV|XSA] + ETM + 체언
3. 명사형 전성어미 :  VV+ETN, VA+ETM
4. 복합명사 : XPN + [체언 + XSN] + XSN

"""
import csv
import copy
import traceback
import enum
import logging
import multiprocessing as mp
from multiprocessing import current_process


from .config import CONFIG
from .pos_util import union_meta
from .pos_base import PosBase
from .eumjeol_util import check_phoneme_restriction, JONGSUNG_TYPE_NONE, JONGSUNG_TYPE_LIEUL, JONGSUNG_TYPE_COMMON, YANG_VOWEL
from .eumjeol_util import get_jongsung_type, has_jongsung, parse_eumjeol, build_eumjeol, change_jaso

mp.log_to_stderr()
logger_mp = mp.get_logger()
logger_mp.setLevel(logging.INFO)
logger = logging.getLogger(__name__)



#def _read_pos_dict2(file_path, sel_filter_list):
def _read_pos_dict2(file_path):
    logger_mp.info("_read_pos_dict2")
    
    with open(file_path, "r", encoding="UTF-8", newline="") as csvfile:
        for item in csv.DictReader(csvfile, delimiter="\t", dialect="excel-tab"):
            try:
                word = item["word"]
                item_dict = {}
                for sel_filter in sel_filter_list:
                    item_dict[sel_filter] = item[sel_filter]
                word_dict[word] = item_dict
            except Exception:
                tb = traceback.format_exc()
                print(tb)
    return word_dict

def test22():
    logger_mp.info("_read_dict start")
    if mp.current_process().name == 'MainProcess':
        pool = mp.Pool(2)
        params_list = [1]
        result_dict= {}
        for result in pool.map(_read_pos_dict2, params_list):
            logger_mp.info("_read_dict result for")
            result_dict.update(result)
        print(result_dict)


class PosN0(PosBase):
    """
    명사 분석 Class
    """
    GROUP_NOUN = ["NNP", "NNG", "NNB", "NP", "NR"]

    # 
    def __init__(self):
        config_dict = self._read_dict()
        self._noun_ser = config_dict["NOUN_SER"]
        self._nng = config_dict["NNG"]
        self._nnp = config_dict["NNP"]
        self._n_else = config_dict["N_"]
    
    def _read_dict(self):
        logger_mp.info("_read_dict start")
        processCount = CONFIG["multiprocess_count"]
        if processCount == "auto":
            processCount = mp.cpu_count()
        pool = mp.Pool(processCount)
        params_list = []
        params_list.append(["NNG", CONFIG["res_dict_nng"], ["word", "pos", "ratio"]])
        params_list.append(["NNP", CONFIG["res_dict_nnp"], ["word", "pos", "ratio"]])
        params_list.append(["N_", CONFIG["res_dict_n_"], ["word", "pos", "ratio"]])

        result_dict = {}
        for result in pool.map(PosN0._read_pos_dict, params_list):
            logger_mp.info("_read_dict result for")
            result_dict.update(result)
        
        return result_dict

    @staticmethod
    def _read_pos_dict(params):
        ret_key = params[0]
        file_path = params[1]
        sel_filter_list = params[2]
        logger_mp.info("_read_pos_dict start")
        word_dict = {}
        with open(file_path, "r", encoding="UTF-8", newline="") as csvfile:
            for item in csv.DictReader(csvfile, delimiter="\t", dialect="excel-tab"):
                try:
                    word = item["word"]
                    item_dict = {}
                    for sel_filter in sel_filter_list:
                        item_dict[sel_filter] = item[sel_filter]
                    word_dict[word] = item_dict
                except Exception:
                    tb = traceback.format_exc()
                    print(tb)
        return {ret_key : word_dict}

    def isCompNoun(self, eojeol):
        """
        복합명사 검사하고 가장 높은 후보군을 추출해 복합명사 또는 단일 명사 제공

        Args :
            eojeol (str) : 검사하려는 어절
        Returns:
            [postag1, postag2, ...] or None
            
            ex) ["사람/NNG","들/XSN"]
        """
        ## 한 문자이면 복합명사가 아니다. 
        if len(eojeol) == 1:
            pass

        
        return False
