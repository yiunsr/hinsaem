from __future__ import print_function
#-*- coding: utf-8 -*-
"""
    PosBase(형태소 관련 기본 기능) Module
    ~~~~~~~~


"""

class PosBase(object):
    """ 형태소 관련 기본기능 모듈
    
    """
    def _pos_select(self, word, pos, comppostag):
        """
        복합형태소가 있는 경우 복합형태소가 선택되고 

        Arg : 
            word : 형태소를 분석한 원 단어
            pos : 단일형태소
            comppostag : 복합태킹 형태소(복합조사, 복합어미 같은 것)
                ex) 으랬/EP+니/EC   

        Returns:
            [(word_1, pos_1), (word_2, pos_2), ...]
            word_1, word_2, ... : 단어
            pos_1, pos_2, ... : 조사로 추정되는 단어+형태소
        """

        postag_list = []
        if comppostag != "":
            for postagitem in comppostag.split("+"):
                [singleword, pos] = postagitem.split("/")
                postag_list.append((singleword, pos))
        else:
            postag_list.append((word, pos))
        return tuple(postag_list)

    @staticmethod
    def pool_func_wrap(class_name, func_name, param_dict):
        return locals()[func_name](**param_dict)
        
