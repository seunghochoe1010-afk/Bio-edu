"""엑셀 전공 과목 파싱 → major_course_catalog.json"""
import json
import re
from collections import Counter
from pathlib import Path

import pandas as pd

EXCEL_PATH = Path(r"c:\Users\user\Desktop\생물교육과\생물교육과 졸업소요 수강과목 내역(2026.03.06.).xlsx")
OUT_PATH = Path(__file__).parent / "major_course_catalog.json"

# 교과교육 8학점 (교직)
GYOGWA = {"생물교육론", "생물논리및논술교육", "생물교재연구및지도법"}

# 전공과목 15학점 (생물전공 필수) — 2024학번 시트 열4 하단
BIO_MAJOR = {
    "세포학", "유전학", "동물생리학", "미생물학", "생태학",
    "식물생리학", "곤충학", "면역학", "식물생리학",
}

# 4학년 심화 영역 (전공심화 21학점)
SIMHWA = {
    "유전체학", "환경생물학", "생물학사와생물교육",
    "미생물생리학", "과학학습평가", "이상심화학", "이상발생학",
    "분자생물학", "생물정보학", "생물다양성",
}

# 교직 실습·봉사 (열4, 학기 3-0 등 특수)
TEACHING_PRACTICE = {"교육봉사활동", "학교현장실습"}


def parse_semester(raw) -> tuple[int | None, int | None]:
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return None, None
    s = str(raw).strip().split(",")[0].strip()
    m = re.match(r"(\d)-(\d)", s)
    if not m:
        return None, None
    year, sem = int(m.group(1)), int(m.group(2))
    if sem == 0:
        return year, 1  # 3-0(봉사활동 등) → 1학기로 표기
    return year, sem


def parse_credit(raw) -> int | None:
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return None
    s = str(raw).strip().split(",")[0].strip()
    try:
        return int(float(s))
    except ValueError:
        return None


def expand_course_names(name: str) -> list[str]:
    name = str(name).strip()
    if "," not in name:
        return [name]
    parts = [p.strip() for p in name.split(",")]
    if len(parts) == 2 and parts[1].isdigit() and parts[0][-1].isdigit():
        prefix = parts[0][:-1]
        return [parts[0], f"{prefix}{parts[1]}"]
    return parts


def expand_list(raw, n: int) -> list[str]:
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return [""] * n
    items = [x.strip() for x in str(raw).split(",")]
    if len(items) >= n:
        return items[:n]
    return items + [items[-1]] * (n - len(items))


def is_header_or_note(text: str) -> bool:
    if not text or text == "nan":
        return True
    keys = (
        "학점)", "학점)", "영역", "이상", "과목 중", "※", "졸업", "교직이론",
        "교직소양", "교과교육(", "전공과목(", "교육실습(", "교육실습(4",
        "고시", "전선 교과목", "61학점", "기본이수", "교육과학기술부",
        "*", "교필", "교선", "역량", "균형", "기초",
    )
    return any(k in text for k in keys)


def classify_teaching(name: str) -> str:
    if name in GYOGWA:
        return "교직"
    return "교직"


def classify_major(name: str, year: int) -> str:
    if name in GYOGWA or name in TEACHING_PRACTICE:
        return "교직"
    if name in BIO_MAJOR:
        return "생물전공"
    if name in SIMHWA:
        return "심화"
    if year and year >= 4:
        return "심화"
    if "탐구실험" in name:
        return "전선"
    return "전선"


def parse_sheet(sheet_name: str = "2024학번") -> list[dict]:
    df = pd.read_excel(EXCEL_PATH, sheet_name=sheet_name, header=None)
    records: list[dict] = []
    seen: set[tuple] = set()
    in_bio_major_section = False

    def add(name, credit, year, sem, gubun):
        if not name or credit is None or year is None or sem is None:
            return
        name = name.strip()
        if is_header_or_note(name) or len(name) < 2 or name.isdigit():
            return
        key = (name, year, sem, gubun)
        if key in seen:
            return
        seen.add(key)
        records.append({
            "과목명": name,
            "학점": credit,
            "담당교수": "",
            "개설학년": year,
            "개설학기": sem,
            "구분": gubun,
        })

    for i in range(4, len(df)):
        row = df.iloc[i]

        # --- 열 4: 교직 / 생물전공 ---
        t_name = row[4]
        if pd.notna(t_name):
            t_name = str(t_name).strip()
            if "전공과목(15학점)" in t_name:
                in_bio_major_section = True
            elif is_header_or_note(t_name):
                if "전공과목" not in t_name:
                    in_bio_major_section = False
            else:
                yr, sem = parse_semester(row[5])
                cr = parse_credit(row[6])
                if in_bio_major_section or t_name in BIO_MAJOR:
                    gubun = "생물전공"
                else:
                    gubun = classify_teaching(t_name)
                add(t_name, cr, yr, sem, gubun)

        # --- 열 8: 전선 / 심화 / (일부 교직·생물) ---
        m_name = row[8]
        if pd.notna(m_name):
            m_name = str(m_name).strip()
            if is_header_or_note(m_name):
                continue
            names = expand_course_names(m_name)
            sems = expand_list(row[9], len(names))
            crs = expand_list(row[10], len(names))
            for nm, sem_s, cr_s in zip(names, sems, crs):
                if is_header_or_note(nm):
                    continue
                yr, sem = parse_semester(sem_s)
                cr = parse_credit(cr_s)
                gubun = classify_major(nm, yr or 1)
                add(nm, cr, yr, sem, gubun)

    return records


if __name__ == "__main__":
    data = parse_sheet("2024학번")
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("TOTAL", len(data))
    for k, v in sorted(Counter(r["구분"] for r in data).items()):
        print(f"{k}: {v}")
