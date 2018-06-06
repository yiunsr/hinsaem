"""Main Module

이 모듈은 Hinsame Pos Tagger에서 핵심을 담당하는 부분이다. 문장을 어절단위로 나누고,
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
from .eumjeol_util import has_jongsung, parse_eumjeol, build_eumjeol

logger = logging.getLogger(__name__)


class Hinsaem(object):
    """형태소 분석 기본 Class

    자동으로 사전정보 로딩
    어절별 형태소 분석
    """
    GROUP_N = ["NNG", "NNP", "NNB", "NR", "NP"]     # 체언
    GROUP_MA = ["MAG", "MAJ"]   # 부사
    GROUP_MM = ["MM"]   # 관형사
    GROUP_IC = ["IC"]   # 감탄사
    GROUP_JOSA = ["JKS", "JKC", "JKG", "JKO", "JKB", "JKV", "JKQ", "JC", "JX"]
    GROUP_EOMI = ["EC", "EF", "ETN", "ETM"]

    SINGLE_EOJEOL_MORPHEME_LIST = []
    SINGLE_EOJEOL_MORPHEME_LIST.extend(GROUP_N)
    SINGLE_EOJEOL_MORPHEME_LIST.extend(GROUP_MA)
    SINGLE_EOJEOL_MORPHEME_LIST.extend(GROUP_MM)
    SINGLE_EOJEOL_MORPHEME_LIST.extend(GROUP_IC)

    # 받침이 있는 체언에 결합하는 조사
    JOSA_PRE_BADCHIM_LIST = [u"이", u"은", u"을", u"과", u"아",
                             u"이여", u"이랑"]

    # 받침이 없는 체언에 결합하는 조사
    JOSA_PRE_NONBADCHIM_LIST = [u"가", u"는", u"를", u"와", u"고",
                                u"다", u"든", u"라", u"랑", u"며",
                                u"야", u"여"]
    # ㄹ받침이 있거나 받침이 없는 체언에 결합하는 조사
    JOSA_PRE_RIEUL_LIST = [u"로"]

    # ㄹ받침 외의 받침이 있는 체언에 결합하는 조사
    JOSA_PRE_RIEUL_LIST = [u"으로"]

    # 고유명사와 결합할 때 '이'가 삽입되는 조사
    JOSA_INSERT_YI_LIST = [u"이가"]

    # 종료문장기호
    SENTENSE_STOP_MARK = [".", "!", "?"]

    # 문장기호
    SENTENSE_MARK = [",", ".", "!", "?"]

    def __init__(self):
        json_info = self._readDict()
        self._word_dict = json_info["ALL"]
        self._josa_set = json_info["JOSA"]
        self._josa_last = json_info["JOSA_LAST"]
        self._eomi_set = json_info["EOMI"]
        self._eomi_last = json_info["EOMI_LAST"]

    def _readDict(self):
        multi_dict = {}
        josa_set = set({})
        josa_last = set({})
        eomi_set = set({})
        eomi_last = set({})
        file_path0 = CONFIG["res_dict_01"]
        with open(file_path0, 'r', encoding='UTF-8', newline='') as csvfile:
            next(csvfile, None)
            for line in csv.reader(
                    csvfile, delimiter="\t", dialect="excel-tab"):
                try:
                    word = line[0]
                    morpheme = line[1]
                    if word not in multi_dict:
                        multi_dict[word] = [morpheme]
                    else:
                        multi_dict[word].append(morpheme)

                    # # 따로 조사 Set을 만든다.
                    # # 조사음절 마지막 음절 Set을 따로 만든다.
                    if morpheme in self.GROUP_JOSA:
                        josa_set.add(word)
                        josa_last.add(word[-1])

                    # # 따로 어미 Set을 만든다.
                    # # 어미음절 마지막 음절 Set을 따로 만든다.
                    if morpheme in self.GROUP_EOMI:
                        eomi_set.add(word)
                        eomi_last.add(word[-1])
                except Exception:
                    tb = traceback.format_exc()
                    print(tb)

        config_dict = {"ALL": multi_dict, "JOSA": josa_set,
                       "JOSA_LAST": josa_last,
                       "EOMI": eomi_set, "EOMI_LAST": eomi_last}
        return config_dict

    def _parse_sen(self, sen):
        """문장을 어절로 나눔

        Args:
            sen (str): 문장

        Returns:
            List[str,str,...] : 어절 리스트
        """
        word_list = []
        for eojeol in sen.split(" "):
            pos_info = self._parse_eojeol(eojeol)
            word_list.append(pos_info)
        return word_list

    # todo : 동일한 형태소가 여러개 인 경우, 후보군 생성 필요함
    def _parse_eojeol(self, eojeol):
        """어절을 형태소 단위로 나눔, 후보가 여러가 일 때, 리스트로 전달함

        Args:
            eojeol (str) : 어절

        Returns:
            List[postag : str]
            postag : 어절/형태소 + 로 표시한 기호(Split 를 위해 + 기호 앞뒤는 무조건 스패이스)
                      슬래쉬(/)는 그대로 표시
            self._parse_eojeol("나는")
            => ["나/NP + 는/JX", "나/VV + 는/ETD"]
        """
        word_dict = self._word_dict

        # 단일어 검사(체언, 부사, 관형사, 감탄사 검사)
        if eojeol in word_dict:
            union_set = set(word_dict[eojeol]) &\
                set(self.SINGLE_EOJEOL_MORPHEME_LIST)
            if union_set != {}:
                return [eojeol, list(union_set)[0]]

        [josa_check, josa] = self._check_josa_in_eojeol(eojeol)
        if josa_check:
            return josa

        # 어미검사
        [eomi_check, eomi] = self._check_eomi_in_eojeol(eojeol)
        return []

    def _check_eomi_in_eojeol(self, eojeol):
        """
        어미로 종결하는지 검사하고, 어미와 그 외로 구별함

        Arg :
            eojeol : 어절
        Returns:
            List[ List[ left_word, word, mark ], ... ]
            left_word : 뒷 어미를 제외한 부분
            word : 어미로 추정되는 단어
            mark : 문장기호
        """
        # 마지막 어절의 음절이 어미마지막 음절리스트에 있는지 확인한다.
        eomi_last = self._eomi_last
        last_char = eojeol[-1]

        # 문장 종결 기호가 있는지 확인한다.
        mark = None
        if last_char in self.SENTENSE_MARK:
            mark = last_char
            last_char = eojeol[-2]
            new_eojeol = eojeol[:-1]
        else:
            new_eojeol = eojeol

        # todo :  마지막 글자가 없으나 ㄴ,ㄹ,ㅁ 받침만 존재하는 어절이 있으므로 확인 필요하다.
        if last_char not in eomi_last:
            return None

        # 어미 검사
        eomi_set = self._eomi_set
        for index in range(1, len(new_eojeol)):
            candidate_word = new_eojeol[index:]
            left_word = new_eojeol[:index]
            if candidate_word in eomi_set:
                return [left_word, candidate_word, mark]

            # 불규칙 검사
            self._check_irregular_emoi(new_eojeol, candidate_word)

            # ㄴ,ㄹ,ㅁ,ㅂ,ㅆ의 경우 받침으로 결합해서 체크함

            # 모음단위의 결합 체크
            # ㅘ, ㅝ ( 봐 =>보+아,  헹궈=>헹구 + 어 )
            candidate_list = []

        # 용언+어미인데 어미가 결합되는 경우
        # 가 => 가/VV + 아/E 같은 경우, 짜증나 => 짜증나/VV + 아/E
        # 건너=>건너/VV + 어/E

        return [False, None]

    def _check_irregular_emoi(self, eojeol, candidate_eomi):
        """ 용언 불규칙 처리 방법
        불규칙 활용정보 : https://ko.wikipedia.org/wiki/%ED%95%9C%EA%B5%AD%EC%96%B4%EC%9D%98_%EB%B6%88%EA%B7%9C%EC%B9%99_%ED%99%9C%EC%9A%A9  # @IgnorePep8
        !!!! 위키백과에서 어간이 바뀐다는 것은 자소 단위이므로 여기에서의 음절단위로 봤을 때와
        다를 수 있다. 따라서 음절로 봤을 때 어간이 바뀌는 경우에도 처리가 필요하다. !!!!
        어미가 변경되는 불규칙 검사
        어미후보 첫 음절을 이용해서 검사한다.
        "여" 불규칙은 검사하지 않음(어절리스트에 "여"로 시작하는 어미를 사전리스트에 존재하기 때문에)
        "우" 불규칙 검사(오직 푸다만 존재 퍼=>푸다/VV + 어/E )
          - 어절 자체를 검사한다.
        "ㅎ" 불규칙 검사(일부 형용사어간 끝"ㅎ"이 어미 "ㄴ, ㅁ"앞에서 사라지는 현상은 이 함수에서 취급안함 )
          - 어미 "-아/-어" 앞에서 ㅣ로 합쳐지는 현상만 처리
          - 해당 불규칙이 말생하는 끝음절은 개,대,때,래,매,얘
        "ㅂ" 불규칙 : 어간 끝소리 'ㅂ'이 우로 바꾸는 활용(ex : 가볍워=>가볍/VA + 어/EM )
          - 어미후보 첫음절 :  워,우니,와(고와의 경우) 인 경우
        "으" 불규칙(으탈락) : 어간 "으"가 연결어마 "아/어", 과거시제 선어말어미 "았/었"을 만나 으탈락함
           (EX: 슬퍼서=> 슬프다/VA + 다/E )
          - 해당 용언 끝음절은 그, 끄,느,뜨,르,쁘,쓰,으,크,트,프 이고 이에 따라서
            "가","거","갔","갔","까","꺼","갔","겄", ..........., "파","퍼","팠","펐"
        todo : 으 불규칙 어미 첫음절 최적화 가능(아/어, 았/었 둘 중 하나만 있는 경우 있음)

        "르" 불규칙 : 어간 끝 음절 '르'가 받침 ㄹ로 줄고, 어미 '아/어','았/었/ 이 '라/러', '랐/렀' 으로
                변하는 현상
          - 어간 끝음절에 ㄹ이 있고 어미 첫음절이 라,러,랐,렀 인 경우
        "거라" 불규치 : 가다 또는 ~가다로 끝나는 동사 어간 뒤에 명령형어미 "아라/어라"로 되지 않고 "거라"로 되는 경우
          - 어미가 "거라"와 일치할 때
        "너라" 불규칙 : 오다 또는 ~오다로 끝나는 동사 어간 뒤어 명령형어미 "아라/어라"로 되지 않고 "너라"로 되는 경우
          - 어미가 "너라"와 일치할 때
        "오" 불규칙 : 어미 "-어라/-아라"가 어간 뒤에서 "오"로 바뀌는 불규칙, 오직 다오=>달+아라 한 경우이다.
          - 어질이 "다오"와 일치하는 경우
        """

        word_dict = self._word_dict
        candidate_eogan = eojeol[:-len(candidate_eomi)]

        # "러" 불규칙 검사 : 어미 '-어/-어서'의 '-어'가 '-러'로 바뀌는 활용 형식(ex: 검푸르다 =>검푸르러)
        #   - 어간에 러가 있는경우
        if candidate_eomi[0] == "러":
            new_candidate_eomi = "어" + candidate_eomi[1:]
            new_candidate_eogan = candidate_eogan[:-1] + "르"

        return ""

    # 어간이 변경되는 불규칙 검사
    def check_irregular_eogan1(self, candidate_eogan, candidate_eomi):
        word_dict = self._word_dict

        # ㄷ 불규칙 검사
        # 어간 받침 'ㄷ'이 홀소리(모음)으로 시작되는 어미 앞에서 'ㄹ'로 바뀌는 활용
        # (물을) 긷다 =>길어, 길으니
        # 어미 후보가 모음으로 시작하고 어간끝을절이 ㄹ 받침이어야 한다.
        if parse_eumjeol(candidate_eogan[-1]) == "ㄹ" and\
                parse_eumjeol(candidate_eomi[0])[0] == "o":
            jaso = parse_eumjeol(candidate_eogan[-1])
            eogan = candidate_eogan[:-1] + build_eumjeol(jaso[0], jaso[1], "ㄹ")
            return eogan

        # 우 불규칙 검사
        # 어간 끝 '우'가 어미 '-어' 앞에서 사라지는 활용 형식
        # 용언은 '푸다'가 유일하다
        # todo

        # ㅅ 불규칙
        # 어간 끝소리 'ㅅ'이 홀소리로 시작하는 어미 앞에서 사라지는 활용
        # 긋다=>그어, 그으니    낫다 => 나아, 나으니
        if parse_eumjeol(candidate_eogan[-1]) == "ㅅ" and\
                parse_eumjeol(candidate_eomi[0])[0] == "o":
            jaso = parse_eumjeol(candidate_eogan[-1])
            eogan = candidate_eogan[:-1] + build_eumjeol(jaso[0], jaso[1], "ㅅ")
            return eogan

        # ㅂ 불규칙
        # "어간 끝소리 'ㅂ'이 '우'로 바뀌는 활용 형식이다.
        # '워', '우니'의 형태로 결합되어 나타난다."
        # 가볍다=>가벼워, 가벼우니   껄끄럽다=>껄끄러워, 껄끄러우니
        # 곱다, 돕다의 경우 '와'로 바뀐다.
        if parse_eumjeol(candidate_eogan[-1]) == "ㅅ" and\
                parse_eumjeol(candidate_eomi[0])[0] == "o":
            jaso = parse_eumjeol(candidate_eogan[-1])
            eogan = candidate_eogan[:-1] + build_eumjeol(jaso[0], jaso[1], "ㅅ")
            return eogan

    def _check_word_in_dict(self, candidate_word, postag_list):
        word_dict = self._word_dict
        if candidate_word not in word_dict[candidate_word]:
            return False
        word_list = word_dict[candidate_word]
        for word, postag in word_list:
            if postag in postag_list:
                return True
        return False


if __name__ == "__main__":
    try:
        print("Hello, Hinsaem Pos Tagger")
    except Exception:
        tb = traceback.format_exc()
        print(tb)
