"""
.. automodule:: eumjeol_util

이 모듈은 Krcorpus에서 음절관련 기능을  담당하는 부분이다.
음절은 한국어에서 한글자를 의미하는 것으로 음절을 음소로 분해하거나
음소를 다시 음절을 합치는 등의 유틸리티 기능이 있다.

"""
import traceback

#: 종성없음
JONGSUNG_TYPE_NONE = 1
#: 종성이 유음(ㄹ)
JONGSUNG_TYPE_LIEUL = 2
#: 종성이 ㄹ을 제외한 받침
JONGSUNG_TYPE_COMMON = 3

_HANGUL_CODE_START = 44032
_HANGUL_CODE_END = 55199
_CHOSUNG = 19
_JUNGSUNG = 21
_JONGSUNG = 28

_CHOSUNG_LIST = [u'ㄱ', u'ㄲ', u'ㄴ', u'ㄷ', u'ㄸ', u'ㄹ', u'ㅁ', u'ㅂ', u'ㅃ', u'ㅅ',
                 u'ㅆ', u'ㅇ', u'ㅈ', u'ㅉ', u'ㅊ', u'ㅋ', u'ㅌ', u'ㅍ', u'ㅎ']
_JUNGSUNG_LIST = [u'ㅏ', u'ㅐ', u'ㅑ', u'ㅒ', u'ㅓ', u'ㅔ', u'ㅕ', u'ㅖ', u'ㅗ', u'ㅘ',
                  u'ㅙ', u'ㅚ', u'ㅛ', u'ㅜ', u'ㅝ', u'ㅞ', u'ㅟ', u'ㅠ', u'ㅡ', u'ㅢ',
                  u'ㅣ']
_JONGSUNG_LIST = [u'', u'ㄱ', u'ㄲ', u'ㄳ', u'ㄴ', u'ㄵ', u'ㄶ', u'ㄷ', u'ㄹ', u'ㄺ',
                  u'ㄻ', u'ㄼ', u'ㄽ', u'ㄾ', u'ㄿ', u'ㅀ', u'ㅁ', u'ㅂ', u'ㅄ', u'ㅅ',
                  u'ㅆ', u'ㅇ', u'ㅈ', u'ㅊ', u'ㅋ', u'ㅌ', u'ㅍ', u'ㅎ']

#: 양성모음
YANG_VOWEL = [u"ㅏ", u"ㅑ", u"ㅗ", u"ㅛ"]


def parse_eumjeol(eumjeol):
    """음절을 자소로 분리함

        Args :
            eumjeol (str) : 검사하려는 음절
        Returns:
            [ cho, jung, jong ]
            cho : 초성
            jung : 중성(모음)
            jong : 종성(받침, 없으면 "")
            ex) ["ㄱ", "ㅏ", "ㄴ"]
    """
    if eumjeol in ["", " "]:
        return [None, None, None]

    eumjeol_int = ord(eumjeol)
    if _HANGUL_CODE_START > eumjeol_int and _HANGUL_CODE_END < eumjeol_int:
        return None
    base = eumjeol_int - _HANGUL_CODE_START
    cho = int(base / (_JUNGSUNG * _JONGSUNG))
    temp = base % (_JUNGSUNG * _JONGSUNG)
    jung = int(temp / _JONGSUNG)
    jong = temp % _JONGSUNG
    return [_CHOSUNG_LIST[cho], _JUNGSUNG_LIST[jung], _JONGSUNG_LIST[jong]]


def change_jaso(eumjeol, cho, jung, jong):
    """음절의 초성, 중성, 종성을 변경함.

        Args :
            eumjeol (str) : 변경하려는 음절
            cho : 초성, 변경 필요 없으면 ""
            jung : 중성(모음), 변경 필요 없으면 ""
            jong : 종성(받침), 변경 필요 없으면 ""
        Returns:
            변경된 음절
        Ex):
            change_jaso("간", "ㅁ", None, None) => "만"
            change_jaso("간", None, None, "") => "가"
    """
    (org_cho, org_jung, org_jong) = parse_eumjeol(eumjeol)
    if cho is not None:
        org_cho = cho
    if jung is not None:
        org_jung = jung
    if jong is not None:
        org_jong = jong
    return build_eumjeol(org_cho, org_jung, org_jong)


def get_jongsung_type(eumjeol):
    """음절에서 종성(받침)의 종류를 리턴함

        Args :
            eumjeol (str) : 확인하려는 음절
        Returns:
            | 종성의 종류
            | JONGSUNG_TYPE_NONE : 종성이 없음
            | JONGSUNG_TYPE_LIEUL : ㄹ
            | JONGSUNG_TYPE_COMMON : ㄹ을 제외한 받침
        Ex):
            change_jaso("간", "ㅁ","","") => "만"
    """
    jong = (parse_eumjeol(eumjeol))[2]
    if jong == "":
        return JONGSUNG_TYPE_NONE
    elif jong == u"ㄹ":
        return JONGSUNG_TYPE_LIEUL
    return JONGSUNG_TYPE_COMMON


def has_jongsung(eumjeol):
    jong = (parse_eumjeol(eumjeol))[2]
    if jong == "":
        return False
    return JONGSUNG_TYPE_COMMON


def check_phoneme_restriction(eumjeol, phoneme):
    # # 예외사항으로 음절이 None일 경우 True이다.
    if eumjeol is None:
        return True
    [_, jung, jong] = parse_eumjeol(eumjeol)
    """
    L    ㄹ받침
    VO    받침없음
    FS    ㄹ제외한받침
    L|FS    ㄹ포함모든받침
    VO|L    받침없거나 ㄹ받침
    NUL    제한없음
    YANG1    모음이 ㅏ,ㅗ
    YANG2    모음이 ㅏ,ㅑ,ㅗ
    EUM1    모음이 ㅏ,ㅗ 제외
    """

    # yangsung = jung in [u"ㅏ", u"ㅑ", u"ㅗ", u"ㅛ"] # pt 기준에 대한 양성모음
    # 표준국어대사전 기준 양성모음 ㅏ,ㅗ,ㅑ,ㅛ,ㅘ,ㅚ,ㅐ 이나
    # ㅐ로 종결하는 용언  개어(개/VV+어/EC), 내어 처럼 음성모음과 어울리므로 뺀다.
    # 과(고/VV+아/EC), 봐(보/VV+아/EC)  같은 경우 활용된 형태는 과, 봐 이고 아/EC 와 어울리므로 추가하는게 맞다.
    # ㅚ 의 경우 아직 알 수 없음

    yang1 = jung in [u'ㅏ', u'ㅗ']
    yang2 = jung in [u'ㅏ', u'ㅑ', u'ㅗ']
    if phoneme == "NUL":
        return True
    elif jong == "" and "VO" in phoneme:  # 모음제약
        return True
    elif jong == u"ㄹ" and "LQ" in phoneme:  # 유음(ㄹ)제약
        return True
    elif jong not in ["", u"ㄹ"] and "FS" in phoneme:
        return True
    elif yang1 and "YANG1" in phoneme:  # 양성모음1체크
        return True
    elif yang2 and "YANG2" in phoneme:  # 양성모음2체크
        return True
    elif not yang1 and "EUM1" in phoneme:   # 음성모음체크
        return True
    return False


def build_eumjeol(cho, jung, jong):
    eumjeol = _HANGUL_CODE_START +\
        _CHOSUNG_LIST.index(cho) * _JUNGSUNG * _JONGSUNG
    eumjeol += _JUNGSUNG_LIST.index(jung) * _JONGSUNG
    eumjeol += _JONGSUNG_LIST.index(jong)
    return chr(eumjeol)


if __name__ == "__main__":
    try:
        jaso_list = parse_eumjeol(u"한")
        print(jaso_list)
    except Exception:
        tb = traceback.format_exc()
        print(tb)
