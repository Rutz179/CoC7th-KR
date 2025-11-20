#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
CoC7 Roll Requests compendium translator for Babele.
수정 버전: 매크로 인자 name:영문 → name:한글 로 변환까지 지원
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

# 매크로 전체 (@coc7.check[...] {label})
MACRO_FULL_RE = re.compile(
    r"(@coc7\.check\[([^\]]*)]\s*\{([^}]*)})"
)

def load_json(path: Path):
    with path.open(encoding="utf-8") as f:
        return json.load(f)


def build_maps():
    ko = load_json(KO_FILE)
    skills = load_json(SKILLS_FILE)

    # 기능 매핑: English → Korean
    skill_map = {
        name: entry.get("name", name)
        for name, entry in skills.get("entries", {}).items()
    }

    # 능력치/기타
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

    return skill_map, attr_map


def translate_name(name: str, skill_map, attr_map):
    """영문 이름을 기능/능력치 맵을 이용해 한글화"""
    if name in skill_map:
        return skill_map[name]
    if name in attr_map:
        return attr_map[name]
    return name


def translate_macro(macro_full: str, inner_args: str, label: str, skill_map, attr_map):
    """매크로 전체를 한글화: 인자와 라벨 둘 다 번역"""
    # 1) 인자 name:값 번역
    def repl_name(match):
        key = match.group(1)     # name:
        val = match.group(2).strip()
        new = translate_name(val, skill_map, attr_map)
        return f"{key}{new}"

    inner_args_new = re.sub(r"(name:)([^,}\]]+)", repl_name, inner_args)

    # 2) 라벨 { ... } 번역
    label = label.strip()
    label_new = translate_name(label, skill_map, attr_map)

    return f"@coc7.check[{inner_args_new}]{{{label_new}}}"


def replace_macros(html: str, skill_map, attr_map):
    """매크로 전체를 한글화"""

    def repl(match):
        full = match.group(1)
        args = match.group(2)
        label = match.group(3)
        return translate_macro(full, args, label, skill_map, attr_map)

    return MACRO_FULL_RE.sub(repl, html)


def main():
    if not ROLL_FILE.exists():
        raise SystemExit(f"입력 파일을 찾을 수 없습니다: {ROLL_FILE}")
    if not SKILLS_FILE.exists():
        raise SystemExit(f"기능 매핑 파일을 찾을 수 없습니다: {SKILLS_FILE}")
    if not KO_FILE.exists():
        raise SystemExit(f"ko.json 을 찾을 수 없습니다: {KO_FILE}")

    data = load_json(ROLL_FILE)
    skill_map, attr_map = build_maps()

    try:
        page = data["entries"]["Roll Requests"]["pages"][0]
    except Exception as e:
        raise SystemExit(f"Roll Requests 페이지 구조를 읽지 못했습니다: {e}")

    html = page["text"]["content"]

    # 매크로 전체 변환
    html = replace_macros(html, skill_map, attr_map)

    # JSON 반영
    data_out = data.copy()
    data_out["entries"]["Roll Requests"]["pages"][0]["text"]["content"] = html

    with OUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(data_out, f, ensure_ascii=False, indent=2)

    print(f"완료: {OUT_FILE.name} 에 저장했습니다.")


if __name__ == "__main__":
    main()
