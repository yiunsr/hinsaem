"""eomi(어미 검사모듈) Module

이 모듈은 Krcorpus에서 핵심을 담당하는 부분이다. 문장을 어절단위로 나누고,
어절의 조합방법에 따라서 형태소를 분석한다.

어절의 형태는
1. 단일어(체언,부사,관형사,감탄사)

2. 조사로 끝나는 경우
체언+조사
체언+용언화 접미사 + "ㅁ/기"+조사
용언+"ㅁ/기"+조사
용언+"아/어"+보조용언+"ㅁ/기"+조사
부사+조사

3. 어미로 끝나는 경우
체언+용언화 접미사+어미
체언+용언화 접미사+"아/어"+보조용언+어미
체언+"에서/부터/에서부터"+"이"+어미
용언+어미
용언+"ㅁ/기"+이+어미
용언+"아/어"+보조용언+어미
체언+동사+어미

중 하나이다.


Todo:
    * 어절내 불규칙활용 처리 필요
    * "나는요 오빠가 좋은걸 어떡해" 이라는 첫 어절 "나는요"는 해석하지 못하고 있어 처리가 필요하다.

.. 관련정보
    http://yiunsr.tistory.com/tag/%ED%98%95%ED%83%9C%EC%86%8C%EB%B6%84%EC%84%9D

"""
import csv
import traceback
import logging
from .config import CONFIG
from .eumjeol_util import get_jongsung_type, JONGSUNG_TYPE_NONE,\
    JONGSUNG_TYPE_LIEUL, JONGSUNG_TYPE_COMMON
from .eumjeol_util import has_jongsung, parse_eumjeol, build_eumjeol

logger = logging.getLogger(__name__)
