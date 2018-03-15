from __future__ import print_function
#-*- coding: utf-8 -*-
import os
import sys
if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from hinsaem import Hinsaem
from hinsaem.pos_util import postag_str, postag_left_check, postag_end_check
from hinsaem.pos_j import PosJ
from hinsaem.pos_util import postag_str
import pytest
import logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('test')

hinsaem = Hinsaem()

def setup_function():
    log.debug("==== START " + __package__ + "::" + __name__ + " ====")

def teardown_function():
    log.debug("==== END ====")

## pytest가 2번 호출되는 버그가 발견되어 그 것을 회피하기 위해
if __name__ != "__main__":
    pos_J = PosJ()

def test_0001_j():
    """ 조사 사전 로딩 검사 """    
    assert u"께서" in pos_J._josa_list, u"Loading Check 1"
    assert u"같이" in pos_J._josa_list, u"Loading Check 2"
    assert u"는" in pos_J._josa_list, u"Loading Check 3"
    assert u"은" in pos_J._josa_list, u"Loading Check 4"
    
def test_0002_j():
    """ 조사로 끝나는 어절의 조사 검사 """
    # 명사로 끝나는 경우에는 None
    pos_list = pos_J.endswithj(u"사람")
    assert pos_list is None, u"명사의 경우 None"

    pos_list = pos_J.endswithj(u"사람은")
    assert postag_left_check(pos_list, u"사람"), u"사람 in eojeol"
    assert postag_end_check(pos_list, u"은/JX"), u"은/JX in eojeol"
    
    pos_list = pos_J.endswithj(u"사람에게")
    assert postag_left_check(pos_list, u"사람"), u"사람 in eojeol"
    assert postag_end_check(pos_list, u"에게/JKB"), u"에게/JKB in eojeol"
    assert postag_left_check(pos_list, u"사람에"), u"사람에 in eojeol"
    assert postag_end_check(pos_list, u"게/JKB"), u"게/JKB in eojeol"
     
    
def test_0003_j():
    """ 복합조사 검사 """
    pos_list = pos_J.endswithj(u"사람같이는")
    assert postag_left_check(pos_list, u"사람"), u"사람 in eojeol"
    assert postag_end_check(pos_list, u"같이/JKB+는/JX"), u"같이/JKB+는/JX in eojeol"

    pos_list = pos_J.endswithj(u"회사같이도")
    assert postag_left_check(pos_list, u"회사"), u"회사 in eojeol"
    assert postag_end_check(pos_list, u"같이/JKB+도/JX"), u"같이/JKB+도/JX in eojeol"

def test_0004_j():
    """ 문장기호가 있는경우 """
    pos_list = pos_J.endswithj(u"나요.")
    assert postag_left_check(pos_list, u"나"), u"나 in eojeol"
    assert postag_end_check(pos_list, u"요/JX"), u"요/JX in eojeol"
    assert pos_list[0][2] == u".", u". in eojeol"

    pos_list = pos_J.endswithj(u"나는야!")
    assert postag_left_check(pos_list, u"나"), u"나 in eojeol"
    assert postag_end_check(pos_list, u"는/JX+야/JX"), u"는/JX+야/JX in eojeol"
    assert pos_list[0][2] == u"!", u". in eojeol"


def test_0005_j():
    """ 받침으로만 이루어진 조사 검사 """
    pos_list = pos_J.endswithj(u"우린")
    assert postag_left_check(pos_list, u"우리"), u"우리 in eojeol"
    assert postag_end_check(pos_list, u"ㄴ/JX"), u"ㄴ/JX in eojeol"

    pos_list = pos_J.endswithj(u"날")
    assert postag_left_check(pos_list, u"나"), u"나 in eojeol"
    assert postag_end_check(pos_list, u"ㄹ/JKO"), u"ㄹ/JKO in eojeol"

    

def test_0006_j():
    """ 받침으로만 시작하는 조사 검사 """
    pos_list = pos_J.endswithj(u"절더러")
    assert postag_left_check(pos_list, u"저"), u"저 in eojeol"
    assert postag_end_check(pos_list, u"ㄹ더러/JKB"), u"ㄹ더러/JKB in eojeol"

    pos_list = pos_J.endswithj(u"난들")
    assert postag_left_check(pos_list, u"나"), u"나 in eojeol"
    assert postag_end_check(pos_list, u"ㄴ들/JKB"), u"ㄴ들/JKB in eojeol"
    

if __name__ == "__main__":
    pytest.main([__file__])
    
    ## test single method
    #pytest.main(["-k test_0005_j"])
