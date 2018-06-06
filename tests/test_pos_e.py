import pathmagic  # noqa

from hinsaem import Hinsaem
from hinsaem.pos_e import PosE
from hinsaem.pos_util import postag_str, postag_left_check, postag_end_check
import pytest
import logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger("test")

# hinsaem = Hinsaem()


def setup_function():
    log.debug("==== START " + __package__ + "::" + __name__ + " ====")


def teardown_function():
    log.debug("==== END ====")


pos_E = PosE()


def test_0001_e():
    """ 어미 사전 로딩 검사 """
    assert u"라고" in pos_E._eomi_list, u"Loading Check 1"
    assert u"다" in pos_E._eomi_list, u"Loading Check 2"


def test_0002_e():
    """ 어미 검사 """
    pos_list = pos_E.endswithE(u"코")
    assert pos_list == [], u"명사의 경우 []"

    # 문장 종결부호가 없기 때문에 /EF는 문가능하다.
    pos_list = pos_E.endswithE(u"빠르고")
    assert postag_left_check(pos_list, u"빠르"), u"빠르 in eojeol"
    assert postag_end_check(pos_list, u"고/EC"), u"고 in eojeol"
    # assert pos_list[0][0] == u"빠르", u"빠르 in eojeol"
    # assert postag_str(pos_list[0][1]) == u"고/EC", u"고 in eojeol"


def test_0003_e():
    """ 종결어미 마침표가 있는 경우 """
    pos_list = pos_E.endswithE(u"빠르다.")
    assert postag_left_check(pos_list, u"빠르"), u"빠르 in eojeol"
    assert postag_end_check(pos_list, u"다/EF"), u"다/EF in eojeol"


def test_0004_e():
    """ 받침으로만 이루어진 어미 """
    pos_list = pos_E.endswithE(u"미끄러짐")
    assert postag_left_check(pos_list, u"미끄러지"), u"미끄러지 in eojeol"
    assert postag_end_check(pos_list, u"ㅁ/ETN"), u"ㅁ/ETN in eojeol"

    pos_list = pos_E.endswithE(u"감")
    assert postag_left_check(pos_list, u"가"), u"가 in eojeol"
    assert postag_end_check(pos_list, u"ㅁ/ETN"), u"ㅁ/ETN in eojeol"


def test_0005_e():
    """ 받침으로 시작하는 어미 """
    pos_list = pos_E.endswithE(u"간걸.")
    assert postag_left_check(pos_list, u"가"), u"가 in eojeol"
    assert postag_end_check(pos_list, u"ㄴ걸/EF"), u"ㄴ걸/EF in eojeol"


def test_0006_e():
    """ 선어말 어미 검사 """
    # pos_list = pos_E.endswithE(u"먹었다.")
    # assert pos_list[0][0] == u"먹", u"먹 in eojeol"
    # pass
    pos_list = pos_E.endswithE(u"먹었다.")
    assert postag_left_check(pos_list, u"먹"), u"먹 in eojeol"
    assert postag_end_check(pos_list, u"었/EP+다/EF"), u"었/EP+다/EF in eojeol"

    pos_list = pos_E.endswithE(u"먹었겠다.")
    assert postag_left_check(pos_list, u"먹"), u"먹 in eojeol"
    assert postag_end_check(
        pos_list, u"었/EP+겠/EP+다/EF"), u"었/EP+겠/EP+다/EF in eojeol"

    pos_list = pos_E.endswithE(u"달리시겠어요.")
    assert postag_left_check(pos_list, u"달리"), u"달리 in eojeol"
    assert postag_end_check(
        pos_list, u"시/EP+겠/EP+어요/EF"), u"시/EP+겠/EP+어요/EF in eojeol"

    pos_list = pos_E.endswithE(u"갔다.")
    assert postag_left_check(pos_list, u"가"), u"가 in eojeol"
    assert postag_end_check(pos_list, u"ㅆ/EP+다/EF"), u"ㅆ/EP+다/EF in eojeol"


def test_0007_e():
    """ 불규칙 활용기능 테스트 1"""

    # #### "러" 불규칙 활용
    pos_list = pos_E.endswithE(u"검푸르러")
    assert postag_left_check(pos_list, u"검푸르"), u"검푸르 in eojeol"
    assert postag_end_check(pos_list, u"러/EC"), u"러/EC in eojeol"

    pos_list = pos_E.endswithE(u"푸르러서")
    assert postag_left_check(pos_list, u"푸르"), u"푸르 in eojeol"
    assert postag_end_check(pos_list, u"어서/EC"), u"어서/EC in eojeol"

    # #### "ㄷ" 불규칙 활용
    pos_list = pos_E.endswithE(u"걸으니")
    # 규칙형 검사
    assert postag_left_check(pos_list, u"걸"), u"걸 in eojeol"
    assert postag_end_check(pos_list, u"으니/EC"), u"으니/EC in eojeol"
    # 불규칙형
    assert postag_left_check(pos_list, u"걷"), u"걷 in eojeol"
    assert postag_end_check(pos_list, u"으니/EC"), u"으니/EC in eojeol"

    pos_list = pos_E.endswithE(u"실어")
    # 규칙형 검사
    assert postag_left_check(pos_list, u"실"), u"실 in eojeol"
    assert postag_end_check(pos_list, u"어/EC"), u"어/EC in eojeol"
    # 불규칙형
    assert postag_left_check(pos_list, u"싣"), u"싣 in eojeol"
    assert postag_end_check(pos_list, u"어/EC"), u"어/EC in eojeol"

    # #### "ㄹ" 불규칙 활용
    pos_list = pos_E.endswithE(u"주니")  # 몸무게가 줄다. 몸무게가 주니
    # 규칙형 검사
    assert postag_left_check(pos_list, u"주"), u"주 in eojeol"
    assert postag_end_check(pos_list, u"니/EC"), u"니/EC in eojeol"
    # 불규칙형
    assert postag_left_check(pos_list, u"줄"), u"줄 in eojeol"
    assert postag_end_check(pos_list, u"니/EC"), u"니/EC in eojeol"

    # 아주 예외적으로 시가 붙는 경우 불규칙이 발생한다.
    pos_list = pos_E.endswithE(u"가셨다.")  # 아버지는 칼을 가셨다.
    # 규칙형 검사
    assert postag_left_check(pos_list, u"가"), u"가 in eojeol"
    assert postag_end_check(
        pos_list, u"시/EP+었/EP+다/EF"), u"시/EP+었/EP+다/EF in eojeol"
    # 불규칙형
    assert postag_left_check(pos_list, u"갈"), u"갈 in eojeol"
    assert postag_end_check(
        pos_list, u"시/EP+었/EP+다/EF"), u"시/EP+었/EP+다/EF in eojeol"

    # "우" 불규칙
    pos_list = pos_E.endswithE(u"퍼")
    assert postag_left_check(pos_list, u"푸"), u"푸 in eojeol"
    assert postag_end_check(pos_list, u"어/EC"), u"어/EC in eojeol"

    pos_list = pos_E.endswithE(u"퍼서")
    assert postag_left_check(pos_list, u"푸"), u"푸 in eojeol"
    assert postag_end_check(pos_list, u"어서/EC"), u"어서/EC in eojeol"

    pos_list = pos_E.endswithE(u"펐다.")
    assert postag_left_check(pos_list, u"푸"), u"푸 in eojeol"
    assert postag_end_check(pos_list, u"었/EP+다/EF"), u"었/EP+다/EF in eojeol"


def test_0008_e():
    """ 불규칙 활용기능 테스트 2"""

    # #### "ㅅ" 불규칙 활용
    pos_list = pos_E.endswithE(u"그어")
    # 규칙
    assert postag_left_check(pos_list, u"그"), u"그 in eojeol"
    assert postag_end_check(pos_list, u"어/EC"), u"어/EC in eojeol"
    # 불규칙
    assert postag_left_check(pos_list, u"긋"), u"긋 in eojeol"
    assert postag_end_check(pos_list, u"어/EC"), u"어/EC in eojeol"

    # "ㅅ" 불규칙인데 뒤에 선어말 어미가 있다.
    pos_list = pos_E.endswithE(u"노저었다.")
    # 규칙
    assert postag_left_check(pos_list, u"노저"), u"노저 in eojeol"
    assert postag_end_check(pos_list, u"었/EP+다/EF"), u"었/EP+다/EF in eojeol"
    # 불규칙
    assert postag_left_check(pos_list, u"노젓"), u"노젓 in eojeol"
    assert postag_end_check(pos_list, u"었/EP+다/EF"), u"었/EP+다/EF in eojeol"

    pos_list = pos_E.endswithE(u"노저었지만")
    assert postag_left_check(pos_list, u"노젓"), u"노젓 in eojeol"
    assert postag_end_check(pos_list, u"었/EP+지만/EC"), u"었/EP+지만/EC in eojeol"

    # #### "ㅎ" 불규칙 활용 Case1
    pos_list = pos_E.endswithE(u"까만")
    assert postag_left_check(pos_list, u"까맣"), u"까맣 in eojeol"
    assert postag_end_check(pos_list, u"ㄴ/ETM"), u"ㄴ/ETM in eojeol"

    pos_list = pos_E.endswithE(u"노란")
    assert postag_left_check(pos_list, u"노랗"), u"노랗 in eojeol"
    assert postag_end_check(pos_list, u"ㄴ/ETM"), u"ㄴ/ETM in eojeol"

    pos_list = pos_E.endswithE(u"빨감")
    assert postag_left_check(pos_list, u"빨갛"), u"빨갛빨깧 in eojeol"
    assert postag_end_check(pos_list, u"ㅁ/ETN"), u"ㅁ/ETN in eojeol"

    pos_list = pos_E.endswithE(u"가느다람")
    assert postag_left_check(pos_list, u"가느다랗"), u"가느다랗 in eojeol"
    assert postag_end_check(pos_list, u"ㅁ/ETN"), u"ㅁ/ETN in eojeol"

    # #### "ㅎ" 불규칙 활용 Case2
    pos_list = pos_E.endswithE(u"어때.")
    assert postag_left_check(pos_list, u"어떻"), u"어떻 in eojeol"
    assert postag_end_check(pos_list, u"어/EF"), u"어/EF in eojeol"

    pos_list = pos_E.endswithE(u"어때서.")
    assert postag_left_check(pos_list, u"어떻"), u"어떻 in eojeol"
    assert postag_end_check(pos_list, u"어서/EF"), u"어서/EF in eojeol"

    pos_list = pos_E.endswithE(u"동그래")
    assert postag_left_check(pos_list, u"동그랗"), u"동그랗 in eojeol"
    assert postag_end_check(pos_list, u"어/EC"), u"어/EC in eojeol"

    pos_list = pos_E.endswithE(u"멀개서")
    assert postag_left_check(pos_list, u"멀갛"), u"멀갛 in eojeol"
    assert postag_end_check(pos_list, u"어서/EC"), u"어서/EC in eojeol"

    pos_list = pos_E.endswithE(u"덩그레서")
    assert postag_left_check(pos_list, u"덩그렇"), u"덩그렇 in eojeol"
    assert postag_end_check(pos_list, u"어서/EC"), u"어서/EC in eojeol"

    pos_list = pos_E.endswithE(u"뻘게서")
    assert postag_left_check(pos_list, u"뻘겋"), u"뻘껗 in eojeol"
    assert postag_end_check(pos_list, u"어서/EC"), u"어서/EC in eojeol"

    # 선어말 어미가 들어간 형태
    pos_list = pos_E.endswithE(u"어땠어.")
    assert postag_left_check(pos_list, u"어떻"), u"어떻 in eojeol"
    assert postag_end_check(pos_list, u"었/EP+어/EF"), u"었/EP+어/EF in eojeol"

    pos_list = pos_E.endswithE(u"파랬다.")
    assert postag_left_check(pos_list, u"파랗"), u"파랗 in eojeol"
    assert postag_end_check(pos_list, u"ㅆ/EP+다/EF"), u"ㅆ/EP+다/EF in eojeol"


def test_0009_e():
    """ 불규칙 활용기능 테스트 3"""

    # #### "ㅂ"불규칙
    pos_list = pos_E.endswithE(u"가벼워")
    assert postag_left_check(pos_list, u"가볍"), u"가볍 in eojeol"
    assert postag_end_check(pos_list, u"어/EC"), u"어/EC in eojeol"

    pos_list = pos_E.endswithE(u"무거우니")
    assert postag_left_check(pos_list, u"무겁"), u"무겁 in eojeol"
    assert postag_end_check(pos_list, u"니/EC"), u"니/EC in eojeol"

    # ㅁ, ㄴ이 들어가는 경우
    pos_list = pos_E.endswithE(u"아름다움")
    assert postag_left_check(pos_list, u"아름답"), u"아름답 in eojeol"
    assert postag_end_check(pos_list, u"ㅁ/ETN"), u"ㅁ/ETN in eojeol"

    pos_list = pos_E.endswithE(u"즐거운")
    assert postag_left_check(pos_list, u"즐겁"), u"즐겁 in eojeol"
    assert postag_end_check(pos_list, u"ㄴ/ETM"), u"ㄴ/ETM in eojeol"

    # 선어말 어미가 들어간 형태
    pos_list = pos_E.endswithE(u"슬기로웠다.")
    assert postag_left_check(pos_list, u"슬기롭"), u"슬기롭 in eojeol"
    assert postag_end_check(pos_list, u"았/EP+다/EF"), u"았/EP+다/EF in eojeol"

    pos_list = pos_E.endswithE(u"더웠다.")
    assert postag_left_check(pos_list, u"덥"), u"덥 in eojeol"
    assert postag_end_check(pos_list, u"었/EP+다/EF"), u"었/EP+다/EF in eojeol"

    # #### "으"불규칙
    pos_list = pos_E.endswithE(u"슬퍼")
    assert postag_left_check(pos_list, u"슬프"), u"슬프 in eojeol"
    assert postag_end_check(pos_list, u"어/EC"), u"어/EC in eojeol"

    pos_list = pos_E.endswithE(u"아파서")
    assert postag_left_check(pos_list, u"아프"), u"아프 in eojeol"
    assert postag_end_check(pos_list, u"아서/EC"), u"아서/EC in eojeol"

    pos_list = pos_E.endswithE(u"뒤따라")
    assert postag_left_check(pos_list, u"뒤따르"), u"뒤따르 in eojeol"
    assert postag_end_check(pos_list, u"아/EC"), u"아/EC in eojeol"

    pos_list = pos_E.endswithE(u"들러서")
    assert postag_left_check(pos_list, u"들르"), u"들러 in eojeol"
    assert postag_end_check(pos_list, u"어서/EC"), u"어서/EC in eojeol"

    # 선어말 어미가 들어간 형태
    pos_list = pos_E.endswithE(u"아팠어.")
    assert postag_left_check(pos_list, u"아프"), u"아프 in eojeol"
    assert postag_end_check(pos_list, u"았/EP+어/EF"), u"았/EP+어/EF in eojeol"

    pos_list = pos_E.endswithE(u"들렀어")
    assert postag_left_check(pos_list, u"들르"), u"들러 in eojeol"
    assert postag_end_check(pos_list, u"었/EP+어/EC"), u"었/EP+어/EC in eojeol"

    # #### "르"불규칙
    pos_list = pos_E.endswithE(u"몰라")
    assert postag_left_check(pos_list, u"모르"), u"모르 in eojeol"
    assert postag_end_check(pos_list, u"아/EC"), u"아/EC in eojeol"

    pos_list = pos_E.endswithE(u"굴러서")
    assert postag_left_check(pos_list, u"구르"), u"구르 in eojeol"
    assert postag_end_check(pos_list, u"어서/EC"), u"어서/EC in eojeol"

    # 선어말 어미가 들어간 형태
    pos_list = pos_E.endswithE(u"몰랐어")
    assert postag_left_check(pos_list, u"모르"), u"모르 in eojeol"
    assert postag_end_check(pos_list, u"았/EP+어/EC"), u"았/EP+어/EC in eojeol"

    pos_list = pos_E.endswithE(u"굴렀다")
    assert postag_left_check(pos_list, u"구르"), u"구르 in eojeol"
    assert postag_end_check(pos_list, u"었/EP+다/EC"), u"었/EP+다/EC in eojeol"

    # #### "오"불규칙
    pos_list = pos_E.endswithE(u"다오")
    assert postag_left_check(pos_list, u"달"), u"달 in eojeol"
    assert postag_end_check(pos_list, u"아라/EC"), u"아라/EC in eojeol"

    pos_list = pos_E.endswithE(u"다오.")
    assert postag_left_check(pos_list, u"달"), u"달 in eojeol"
    assert postag_end_check(pos_list, u"아라/EF"), u"아라/EF in eojeol"


def test_0010_e():
    """ 음운 축약 형태 간음화 현상 검사 """
    # #### ㅕ => ㅣ + ㅓ
    pos_list = pos_E.endswithE(u"가려")
    assert postag_left_check(pos_list, u"가리"), u"가리 in eojeol"
    assert postag_end_check(pos_list, u"어/EC"), u"어/EC in eojeol"

    pos_list = pos_E.endswithE(u"다녔고")
    assert postag_left_check(pos_list, u"다니"), u"다니 in eojeol"
    assert postag_end_check(pos_list, u"었/EP+고/EC"), u"었/EP+고/EC in eojeol"

    # #### ㅘ => ㅗ + ㅏ
    pos_list = pos_E.endswithE(u"과")  # # 약재 같은 것을 푹 고아
    assert postag_left_check(pos_list, u"고"), u"고다니 in eojeol"
    assert postag_end_check(pos_list, u"아/EC"), u"아/EC in eojeol"

    pos_list = pos_E.endswithE(u"봤다.")  #
    assert postag_left_check(pos_list, u"보"), u"보 in eojeol"
    assert postag_end_check(pos_list, u"았/EP+다/EF"), u"ㅆ/EP+다/EF in eojeol"

    # ### ㅝ => ㅜ + ㅓ
    pos_list = pos_E.endswithE(u"줘.")
    assert postag_left_check(pos_list, u"주"), u"주 in eojeol"
    assert postag_end_check(pos_list, u"어/EF"), u"어/EF in eojeol"

    pos_list = pos_E.endswithE(u"떨궜다.")  # #
    assert postag_left_check(pos_list, u"떨구"), u"떨구 in eojeol"
    assert postag_end_check(pos_list, u"었/EP+다/EF"), u"었/EP+다/EF in eojeol"

    # #### ㅙ => ㅚ + ㅓ
    pos_list = pos_E.endswithE(u"돼")
    assert postag_left_check(pos_list, u"되"), u"되 in eojeol"
    assert postag_end_check(pos_list, u"어/EC"), u"어/EC in eojeol"

    pos_list = pos_E.endswithE(u"뵀다.")
    assert postag_left_check(pos_list, u"뵈"), u"뵈 in eojeol"
    assert postag_end_check(pos_list, u"었/EP+다/EF"), u"었/EP+다/EF in eojeol"

    # #### 해 => 하 + 여
    pos_list = pos_E.endswithE(u"해")
    assert postag_left_check(pos_list, u"하"), u"하 in eojeol"
    assert postag_end_check(pos_list, u"여/EC"), u"여/EC in eojeol"

    pos_list = pos_E.endswithE(u"흔했다.")
    assert postag_left_check(pos_list, u"흔하"), u"흔하 in eojeol"
    assert postag_end_check(pos_list, u"였/EP+다/EF"), u"였/EP+다/EF in eojeol"

    # #### ㅋ,ㅌ,ㅊ => 하 + ㄱ,ㄷ,ㅈ
    pos_list = pos_E.endswithE(u"간편케")
    assert postag_left_check(pos_list, u"간편하"), u"간편하 in eojeol"
    assert postag_end_check(pos_list, u"게/EC"), u"게/EC in eojeol"

    pos_list = pos_E.endswithE(u"다정타.")
    assert postag_left_check(pos_list, u"다정하"), u"다정하 in eojeol"
    assert postag_end_check(pos_list, u"다/EF"), u"다/EF in eojeol"

    pos_list = pos_E.endswithE(u"무심치")
    assert postag_left_check(pos_list, u"무심하"), u"무심하 in eojeol"
    assert postag_end_check(pos_list, u"지/EC"), u"지/EC in eojeol"

    # #### 동음탈락 ㅏ
    pos_list = pos_E.endswithE(u"숨차")
    assert postag_left_check(pos_list, u"숨차"), u"숨차 in eojeol"
    assert postag_end_check(pos_list, u"아/EC"), u"아/EC in eojeol"

    pos_list = pos_E.endswithE(u"갔다.")
    assert postag_left_check(pos_list, u"가"), u"가 in eojeol"
    assert postag_end_check(pos_list, u"ㅆ/EP+다/EF"), u"ㅆ/EP+다/EF in eojeol"

    pos_list = pos_E.endswithE(u"갔었다.")
    assert postag_left_check(pos_list, u"가"), u"가 in eojeol"
    assert postag_end_check(pos_list, u"ㅆ었/EP+다/EF"), u"ㅆ었/EP+다/EF in eojeol"

    # #### 동음탈락 ㅓ
    pos_list = pos_E.endswithE(u"서.")
    assert postag_left_check(pos_list, u"서"), u"서 in eojeol"
    assert postag_end_check(pos_list, u"어/EF"), u"어/EF in eojeol"

    pos_list = pos_E.endswithE(u"건넜다.")
    assert postag_left_check(pos_list, u"건너"), u"건너 in eojeol"
    assert postag_end_check(pos_list, u"ㅆ/EP+다/EF"), u"ㅆ/EP+다/EF in eojeol"

    pos_list = pos_E.endswithE(u"설레")
    assert postag_left_check(pos_list, u"설레"), u"설레 in eojeol"
    assert postag_end_check(pos_list, u"어/EC"), u"어/EC in eojeol"

    pos_list = pos_E.endswithE(u"달래서")
    assert postag_left_check(pos_list, u"달래"), u"달래 in eojeol"
    assert postag_end_check(pos_list, u"어서/EC"), u"어서/EC in eojeol"

    # ### "하" 탈락현상  "어간안울림받침(ㄱ,ㅂ,ㅅ) + 어미""지"", ""건대"", ""다"""
    pos_list = pos_E.endswithE(u"거북지")
    assert postag_left_check(pos_list, u"거북하"), u"거북지 in eojeol"
    assert postag_end_check(pos_list, u"지/EC"), u"지/EC in eojeol"

    pos_list = pos_E.endswithE(u"익숙지")
    assert postag_left_check(pos_list, u"익숙하"), u"익숙지 in eojeol"
    assert postag_end_check(pos_list, u"지/EC"), u"지/EC in eojeol"

    pos_list = pos_E.endswithE(u"생각건대")
    assert postag_left_check(pos_list, u"생각하"), u"생각건 in eojeol"
    assert postag_end_check(pos_list, u"건대/EC"), u"건대/EC in eojeol"

    pos_list = pos_E.endswithE(u"갑갑다.")
    assert postag_left_check(pos_list, u"갑갑하"), u"갑갑하 in eojeol"
    assert postag_end_check(pos_list, u"다/EF"), u"다/EF in eojeol"


if __name__ == "__main__":
    pytest.main([__file__])

    # test single method
    # pytest.main(["-k test_0010_e"])  # @UndefinedVariable
