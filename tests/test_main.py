import pathmagic  # noqa

from hinsaem import Hinsaem
import pytest
import logging
logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger('test')

hinsaem = Hinsaem()


def setup_function():
    log.debug("==== START " + __package__ + "::" + __name__ + " ====")


def teardown_function():
    log.debug("==== END ====")


def test_0001_dict_loadcheck():
    """ 사전 로드 체크 """
    assert u"가" in hinsaem._word_dict, "Simple Data '가' in word_dict Check "
    assert u"까지" in hinsaem._josa_set, "Simple Data '까지' in _josa_set"
    assert u"라구" in hinsaem._eomi_set, "Simple Data '은' in _eomi_set"
    assert u"구" in hinsaem._eomi_last, "Simple Data '구' in _eomi_last"


def test_0002_dict_josa_check():
    """ 조사로 끝나는 어절의 조사 검사 """
    # 명사로 끝나는 경우에는 None
    pos_list = hinsaem._check_josa_in_eojeol(u"사람")
    assert pos_list is None, u"명사의 경우 None"

    pos_list = hinsaem._check_josa_in_eojeol(u"사람은")
    assert pos_list[0] == u"사람", u"사람 in eojeol"
    assert pos_list[1] == u"은", u"은 in eojeol"

    pos_list = hinsaem._check_josa_in_eojeol(u"너는")
    assert pos_list[0] == u"너", u"너 in eojeol"
    assert pos_list[1] == u"는", u"는 in eojeol"

    pos_list = hinsaem._check_josa_in_eojeol(u"가다")
    assert pos_list is None


def test_0003_dict_eomi_check():
    """ 규칙 어미 테스트 """
    pos_list = hinsaem._check_eomi_in_eojeol(u"가다")
    assert pos_list[0] == u"가"
    assert pos_list[1] == u"다"
    assert pos_list[2] is None

    pos_list = hinsaem._check_eomi_in_eojeol(u"가다.")
    assert pos_list[0] == u"가"
    assert pos_list[1] == u"다"
    assert pos_list[2] == u"."

    pos_list = hinsaem._check_eomi_in_eojeol(u"먹고")
    assert pos_list[0] == u"먹"
    assert pos_list[1] == u"고"
    assert pos_list[2] is None


def test_0004_dict_eomi_check():
    """ 불규칙 어미의 경우 테스트 """
    pos_list = hinsaem._check_eomi_in_eojeol(u"가다")
    assert pos_list[0] == u"가"
    assert pos_list[1] == u"다"
    assert pos_list[2] is None

    pos_list = hinsaem._check_eomi_in_eojeol(u"가다.")
    assert pos_list[0] == u"가"
    assert pos_list[1] == u"다"
    assert pos_list[2] == u"."

    pos_list = hinsaem._check_eomi_in_eojeol(u"먹고")
    assert pos_list[0] == u"먹"
    assert pos_list[1] == u"고"
    assert pos_list[2] is None


# def test_0003_dict_eomi_check():
#     pos_list = hinsaem._check_eomi_in_eojeol(u"안녕하세요")
#     assert pos_list[0] == u"안녕하"
#     assert pos_list[1] == u"세요"


if __name__ == "__main__":
    pytest.main(__file__)

    # test single method
    # pytest.main("-k test_0003_dict_eomi_check")
