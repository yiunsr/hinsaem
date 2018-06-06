from __future__ import print_function
#-*- coding: utf-8 -*-
import os
import sys
if __name__ == "__main__":
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from hinsaem.pos_n0 import PosN0
import pytest
import logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('test')

#pos_n0 = PosN0()


def setup_function():
    log.debug("==== START " + __package__ + "::" + __name__ + " ====")

def teardown_function():
    log.debug("==== END ====")

def test_0000_01():
    pos_n0 = PosN0()
    log.debug("==== test_0000_01 ====")
    assert False

# def test_0001_n():
#     """ 복합명사 사전 로딩 검사 """    
#     assert u"Sn년" in pos_n0._noun_ser, u"Loading Check 1"
#     assert u"Sn년대" in pos_n0._noun_ser, u"Loading Check 2"
#     assert u"자가요법" in pos_n0._noun_ser, u"Loading Check 3"
# 
# 
# def test_0002_n():
#     """ 리스트에 존재하는 복합명사 """
#     isCompNoun = pos_n0.isCompNoun(u"사람들")
#     assert isCompNoun is True, u"'사람들' 복합명사"
    
if __name__ == "__main__":
    pytest.main([__file__])
    
    ## test single method
    #pytest.main(["-k test_0005_j"])
