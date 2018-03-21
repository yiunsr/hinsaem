from __future__ import print_function
#-*- coding: utf-8 -*-
import os
import sys
if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from hinsaem import Hinsaem
from hinsaem.pos_nr import PosNR
import pytest
import logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('test')

#hinsaem = Hinsaem()

def setup_function():
    log.debug("==== START " + __package__ + "::" + __name__ + " ====")

def teardown_function():
    log.debug("==== END ====")

posNR = PosNR()

def test_0001_nr():
    """ 수사 사전 로딩 검사 """    
    assert u"칠순" in posNR._nr_multi_dict, u"Loading Check"
    assert u"영" in posNR._nr_multi_dict, u"Loading Check"
    
def test_0002_nr():
    """ 고유어 수사 검사 """
    assert posNR.check(u"하나"), u"하나 is nr"
    assert posNR.check(u"둘"), u"둘 is nr"
    assert posNR.check(u"스물하나"), u"스물하나 is nr"
    assert posNR.check(u"마흔둘"), u"마흔둘 is nr"
    assert posNR.check(u"백만스물하나"), u"백만스물하나 is nr"
    
    """ 고유어 수사 검사 2"""
    assert posNR.check(u"한두"), u"한두 is nr"
    assert posNR.check(u"예닐곱"), u"예닐곱 is nr"
    

def test_0003_nr():
    """ 한자어 수사 검사 """
    assert posNR.check(u"일"), u"일 is nr"
    assert posNR.check(u"십"), u"십 is nr"
    assert posNR.check(u"일백만"), u"일백만 is nr"
    assert posNR.check(u"이천구백삼십일"), u"이천구백삼십일 is nr"
    assert posNR.check(u"이십만이천"), u"이십만이천 is nr"
    
    """ 접두어가 붙은 수사 """
    assert posNR.check(u"몇십"), u"몇십 is nr"
    assert posNR.check(u"기백"), u"기백 is nr"
    assert posNR.check(u"수천만"), u"수천만 is nr"

if __name__ == "__main__":
    pytest.main([__file__])
    
    # test single method
    #pytest.main(["-k test_0001_nr"])
