from __future__ import print_function
#-*- coding: utf-8 -*-
"""pos_util

pos_util



이 모듈은 Krcorpus에서 형태소 관련 도음 기능을 모아둔 부분이다.
"""

def postag_str(postag_tuple):
    """
    postag_tuple 형태의 postag 를 postag_str 형으로 변경한다.abs
    
    Args :
        postag_tuple :  [word_1, pos_1, word_2, pos_2, ...]
    Returns :
        | 형태소1/pos1+형태소2/pos2
        | ex) "가/VV+다/EF"
    """
    postag_pair_list = []
    for postag_pair in postag_tuple:
        word = postag_pair[0]
        pos = postag_pair[1]
        postag_pair_list.append(word + "/" + pos)
    return "+".join(postag_pair_list)

def union_meta(meta_left, meta_right):
    """
    두 meta 정보를 합친다. 

    Args :
        meta_left : meta 정보 dictionary
        meta_right : meta 정보 dictionary
    Returns:
        두 메타 정보의 결합, 통계 정보의 경우 두 독립 확률의 곱이다. 
    """
    new_meta = {}
    
    # 만분율이니까 두 값을 곱한 후 만으로 나눈다. 
    if "spoken" in meta_left and "spoken" in meta_right:
        new_meta["spoken"] = float(meta_left["spoken"]) * float(meta_right["spoken"]) / 10000

    if "writing" in meta_left and "writing" in meta_right:
        new_meta["writing"] = float(meta_left["writing"]) * float(meta_right["writing"]) / 10000
    return new_meta

def postag_left_check(pos_list, left_str):
    """ 
    Testcase 에서 형태소와 품사를 확인할 때 여러 후보군 때문에 재대로된 테스트를 못하는 문제를
    해결하기 위해 만들어진 함수

    Args : 
        | pos_list : pos_e.endswithE, pos_j.endswithE 의 결과물
        | left_str : 미분석된 형태소 단어
    Returns :
        left_str 이 여러 pos_list 내에 존재하면 True 리턴
    """
    for postag_info in pos_list:
        if postag_info[0] == left_str:
            return True
    return False

def postag_end_check(pos_list, postagstr):
    """Testcase 에서 형태소와 품사를 확인할 때 여러 후보군 때문에 재대로된 테스트를 못하는 문제를
    해결하기 위해 만들어진 함수

    Args : 
        | pos_list : pos_e.endswithE, pos_j.endswithE 의 결과물
        | postagstr : 형태소1/pos1+형태소2/pos 형태
    Returns :
        postagstr 이 여러 pos_list 내에 존재하면 True 리턴
    """
    for postag_info in pos_list:
        if postag_str(postag_info[1]) == postagstr:
            return True
    return False
