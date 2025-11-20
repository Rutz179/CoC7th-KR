#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CoC7 Roll Requests compendium translator for Babele.

필요 파일 (같은 폴더에 두세요):
- CoC7.roll-requests.json  : 추출한 원본 롤 리퀘스트 저널
- CoC7.skills.json          : 기능 컴팬디움 번역 파일
- ko.json                   : CoC7 시스템 전체 한글화 JSON

실행:
    python translate_roll_requests.py

결과:
    CoC7.roll-requests.ko.json 이 생성됩니다.
"""

from pathlib import Path
import itertools
import json
import re

ROOT = Path(__file__).parent

ROLL_FILE = ROOT / "CoC7.roll-requests.json"
SKILLS_FILE = ROOT / "CoC7.skills.json"
KO_FILE = ROOT / "ko.json"
OUT_FILE = ROOT / "CoC7.roll-requests.ko.json"

MACRO_RE = re.compile(r"(@coc7\.check\[[^\]]*]\s*\{)([^}]*)(\})")


def load_json(path: Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def build_maps():
    """ko.json, CoC7.skills.json 에서 매핑 딕셔너리 생성"""
    ko = load_json(KO_FILE)
    skills = load_json(SKILLS_FILE)

    # 기능 이름: "Accounting" -> "회계"
    skill_map = {
        name: entry.get("name", name)
        for name, entry in skills.get("entries", {}).items()
    }

    # 능력치/이성/운
    attr_map = {
        "STR": ko.get("CHARAC.STR", "STR"),
        "CON": ko.get("CHARAC.CON", "CON"),
        "SIZ": ko.get("CHARAC.SIZ", "SIZ"),
        "DEX": ko.get("CHARAC.DEX", "DEX"),
        "APP": ko.get("CHARAC.APP", "APP"),
        "INT": ko.get("CHARAC.INT", "INT"),
        "POW": ko.get("CHARAC.POW", "POW"),
        "EDU": ko.get("CHARAC.EDU", "EDU"),
        "Luck": ko.get("CoC7.Luck", "Luck"),
        "Sanity": ko.get("CoC7.Sanity", "Sanity"),
    }

    # 표 안에서 쓰이는 일반 텍스트
    base_text_map = {
        # 헤더
        "Type": "유형",
        "Name": ko.get("CoC7.Name", "이름"),
        "Parameters": "조건",
        "Code": "코드",
        # 타입 구분
        "Attrib": "능력치",
        "Characteristic": "특성",
        "Skill": ko.get("CoC7.Skill", "기능"),
        # 난이도
        "Regular": ko.get("CoC7.RegularDifficulty", "보통"),
        "Hard": ko.get("CoC7.HardDifficulty", "어려움"),
        "Extreme": ko.get("CoC7.ExtremeDifficulty", "극단적"),
        "Critical": ko.get("CoC7.CriticalDifficulty", "대성공"),
        "Blind": ko.get("CoC7.Blind", "비공개"),
        # 보너스/패널티 표기
        "1 Bonus": "보너스 1",
        "2 Bonus": "보너스 2",
        "1 Penalty": "패널티 1",
        "2 Penalty": "패널티 2",
    }

    # 매크로 라벨에서 쓰이는 접미사
    suffix_map = {
        "Hard": base_text_map["Hard"],
        "Extreme": base_text_map["Extreme"],
        "Critical": base_text_map["Critical"],
        "Blind": base_text_map["Blind"],
        # 1B, 2B, 1P, 2P 는 그대로 두고 싶으면 그대로, 번역하고 싶으면 바꿔도 됨
        "1B": "1B",
        "2B": "2B",
        "1P": "1P",
        "2P": "2P",
    }

    return skill_map, attr_map, base_text_map, suffix_map


def translate_name(name: str, skill_map, attr_map) -> str:
    """영어 이름을 기능/능력치 매핑으로 한글화"""
    name = name.strip()
    if name in skill_map:
        return skill_map[name]
    if name in attr_map:
        return attr_map[name]
    return name


def translate_macro_label(label: str, skill_map, attr_map, suffix_map) -> str:
    """
    매크로 표시 라벨 한글화.

    예:
      Luck               -> 운
      Luck (Hard)        -> 운 (어려움)
      Accounting (1B)    -> 회계 (1B)
      Art/Craft (Fine Art) (Hard)
        -> 예술/공예 (미술) (어려움)
    """
    label = label.strip()

    # 난이도/보너스 접미사가 붙은 경우만 따로 처리
    for suf, suf_ko in suffix_map.items():
        pattern = f" ({suf})"
        if label.endswith(pattern):
            base = label[:-len(pattern)]
            base_ko = translate_name(base, skill_map, attr_map)
            return f"{base_ko} ({suf_ko})"

    # 접미사가 없으면 그냥 이름만 번역
    return translate_name(label, skill_map, attr_map)


def replace_macro_labels(html: str, skill_map, attr_map, suffix_map) -> str:
    """@coc7.check[...] { 라벨 } 부분만 잡아서 한글로 교체"""

    def repl(match: re.Match) -> str:
        prefix, label, suffix = match.groups()
        new_label = translate_macro_label(label, skill_map, attr_map, suffix_map)
        return prefix + new_label + suffix

    return MACRO_RE.sub(repl, html)


def replace_whole_tag_text(html: str, src: str, dst: str) -> str:
    """
    > 영문 < 꼴로 태그 안에 '그 글자만' 들어있는 경우만 치환.

    매크로 인자 name:Luck 같은 것은 건드리지 않기 위해 이렇게 한정.
    """
    pattern = re.compile(rf">\s*{re.escape(src)}\s*<")
    return pattern.sub(lambda m: m.group(0).replace(src, dst), html)


def main():
    if not ROLL_FILE.exists():
        raise SystemExit(f"입력 파일을 찾을 수 없습니다: {ROLL_FILE}")
    if not SKILLS_FILE.exists():
        raise SystemExit(f"기능 매핑 파일을 찾을 수 없습니다: {SKILLS_FILE}")
    if not KO_FILE.exists():
        raise SystemExit(f"ko.json 을 찾을 수 없습니다: {KO_FILE}")

    data = load_json(ROLL_FILE)
    skill_map, attr_map, base_text_map, suffix_map = build_maps()

    # 일단 Roll Requests 저널 하나만 있다는 가정
    try:
        page = data["entries"]["Roll Requests"]["pages"][0]
    except Exception as e:
        raise SystemExit(f"Roll Requests 페이지 구조를 읽지 못했습니다: {e}")

    html = page["text"]["content"]

    # 1) 매크로 라벨 한글화
    html = replace_macro_labels(html, skill_map, attr_map, suffix_map)

    # 2) 표 안의 일반 텍스트 한글화
    for src, dst in itertools.chain(
        base_text_map.items(), attr_map.items(), skill_map.items()
    ):
        html = replace_whole_tag_text(html, src, dst)

    # 결과를 새 JSON에 반영
    data_out = data.copy()
    data_out["entries"]["Roll Requests"]["pages"][0]["text"]["content"] = html

    with OUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(data_out, f, ensure_ascii=False, indent=2)

    print(f"완료: {OUT_FILE.name} 에 저장했습니다.")


if __name__ == "__main__":
    main()
