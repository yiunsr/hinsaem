"""PosN(체언 관련모듈) Module

이 모듈은 Krcorpus에서 체언분석을 담당하는 부분이다.
이 모듈의 가장 큰 역할은 어절이 체언인지 검사하는 부분이다.

체언의 종류는
1. NNG(일반명사)
2. NNG(일반명사)
3. NNP(고유명사)
4. NNB(의존명사)
5. NR(수사)
6. NP(대명사)

"""
import csv
import copy
import traceback
import enum
import logging
from .config import CONFIG
from .pos_util import union_meta
from .pos_base import PosBase
from .eumjeol_util import check_phoneme_restriction, JONGSUNG_TYPE_NONE,\
    JONGSUNG_TYPE_LIEUL, JONGSUNG_TYPE_COMMON, YANG_VOWEL
from .eumjeol_util import get_jongsung_type, has_jongsung, parse_eumjeol,\
    build_eumjeol, change_jaso

logger = logging.getLogger(__name__)


class PosN(PosBase):
    """
    어미 분석 Class
    """
    GROUP_N = ["NNG", "NNP", "NNB", "NR", "NP"]

    #
    def __init__(self):
        config_dict = self._readDict()
        self._eomi_list = config_dict["EOMI"]
        self._eomi_last = config_dict["EOMI_LAST"]
        self._eomi_jungjong = config_dict["EOMI_JUNGJONG"]
        self._eomi_jungjong_start = config_dict["EOMI_JUNGJONG_START"]
        self._eomi_jungjong_only = config_dict["EOMI_JUNGJONG_ONLY"]

        # 문장부호를 이용한 기호반영
        self._sense_sentence_mark = True

    def _readDict(self):
        multi_dict = {}
        eomi_jungjong = {}
        eomi_jungjong_only = {}
        eomi_jungjong_start = set({})
        eomi_last = set({})

        file_path0 = CONFIG["res_dict_e"]
        with open(file_path0, "r", encoding="UTF-8", newline="") as csvfile:
            # next(csvfile, None)
            for item in csv.DictReader(
                    csvfile, delimiter="\t", dialect="excel-tab"):
                try:
                    word = item["word"]
                    posinfo = {"pos": item["pos"], "pos2": item["pos2"],
                               "phoneme": item["phoneme"],
                               "spoken": item["spoken"],
                               "writing": item["writing"]
                               }

                    if word[0] < u"가":  # 이 경우 완저한 음절이 아니라 부분 문자이다. (ex : ㅁ)
                        if word not in eomi_jungjong:
                            eomi_jungjong[word] = []
                        eomi_jungjong[word].append(posinfo)
                        # 중성, 종성으로 시작하는 어미의 시작 중종성 저정
                        eomi_jungjong_start.add(word[0])

                    # # 어미음절 마지막 음절 Set을 따로 만든다.
                    eomi_last.add(word[-1])
                    if word not in multi_dict:
                        multi_dict[word] = []
                    multi_dict[word].append(posinfo)

                except Exception:
                    tb = traceback.format_exc()
                    print(tb)

        # #### 불규칙에 의한 오류수정
        # "우" 불규칙
        eomi_last.add(u"퍼")

        config_dict = {"EOMI": multi_dict, "EOMI_LAST": eomi_last,
                       "EOMI_JUNGJONG": eomi_jungjong,
                       "EOMI_JUNGJONG_START": eomi_jungjong_start,
                       "EOMI_JUNGJONG_ONLY": eomi_jungjong_only
                       }
        return config_dict

    def endswithE(self, eojeol):
        """
        어미로 종결하는지 검사하고, 어미와 그 외로 구별함

        Args :
            eojeol (str) : 검사하려는 어절
        Returns:
            [ left_word, word, mark ] or None
            left_word : 뒷 조사를 제외한 부분
            word : 어미로 추정되는 단어+형태소
            mark : 문장기호, 없으면 None
            ex) ["달리", "다/EF, "."]
        """
        last_char = eojeol[-1]

        # 문장 종결 기호가 있는지 확인한다.
        mark = None
        if last_char in CONFIG["sentence_mark"]:
            mark = last_char
            last_char = eojeol[-2]
            new_eojeol = eojeol[:-1]
        else:
            new_eojeol = eojeol

        # 문장 종료 기호에 따라서 end_mark 설정
        if not self._sense_sentence_mark:
            pos_filter = self.GROUP_EOMI
        else:
            if mark in CONFIG["sentence_end_mark"]:
                pos_filter = ["EF"]
            else:
                pos_filter = ["EC", "ETM", "ETN"]
        candiate_list = self._endswithES(new_eojeol, mark, pos_filter)

        # # 어미 앞에 선어말 어미가 존재할 수 있기 때문에 선어말 어미가 존재 하지 않을 때
        # # 까지 반복해서 선어말 어미를 찾는다.
        # # 복합어미가 존재해서 같은 형태소 분석이 2개 이상 존재할 수 있기 때문에 제거해야 한다.
        candiate_list_with_ep = []
        duplication_check_set = set({})
        for candiate_item in candiate_list:
            new_eojeol = candiate_item[0]
            postag_tuple = candiate_item[1]
            meta = candiate_item[3]
            for candiate_with_ep in self._endswithES(new_eojeol, None, ["EP"]):
                new_left_word = candiate_with_ep[0]
                postage_tuple_ep = candiate_with_ep[1]
                meta_ep = candiate_with_ep[3]
                new_meta = union_meta(meta_ep, meta)

                # [new_left_word] 가 더해지는 이유는 용언 불규칙 때문에
                # 뒤의 형태소는 같지만 new_left_word 가 다른 경우가 있기 때문에
                # 이 형태를 중복으로 처리하면 안되기 때문이다.
                duplicated_check_key = [new_left_word] + \
                    postage_tuple_ep + postag_tuple
                new_postag_tuple = postage_tuple_ep + postag_tuple

                # # 복합어미 때문에 중복 될 수 있으므로 제거 한다.
                # # 복합어미 길이가 더 길기 때문에
                if tuple(duplicated_check_key) not in duplication_check_set:
                    candiate_list_with_ep.append(
                        [new_left_word, new_postag_tuple, mark, new_meta])
                duplication_check_set.add(tuple(duplicated_check_key))
            else:
                candiate_list_with_ep.append(
                    [new_eojeol, postag_tuple, mark, meta])

        if candiate_list_with_ep == []:
            return None
        return candiate_list_with_ep

    def _endswithES(self, new_eojeol, mark, pos_filter):
        last_char = new_eojeol[-1]

        # #### 마지막 어절의 음절이 어미마지막 음절리스트에 있는지 확인한다.
        # 없는 경우, 규칙활용으로는 없다는 것이다.
        regular_fail = False
        if last_char not in self._eomi_last:
            # 받침으로 결합하는 어미에 대한 예외처리한다.
            (_, _, jong) = parse_eumjeol(last_char)
            if jong not in self._eomi_jungjong_start:
                regular_fail = True
                # return []

        candiate_list = []
        # 최장 음절을 가정하고 최장음절부터 겹치는 조사가 있는지 검사한다.
        # 어미만으로 이루어진 어절은 없기 때문에 어절수-1을 어미 조사로 생각한다.
        eomi_list = self._eomi_list
        eogan_eomi_list = []
        for index in range(0, len(new_eojeol) + 1):
            left_word = new_eojeol[:index]
            candidate_eomi = new_eojeol[index:]
            if left_word != "" and not regular_fail:
                eogan_eomi_list.append(
                    [index, new_eojeol, left_word, candidate_eomi])
            irregular_eogan_eomi_list = self._find_exception_case(
                index, new_eojeol, left_word, candidate_eomi, pos_filter)
            if len(irregular_eogan_eomi_list) > 0:
                eogan_eomi_list.extend(irregular_eogan_eomi_list)

        for eogan_eomi_item in eogan_eomi_list:
            index = eogan_eomi_item[0]

            new_eojeol = eogan_eomi_item[1]
            left_word = eogan_eomi_item[2]
            right_word = eogan_eomi_item[3]

            if left_word == "":
                # 활용된 상태의 어간
                last_eumjeol_eogan = ""
                # 활용되기전의 원래 어간
                org_last_eumjeol_eogan = ""
            else:
                # last_eumjeol_eogan = left_word[-1]
                # 변경되는 어간 형태에 대해서는 변경된 어간 자체로 phoneme 제약을 확인해야 한다.
                # 불규칙에 대해서 불규칙이 반영된 형태로
                last_eumjeol_eogan = new_eojeol[index - 1]
                org_last_eumjeol_eogan = left_word[-1]
            candiate_info = None

            # 받침으로 시작하는 어미
            # 어미 추정 앞 음절이 받침이라고 생각한다.
            (cho, jung, jong) = parse_eumjeol(org_last_eumjeol_eogan)
            if jong in self._eomi_jungjong_start:
                right_word = jong + right_word
                # last_eumjeol_eogan = build_eumjeol(cho, jung, "")
                # 불규칙, 축약이 적용된 어미를 기준으로
                last_eumjeol_eogan = change_jaso(left_word[-1], None, None, "")
                left_word = left_word[:index - 1] + last_eumjeol_eogan
                if right_word in eomi_list:
                    for posinfo in eomi_list[right_word]:
                        if check_phoneme_restriction(
                                last_eumjeol_eogan, posinfo["phoneme"]):
                            postag_tuple = self._pos_select(
                                right_word, posinfo["pos"], posinfo["pos2"])
                            # 추출하려는 형태소가 아니면 패스
                            if postag_tuple[-1][1] not in pos_filter:
                                continue
                            candiate_info = [left_word,
                                             postag_tuple, mark, posinfo]
                            candiate_list.append(candiate_info)

            # 받침으로 시작하는 조사가 매칭되었을 때는
            # 음절로 시작하는 조사가 매칭될 수 있는 경우가 많기 때문에
            # 그냥 무시한다. 예외 Case 가 있는지 확인 필요
            # "들렀어"에서 예외 발생(들러+ㅆ어/EP 로 분석함 )
            if candiate_info:
                continue

            new_eojeol = eogan_eomi_item[1]
            left_word = eogan_eomi_item[2]
            right_word = eogan_eomi_item[3]

            if left_word == "":
                last_eumjeol_eogan = ""
                org_last_eumjeol_eogan = ""
            else:
                # last_eumjeol_eogan = left_word[-1]
                # 변경되는 어간 형태에 대해서는 변경된 어간 자체로 phoneme 제액을 확인해야 한다.
                # 불규칙에 대해서 불규칙이 반영된 형태로
                last_eumjeol_eogan = new_eojeol[index - 1]
                org_last_eumjeol_eogan = left_word[-1]

            if right_word in eomi_list:
                for posinfo in eomi_list[right_word]:
                    if check_phoneme_restriction(
                            last_eumjeol_eogan, posinfo["phoneme"]):
                        postag_tuple = self._pos_select(
                            right_word, posinfo["pos"], posinfo["pos2"])
                        # 추출하려는 형태소가 아니면 패스
                        if postag_tuple[-1][1] not in pos_filter:
                            continue
                        candiate_info = [left_word,
                                         postag_tuple, mark, posinfo]
                        candiate_list.append(candiate_info)

        return candiate_list

    def _find_exception_case(self, index, eojeol, candidate_eogan,
                             candidate_eomi, pos_filter):
        """ 용언 불규칙과 모음축약 현상 처리"""
        eogan_eomi_list = []
        irregular_eogan_eomi_list = self._find_irregular(
            eojeol, candidate_eogan, candidate_eomi, pos_filter)
        for eogan_eomi in irregular_eogan_eomi_list:
            eogan = eogan_eomi[0]
            eomi = eogan_eomi[1]
            eogan_eomi_list.append([index, eojeol, eogan, eomi])

        abbreviation_eogan_eomi_list = self._find_abbreviation(
            eojeol, candidate_eogan, candidate_eomi, pos_filter)
        for eogan_eomi in abbreviation_eogan_eomi_list:
            eogan = eogan_eomi[0]
            eomi = eogan_eomi[1]
            eogan_eomi_list.append([index, eojeol, eogan, eomi])

        return eogan_eomi_list

    def _find_irregular(self, eojeol, candidate_eogan, candidate_eomi,
                        pos_filter):
        """불규칙 용언 원어간, 원어미 추출

        Args :
            eojeol : 어절, 현재는 사용되지 않는다.
            candidate_eogan : 어간 후보
            candidate_eomi : 어미 후보
            pos_filter : 가능한 형태소 품사

        Returns :
            [[eogan1, eomi1], [eogan2, eomi2], ...]

         용언 불규칙 처리 방법
        불규칙 활용정보 : https://ko.wikipedia.org/wiki/%ED%95%9C%EA%B5%AD%EC%96%B4%EC%9D%98_%EB%B6%88%EA%B7%9C%EC%B9%99_%ED%99%9C%EC%9A%A9  # @IgnorePep8
        !!!! 위키백과에서 어간이 바뀐다는 것은 자소 단위이므로 여기에서의 음절단위로 봤을 때와
        다를 수 있다. 따라서 음절로 봤을 때 어간이 바뀌는 경우에도 처리가 필요하다. !!!!

        아래 불규칙은 따로 검사하지 않는다.
        "여" 불규칙은 검사하지 않음(어절리스트에 "여"로 시작하는 어미를 사전리스트에 존재하기 때문에)
        "거라" 불규치 : 가다 또는 ~가다로 끝나는 동사 어간 뒤에 명령형어미 "아라/어라"로 되지 않고 "거라"로 되는 경우
          - 어미가 "거라"와 일치할 때
        "너라" 불규칙 : 오다 또는 ~오다로 끝나는 동사 어간 뒤어 명령형어미 "아라/어라"로 되지 않고 "너라"로 되는 경우
          - 어미가 "너라"와 일치할 때
        "오" 불규칙 : 어미 "-어라/-아라"가 어간 뒤에서 "오"로 바뀌는 불규칙, 오직 다오=>달+아라 한 경우이다.
          - 어질이 "다오"와 일치하는 경우
        """
        eogan_eomi_list = []

        # "ㅎ" 불규칙의 경우 어간, 어미가 한 음절임
        # if candidate_eomi == "":
        #    return eogan_eomi_list

        if len(candidate_eogan) > 0:
            last_eumjeol_eogan = candidate_eogan[-1]
        else:
            last_eumjeol_eogan = ""
        [eogan_cho, eogan_jung, eogan_jong] = parse_eumjeol(last_eumjeol_eogan)

        if len(candidate_eomi) > 0:
            first_eumjeol_eomi = candidate_eomi[0]
        else:
            first_eumjeol_eomi = ""
        [eomi_cho, eomi_jung, eomi_jong] = parse_eumjeol(first_eumjeol_eomi)

        # # 어간이 없는 경우가 없다.
        if candidate_eogan == "":
            return eogan_eomi_list

        # "우" 불규칙 검사
        # 어간 끝 "우"가 어미 "-어" 앞에서 사라지는 활용 형식
        # 용언은 "푸다"가 유일하다
        # "우" 불규칙 검사(오직 푸다만 존재 퍼=>푸다/VV + 어/E )
        #  - 어절 자체를 검사한다.
        # if candidate_eogan == "" and first_eumjeol_eomi == u"퍼":
        #    eogan = u"푸"
        #    eomi = u"어" + candidate_eomi[1:]
        #    eogan_eomi_list.append([eogan, eomi])
        if candidate_eogan in [u"퍼", u"펐"] and candidate_eomi == "":
            eogan = u"푸"
            eomi = change_jaso(u"어", None, None, eogan_jong)
            eogan_eomi_list.append([eogan, eomi, self.Eojel_Type.IRR_U])

        # "ㄷ" 불규칙
        # - 어간 받침 "ㄷ"이  홀소리로 시작하는 어미와 맡나는 경우 어간 받침이 "ㄹ"로 변함
        # ex) (물을) 긷다 =>길어, 길으니  ,  싣다 =>실어, 실으니
        # 간단규칙 : 어간후보가 끝음절이 LAST_EUMJEOL_IRR_D 에 있는지 검사하고 어미후보의
        # 첫음절의 첫소리가 "ㅇ"인지 검사한다.
        # 어간 끝음절 받침은 ㄷ 대신 ㄹ 로 변경
        # 어미는 변경없음
        if last_eumjeol_eogan in self._LAST_EUMJEOL_IRR_D and eomi_cho == u"ㅇ":
            eogan = candidate_eogan[:-1] + \
                change_jaso(last_eumjeol_eogan, None, None, u"ㄷ")
            eomi = candidate_eomi
            eogan_eomi_list.append(
                [eogan, candidate_eomi, self.Eojel_Type.IRR_D])

        # "ㄹ" 불규칙("ㄹ" 탈락)
        # 어간 끝소리 "ㄹ" + 어미 "ㄴ","ㄹ","ㅂ","오","시" 어미를 만나 어간 ㄹ 탈란
        #  - 어미의 마지막이 받침 없음, 어간의 첫소리가 "ㄴ", "ㄹ", "ㅂ", "오", "시" 임
        #  - 어간 끝소리 "르"를 제외하고 , 추정어간 첫음절이
        # "ㄴ", "ㄹ", "ㅂ", "오", "시", "셔"(시의 결합형, "셔", "셨")로 시작하는지,  체크
        if last_eumjeol_eogan in self._LAST_EUMJEOL_IRR_L and\
                (eomi_cho in [u"ㄴ", u"ㄹ", u"ㅂ"]
                 or [eomi_cho, eomi_jung] in [[u"ㅇ", u"ㅗ"], [u"ㅅ", u"ㅣ"],
                                              [u"ㅅ", u"ㅕ"]]):
            eogan = candidate_eogan[:-1] + \
                change_jaso(last_eumjeol_eogan, None, None, u"ㄹ")
            eogan_eomi_list.append(
                [eogan, candidate_eomi, self.Eojel_Type.IRR_L])

        # "ㅅ" 불규칙
        # 어간 끝소리 "ㅅ"이 홀소리로 시작하는 어미 앞에서 사라지는 활용
        # 긋다=>그어, 그으니    낫다 => 나아, 나으니
        #  - 어미 마지막 음절에 받침이 없고, 어간 첫음절이 모음으로 시작하는 경우
        # 간단규칙 : 어간끝소리가 self._LAST_EUMJEOL_IRR_S 이고 어미 첫음절 첫소리가 'ㅇ'인 경우
        if last_eumjeol_eogan in self._LAST_EUMJEOL_IRR_S and eomi_cho == u"ㅇ":
            eogan = candidate_eogan[:-1] + \
                change_jaso(last_eumjeol_eogan, None, None, u"ㅅ")
            eogan_eomi_list.append(
                [eogan, candidate_eomi, self.Eojel_Type.IRR_S])

        # "ㅎ" 불규칙 1
        # 일부 형용사에서 어간 끝 'ㅎ'이
        # 일부 형용사에서 어간 끝 'ㅎ'이 어미 '-ㄴ'이나 '-ㅁ' 앞에서 사라지는 현상
        # 간단규칙 : 어간끝소리가 self._LAST_EUMJEOL_IRR_H_N,  _LAST_EUMJEOL_IRR_H_M 인 경우
        # 어간+어미가 한 음절이기 때문에
        # 어미마지막 음절  대신 어미 첫음절로 체크한다.
        # (어미가 없는 경우 skip 하기 때문에 이시점 검사)
        if first_eumjeol_eomi in self._LAST_EUMJEOL_IRR_H_N:
            eogan = candidate_eogan + \
                change_jaso(first_eumjeol_eomi, None, None, u"ㅎ")
            eomi = u"ㄴ"
            eogan_eomi_list.append([eogan, eomi, self.Eojel_Type.IRR_H1])
        elif first_eumjeol_eomi in self._LAST_EUMJEOL_IRR_H_M:
            eogan = candidate_eogan + \
                change_jaso(first_eumjeol_eomi, None, None, u"ㅎ")
            eomi = u"ㅁ"
            eogan_eomi_list.append([eogan, eomi, self.Eojel_Type.IRR_H1])

        # "ㅎ" 불규칙 2
        # 일부 형용사에서 어간 끝 'ㅎ'이
        # 어미 '-아/-어' 앞에서 ㅣ로 바뀌어 합쳐지는 활용
        # 간단규칙 : 어절에 어때가 있거나 어간끝소리가 self._LAST_EUMJEOL_IRR_AE,
        # _LAST_EUMJEOL_IRR_E 인 경우

        # 중복해서 후보가 되지 않도록 주의한다.
        # 어간, 어미가 한 음절에서 합해지는 경우, 꼭 어간에서 가져간다.
        if candidate_eogan in [u"어때", u"어땠"]:
            eogan = u"어떻"
            eomi = change_jaso(u"어", None, None, eogan_jong) + candidate_eomi
            eogan_eomi_list.append([eogan, eomi, self.Eojel_Type.IRR_H2])
        elif last_eumjeol_eogan in self._LAST_EUMJEOL_IRR_H_AE:
            eogan = candidate_eogan[:-1] + \
                change_jaso(last_eumjeol_eogan, None, u"ㅏ", u"ㅎ")
            eomi = change_jaso(u"어", None, None, eomi_jong) + candidate_eomi
            eogan_eomi_list.append([eogan, eomi, self.Eojel_Type.IRR_H2])
        elif last_eumjeol_eogan in self._LAST_EUMJEOL_IRR_H_E:
            eogan = candidate_eogan[:-1] + \
                change_jaso(last_eumjeol_eogan, None, u"ㅓ", u"ㅎ")
            eomi = change_jaso(u"어", None, None, eomi_jong) + candidate_eomi
            eogan_eomi_list.append([eogan, eomi, self.Eojel_Type.IRR_H2])

        # "ㅂ" 불규칙
        # "어간 끝소리 "ㅂ"이 "우"로 바뀌는 활용 형식이다.
        # "워", "우니"의 형태로 결합되어 나타난다."
        # 가벼워=>가볍/VA+어/EC, 가벼우니=>가볍/VA+니/EC
        # 껄끄러워=>껄끄럽/VA+어/EC, 껄끄러우니=>껄끄럽/VA+니/EC
        # 고와=>곱/VA+어/EC, 과와서=>곱
        # 곱다, 돕다의 경우 "와"로 바뀐다.
        # 간단규칙 : 어간끝음절 _LAST_EUMJEOL_IRR_B1, _LAST_EUMJEOL_IRR_B2 이고
        # 어미첫음절 중성이 ㅘ,ㅝ, ㅗ,ㅜ 인지
        #            검사
        if last_eumjeol_eogan in self._LAST_EUMJEOL_IRR_B1 and\
                eomi_cho == u"ㅇ" and eomi_jung in [u"ㅘ", u"ㅝ"]:
            eogan = candidate_eogan[:-1] + \
                change_jaso(last_eumjeol_eogan, None, None, u"ㅂ")
            if eogan_jung in YANG_VOWEL:  # 양성모음이기 때문에 아
                eomi = change_jaso(
                    u"아", None, None, eomi_jong) + candidate_eomi[1:]
            else:
                eomi = change_jaso(
                    u"어", None, None, eomi_jong) + candidate_eomi[1:]
            eogan_eomi_list.append([eogan, eomi, self.Eojel_Type.IRR_B])

        elif last_eumjeol_eogan in self._LAST_EUMJEOL_IRR_B1 and\
                eomi_cho == u"ㅇ" and eomi_jung in [u"ㅗ", u"ㅜ"]:
            eogan = candidate_eogan[:-1] + \
                change_jaso(last_eumjeol_eogan, None, None, u"ㅂ")
            eomi = eomi_jong + candidate_eomi[1:]
            eogan_eomi_list.append([eogan, eomi, self.Eojel_Type.IRR_B])

        # 설우니 => 섧/VA+
        elif candidate_eogan in self._LAST_EUMJEOL_IRR_B2 and\
                eomi_cho == u"ㅇ" and eomi_jung == u"ㅘ":
            eogan = u"섧"
            if eogan_jung in YANG_VOWEL:  # 양성모음이기 때문에 아
                eomi = change_jaso(
                    u"아", None, None, eomi_jong) + candidate_eomi[1:]
            else:
                eomi = change_jaso(
                    u"어", None, None, eomi_jong) + candidate_eomi[1:]
            eogan_eomi_list.append([eogan, eomi, self.Eojel_Type.IRR_B])
        elif candidate_eogan in self._LAST_EUMJEOL_IRR_B2 and\
                eomi_cho == u"ㅇ" and eomi_jung == u"ㅗ":
            eogan = u"섧"
            eomi = change_jaso(u"어", None, None, eomi_jong) + \
                candidate_eomi[1:]
            eogan_eomi_list.append([eogan, eomi, self.Eojel_Type.IRR_B])

        # "으" 불규칙(으탈락) : 어간 "으"가 연결어마 "아/어", 과거시제 선어말어미 "았/었"을 만나 으탈락함
        #   (EX: 슬퍼서=> 슬프/VA + 서/EC )
        # 간단규칙 : 어간 끝음절이 _LAST_EUMJEOL_IRR_EU 이거나
        # 어간이 _LAST_EUMJEOL_IRR_EU_LEU 인 줄 하나인 경우
        eu_check = False
        if last_eumjeol_eogan in self._LAST_EUMJEOL_IRR_EU or\
                candidate_eogan in self._LAST_EUMJEOL_IRR_EU_LEU:
            eogan = candidate_eogan[:-1] + \
                change_jaso(last_eumjeol_eogan, None, "ㅡ", "")
            eomi = change_jaso(last_eumjeol_eogan, "ㅇ",
                               eogan_jung, eogan_jong) + candidate_eomi
            eogan_eomi_list.append([eogan, eomi, self.Eojel_Type.IRR_EU])
            eu_check = True

        # "러" 불규칙 : 어간 "르"가 어미 "-어/-어서"의 "-어"가 "-러"로 바뀌는 활용 형식
        #  (ex: 검푸르다 =>검푸르러)
        #  - 어미의 마지막이 "르"
        #  - 간단규칙 :  어간후보가 self._LAST_STR_IRR_LEO 인 용언만
        leu_check = False
        if candidate_eogan in self._LAST_STR_IRR_LEO\
                and first_eumjeol_eomi == u"러":
            eomi = u"어" + candidate_eomi[1:]
            eogan = candidate_eogan[:-1] + u"르"
            eogan_eomi_list.append([eogan, eomi, self.Eojel_Type.IRR_LEO])
            leu_check = True

        # "르" 불규칙 : 어간의 끝 음절 '르'가 'ㄹ'로 줄고, 어미 '-아/-어'가 '-라/-러'로 바뀌는 활용
        # (ex: 몰라 => 몰르/VA+아/EC)
        #  - 간단규칙 : "으", "러" 불규칙이 아니고 어간 끝 음절이 ㄹ라/ㄹ러 로 끝나는 경우
        if (not eu_check and not leu_check and len(candidate_eogan) >= 2 and
                parse_eumjeol(candidate_eogan[-2])[2] == u"ㄹ" and
                [eogan_cho, eogan_jung] in [[u"ㄹ", u"ㅏ"], [u"ㄹ", u"ㅓ"]]):
            eogan = candidate_eogan[:-3] + \
                change_jaso(candidate_eogan[-2], None, None, "") + u"르"
            eomi = change_jaso(last_eumjeol_eogan, u"ㅇ",
                               None, None) + candidate_eomi
            eogan_eomi_list.append([eogan, eomi, self.Eojel_Type.IRR_LEU])

        # "오" 불규칙 : 어미 '-아라/어라'가 어간 뒤에서 '오'로 바뀌는 활용
        # 다오 => 달/VV+아라/EF 가 유일하다.
        if candidate_eogan == u"다" and candidate_eomi == u"오":
            eogan_eomi_list.append([u"달", u"아라", self.Eojel_Type.IRR_O])

        return eogan_eomi_list

    def _find_abbreviation(self, eojeol, candidate_eogan, candidate_eomi,
                           pos_filter):
        """모음 축약현상을 처리해 원어간, 원어미를 분리한다.
        준말에 관한 사항은 한글맞춤법 4장(형태에 관한 것) 5절(준말) 항목에 잘 나와 있다.

        Args :
            eoejl : 어절, 현재는 이용되지 않는다.
            candidate_eogan : 어간후보
            candidate_eomi : 어미후보
            pos_filter : 가능한 형태소 품사

        Returns :
            [[eogan1, eomi1], [eogan2, eomi2], ...]
        """

        eogan_eomi_list = []
        if len(candidate_eogan) > 0:
            last_eumjeol_eogan = candidate_eogan[-1]
        else:
            last_eumjeol_eogan = ""
        [eogan_cho, eogan_jung, eogan_jong] = parse_eumjeol(last_eumjeol_eogan)

        if len(candidate_eomi) > 0:
            first_eumjeol_eomi = candidate_eomi[0]
        else:
            first_eumjeol_eomi = ""
        [eomi_cho, eomi_jung, eomi_jong] = parse_eumjeol(first_eumjeol_eomi)

        """
        간음화 : 간음화는 앞뒤 음절의 모음이 만나 서로 영향을 주고받아 두 모음의 중간음으로
           단일화 되는 현상으로 'ㅏ, ㅓ, ㅗ, ㅜ'가 'ㅣ'와 만나면 'ㅐ, ㅔ, ㅚ, ㅟ'로 변화하게 된다.
           이 현상은 용언+어미 결합간에 발생하는 것이 없어 보이므로 처리하지 않는다.
           (어미가 이인 )
           이 현상의 경우 용언내의 축약이기 때문에 사전에 추가하는 식으로 처리한다.
           (보이다=>뵈다  뵈/VV 라는 정보가 사전내에 존재한다. )
        """

        """
        이중모음화 : 두 단모음이 합쳐져 하나의 이중모음이 된다.
        ㅒ => ㅣ + ㅑ 는 용언+어미 결합이 없어보여 제외
        ㅛ => ㅣ + ㅗ 는 용언+어미 결합이 없어보여 제외
        ㅢ => ㅡ + ㅣ 는 용언+어미 결합이 없어보여 제외
            쓰이다, 뜨이다 같은 경우 씌다, 띄다 가 사전에 등록되어 있음
        """
        if eogan_jung == u"ㅕ" and eogan_jong in ["", u"ㅆ"]:
            """ ㅕ => ㅣ + ㅓ
            가려->가리어, 다녀->다니어, 꾸며->꾸미어
            가렸다=> 가리었다,  다녔고 => 다니었고,  꾸몄으나 => 꾸미었으나
            """
            eogan = candidate_eogan[:-1] + build_eumjeol(eogan_cho, u"ㅣ", "")
            eomi = build_eumjeol(u"ㅇ", u"ㅓ", eogan_jong) + candidate_eomi
            eogan_eomi_list.append([eogan, eomi, self.Eojel_Type.ABB_YEO])

        elif eogan_jung == u"ㅘ" and eogan_jong in ["", u"ㅆ"]:
            """  ㅘ => ㅗ + ㅏ
            봐 => 보아,  와 => 오아, 과 => 고아(한약, 약재 같은 것을 푹 끓이다.)
            봤다 => 보았다.  왔고 => 오았고
            """
            eogan = candidate_eogan[:-1] + build_eumjeol(eogan_cho, u"ㅗ", "")
            eomi = build_eumjeol(u"ㅇ", u"ㅏ", eogan_jong) + candidate_eomi
            eogan_eomi_list.append([eogan, eomi, self.Eojel_Type.ABB_WA])

        elif eogan_jung == u"ㅝ" and eogan_jong in ["", u"ㅆ"]:
            """  ㅝ => ㅜ + ㅓ
            줘 => 주어,  떨궈 => 떨구어, 둬 =>두어
            줬고 => 주었고, 떨궜다 => 떨구었다

            """
            eogan = candidate_eogan[:-1] + build_eumjeol(eogan_cho, u"ㅜ", "")
            eomi = build_eumjeol(u"ㅇ", u"ㅓ", eogan_jong) + candidate_eomi
            eogan_eomi_list.append([eogan, eomi, self.Eojel_Type.ABB_WO])

        elif eogan_jung == u"ㅙ" and eogan_jong in ["", u"ㅆ"]:
            """  ㅙ => ㅚ + ㅓ
            돼 => 되어,  봬서 => 뵈어서, 왜 -> 외어, 쇄 -> 쇠어
            됐어 -> 되었어, 쇘다 -> 쇠었다
            """
            eogan = candidate_eogan[:-1] + build_eumjeol(eogan_cho, u"ㅚ", "")
            eomi = build_eumjeol(u"ㅇ", u"ㅓ", eogan_jong) + candidate_eomi
            eogan_eomi_list.append([eogan, eomi, self.Eojel_Type.ABB_WAE])

        elif last_eumjeol_eogan in [u"해", u"했"]:
            """ 축약 "해"
            한글맞춤법 제 34항 붙임 2
            하 + 여 => 해
            해 => 하여,  더해 => 더하여,  했다 => 하였다,  흔했다 => 흔하였다.
            """
            eogan = candidate_eogan[:-1] + u"하"
            eomi = build_eumjeol(u"ㅇ", u"ㅕ", eogan_jong) + candidate_eomi
            eogan_eomi_list.append([eogan, eomi, self.Eojel_Type.ABB_HAE])

        elif len(candidate_eogan) >= 2 and eogan_cho in [u"ㅊ", u"ㅋ", u"ㅌ"]:
            """ 하 다음의 음절의 첫소리가 거센소리로 적히는 현상
            한글맞춤법 제 40항
            간편케 => 간편하게, 달성코자 =>달성하고자, 청컨대 => 청하건대
            다정타 => 다정하다, 연구토록 => 연구하도록, 부지런타 => 부지런하다
            무심치 => 무심하지, 허송치 => 허송하지, 당치 => 당하지
            """
            eogan = candidate_eogan[:-1] + u"하"
            cho = {u"ㅊ": u"ㅈ", u"ㅋ": u"ㄱ", u"ㅌ": u"ㄷ"}[eogan_cho]
            eomi = build_eumjeol(cho, eogan_jung, eogan_jong) + candidate_eomi
            eogan_eomi_list.append([eogan, eomi, self.Eojel_Type.ABB_ASPIRATE])

        elif eogan_jong in [u"ㄱ", u"ㅂ", u"ㅅ"] and\
                first_eumjeol_eomi in [u"지", u"다", u"건"]:
            """  안울림소리 받침(ㄱ,ㅂ,ㅅ) + 하 + (지, 다, 건대)  결합시 "하" 생략 현상
            한글맞춤법 제 40항
            거북지 => 거북하지 , 넉넉지 않다 => 넉넉하지 않다, 익숙지 않다. => 익숙하지 않다
            생각건대 => 생각하건대 ,  추측건대 => 추측하건대
            생각다 못해 => 생각하다,  갑갑다 => 갑갑하다.
            """
            eogan = candidate_eogan + u"하"
            eomi = candidate_eomi
            eogan_eomi_list.append([eogan, eomi, self.Eojel_Type.DROPOUT_HA])

        elif len(candidate_eogan) >= 1 and first_eumjeol_eomi == u"찮":
            """ 찮 축약
            미리 추출해야 할 수 있다.
            한글맞춤법 제 39항
            -하지 않-  => -찮- 으로 축약되는 현상
            만만찮은 => 만만하지 않은,   변변찮다 => 변변하지 않다.
            심심찮다 => 심심하지 않다
            """
            eogan = candidate_eogan + u"하"
            eomi = u"지 않은" + candidate_eomi
            eogan_eomi_list.append([eogan, eomi, self.Eojel_Type.ABB_CHANH])

        elif len(candidate_eogan) >= 1 and first_eumjeol_eomi == u"잖":
            """ 잖 축약
            미리 추출해야 할 수 있다.
            한글맞춤법 제 39항
            -하지 않-  => -찮- 으로 축약되는 현상
            적잖은 => 적지 않은,   그렇잖은 => 그렇지 않은
            남부럽잖다 => 남부럽지 않다
            """
            eogan = candidate_eogan
            eomi = u"지 않은" + candidate_eomi
            eogan_eomi_list.append([eogan, eomi, self.Eojel_Type.ABB_JANH])

        # pos_filter가 선어말어미가 아니어야 한다.
        if eogan_jung == u"ㅏ" and eogan_jong == "" and\
                candidate_eomi == "" and "EP" not in pos_filter:
            """ 동음탈락 "아"
            한글맞춤법 제 34항
            ㅏ계열 가=>가아, 자=>자아, 차->차아, 타->타아
            """
            eogan = candidate_eogan
            eomi = u"아" + candidate_eomi
            eogan_eomi_list.append([eogan, eomi, self.Eojel_Type.DROPOUT_A])

        elif last_eumjeol_eogan in self._LAST_EUMJEOL_DROPOUT_EO\
                and candidate_eomi == "" and "EP" not in pos_filter:
            """ 동음탈락 "어"
            한글맞춤법 제 34항과 붙임 1
            ㅓ계열  건너=>건너어, 서=>서어 , 갈라서=>갈라서
            ㅕ계열  펴 =>펴어, 켜=>켜어
            ㅔ계열  건네=>건네어, 설레=>설레어, 목메=>목메어
            ㅐ계열 깨=>깨어, 달래서=>달래어서,  캐=>캐어, 보태=>보태어, 채 => 채어

            """
            eogan = candidate_eogan
            eomi = u"어" + candidate_eomi
            eogan_eomi_list.append([eogan, eomi, self.Eojel_Type.DROPOUT_EO])

        return eogan_eomi_list
