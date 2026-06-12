# =============================================================================
# 생물교육과 교육과정 안내 및 졸업 요건 확인 챗봇 (24~26학번)
# =============================================================================

import json
import uuid
from datetime import datetime
from pathlib import Path

import streamlit as st
import pandas as pd
from collections import Counter

# 이 파일(app.py)이 있는 폴더 경로
APP_DIR = Path(__file__).parent
DATA_DIR = APP_DIR / "data"
LIBERAL_REVIEWS_PATH = DATA_DIR / "liberal_arts_reviews.json"
GRADUATION_TIPS_PATH = DATA_DIR / "graduation_tips.json"
# 학번별 개인 데이터를 저장하는 폴더
USER_DATA_DIR = DATA_DIR / "users"

# -----------------------------------------------------------------------------
# 1. 페이지 기본 설정
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="생물교육과 교육과정 및 졸업요건",
    page_icon="🍀",
    layout="wide",
)

# =============================================================================
# ★★★ 학과 데이터 입력 구역 — 나중에 이 부분만 수정하세요 ★★★
# =============================================================================

# -----------------------------------------------------------------------------
# [데이터 1] 전공 과목 목록 + 개설 학년·학기
#   - major_course_catalog.json 파일에서 불러옵니다.
#   - 출처: 생물교육과 졸업소요 수강과목 내역(2024학번 기준)
#   - 구분: 교직, 생물전공, 전선, 심화
#   - 갱신: parse_major.py 실행 또는 JSON 직접 수정
# -----------------------------------------------------------------------------

def load_major_course_catalog() -> pd.DataFrame:
  """전공 과목 JSON 파일을 읽어 DataFrame으로 반환합니다."""
  json_path = APP_DIR / "major_course_catalog.json"
  if json_path.exists():
    with open(json_path, encoding="utf-8") as f:
      data = json.load(f)
    return pd.DataFrame(data)
  return pd.DataFrame(
      columns=["과목명", "학점", "담당교수", "개설학년", "개설학기", "구분"]
  )


MAJOR_COURSE_CATALOG = load_major_course_catalog()


def save_major_course_catalog(df: pd.DataFrame) -> None:
  """전공 과목 DataFrame을 JSON 파일로 저장합니다."""
  json_path = APP_DIR / "major_course_catalog.json"
  records = df.fillna("").to_dict(orient="records")
  with open(json_path, "w", encoding="utf-8") as f:
    json.dump(records, f, ensure_ascii=False, indent=2)

# -----------------------------------------------------------------------------
# [데이터 2] 교양 과목 목록 (분야별 조회용)
#   - liberal_arts_catalog.json 파일에서 불러옵니다.
#   - 2025학년도 2학기 교양교과목 편성 목록 중 아래 7개 분야만 포함:
#     역량교양(창의·감성·공동체), 기초교양(기초SW),
#     균형교양(인간과사회·표현과소통·진로와창업)
#   - 목록 갱신 시 JSON 파일만 교체하면 됩니다.
# -----------------------------------------------------------------------------

def load_liberal_arts_catalog() -> pd.DataFrame:
  """교양 과목 JSON 파일을 읽어 DataFrame으로 반환합니다."""
  json_path = APP_DIR / "liberal_arts_catalog.json"
  if json_path.exists():
    with open(json_path, encoding="utf-8") as f:
      data = json.load(f)
    return pd.DataFrame(data)
  return pd.DataFrame(
      columns=["과목명", "학점", "분야", "대분류", "과목코드"]
  )


LIBERAL_ARTS_CATALOG = load_liberal_arts_catalog()

# =============================================================================
# 졸업 요건 · 교양 구조 · 교직 자격 (24~26학번)
# =============================================================================

GRADUATION_REQUIREMENTS = {
    "24학번": {
        "총학점": 150,
        "교양": {"최소": 32, "최대인정": 45, "일선대체최대": 12},
        "교직": 23,
        "생물전공": 23,
        "전선": 48,
        "심화": 0,
        "일선": 24,
    },
    "25학번": {
        "총학점": 150,
        "교양": {"최소": 32, "최대인정": 45, "일선대체최대": 12},
        "교직": 23,
        "생물전공": 23,
        "전선": 48,
        "심화": 0,
        "일선": 24,
    },
    "26학번": {
        "총학점": 150,
        "교양": {"최소": 32, "최대인정": 45, "일선대체최대": 12},
        "교직": 23,
        "생물전공": 23,
        "전선": 48,
        "심화": 0,
        "일선": 24,
    },
}

STUDENT_YEARS = list(GRADUATION_REQUIREMENTS.keys())

LIBERAL_ARTS_STRUCTURE = {
    "역량교양": ["창의", "감성", "공동체"],
    "기초교양": ["기초SW"],
    "균형교양": ["인간과사회", "표현과소통", "진로와창업"],
}

ALL_LIBERAL_ARTS_AREAS = [
    area for areas in LIBERAL_ARTS_STRUCTURE.values() for area in areas
]

TEACHING_LICENSE_REQUIREMENTS = {
    "교직적성검사": {"필수횟수": 2, "연간최대": 1, "설명": "1년에 1회 검사 가능"},
    "응급처치및심폐소생술": {"필수횟수": 2, "연간최대": 1, "설명": "1년에 1회 이수 가능"},
    "성인지교육": {"필수횟수": 4, "연간최대": 1, "설명": "1년에 1회 이수 (총 4회)"},
}

TEACHING_LICENSE_KEYS = list(TEACHING_LICENSE_REQUIREMENTS.keys())
RECORD_YEARS = list(range(2024, 2033))
RECORD_SEMESTERS = [1, 2]

FAQ_LIST = [
    "내 졸업 요건 확인해줘",
    "교양 분야별 이수 현황 알려줘",
    "교직 자격증 이수 조건 확인해줘",
    "선택한 학기 개설 과목 알려줘",
]

# 전필/교직필수/교직이론(8과목 중 6과목) 규칙
MAJOR_REQUIRED_COURSES = [
    "세포학",
    "유전학",
    "생물교육론",
    "생물논리및논술교육",
    "생물교재연구및지도법",
    "동물생리학",
    "미생물학",
    "생태학",
]

TEACHING_REQUIRED_COURSES = [
    "특수교육학개론",
    "학교폭력예방및학생의이해",
    "교직실무",
    "디지털교육",
    "교육봉사활동",
    "학교현장실습",
]

TEACHING_THEORY_POOL = [
    "교육학개론",
    "교육철학및교육사",
    "교육심리",
    "교육사회",
    "교육과정",
    "교육행정및교육경영",
    "교육방법및교육공학",
    "교육평가",
]

# 기초교양필수 과목 — 1학년 필수 이수, 교양 학점으로 인정
# 구분: 교필(교양필수), 교선필수(교양선택이지만 1학년 반드시 이수)
BASIC_LIBERAL_COURSE_NAMES = [
    "일반생물1", "일반생물2",
    "일반물리1", "일반물리2",
    "일반화학1", "일반화학2",
    "일반지구과학1", "일반지구과학2",
]

BASIC_LIBERAL_COURSES_INFO = [
    {"과목명": "일반생물1",     "학점": 3, "개설학년": 1, "개설학기": 1, "구분": "교필"},
    {"과목명": "일반생물2",     "학점": 3, "개설학년": 1, "개설학기": 2, "구분": "교필"},
    {"과목명": "일반물리1",     "학점": 3, "개설학년": 1, "개설학기": 1, "구분": "교선필수"},
    {"과목명": "일반물리2",     "학점": 3, "개설학년": 1, "개설학기": 2, "구분": "교선필수"},
    {"과목명": "일반화학1",     "학점": 3, "개설학년": 1, "개설학기": 1, "구분": "교선필수"},
    {"과목명": "일반화학2",     "학점": 3, "개설학년": 1, "개설학기": 2, "구분": "교선필수"},
    {"과목명": "일반지구과학1", "학점": 3, "개설학년": 1, "개설학기": 1, "구분": "교선필수"},
    {"과목명": "일반지구과학2", "학점": 3, "개설학년": 1, "개설학기": 2, "구분": "교선필수"},
]


def get_basic_liberal_df() -> pd.DataFrame:
    """기초교양필수 DataFrame. 전공 카탈로그에 있으면 그 학점을 사용하고, 없으면 기본값 3점을 씁니다."""
    rows = []
    for info in BASIC_LIBERAL_COURSES_INFO:
        name = info["과목명"]
        catalog_rows = MAJOR_COURSE_CATALOG[MAJOR_COURSE_CATALOG["과목명"] == name]
        if not catalog_rows.empty:
            r = catalog_rows.iloc[0]
            rows.append({
                "과목명": name,
                "학점": int(r.get("학점", info["학점"])),
                "개설학년": int(r.get("개설학년", info["개설학년"])),
                "개설학기": int(r.get("개설학기", info["개설학기"])),
                "구분": info["구분"],
            })
        else:
            rows.append(info.copy())
    return pd.DataFrame(rows)

PROFESSOR_EMOJI = {
    "최*욱교수님": "🧬",
    "정*영교수님": "👩‍🏫",
    "이*본교수님": "🥩",
    "이*현교수님": "🌲",
    "김*만교수님": "🧫",
}

# 사이드바 메뉴 목록 (첫 번째가 홈)
MENU_OPTIONS = [
    "👨‍🏫 교수님별 강의 조회",
    "📚 교양 과목 안내",
    "💡 졸업팁",
    "🧮 졸업요건 확인",
]


# =============================================================================
# 세션 상태
# =============================================================================

def init_session_state() -> None:
  DATA_DIR.mkdir(parents=True, exist_ok=True)
  if "messages" not in st.session_state:
    st.session_state.messages = []
  if "pending_faq" not in st.session_state:
    st.session_state.pending_faq = None
  if "active_menu" not in st.session_state:
    st.session_state.active_menu = MENU_OPTIONS[0]
  if "show_home" not in st.session_state:
    st.session_state.show_home = True
  # 예전 메뉴 이름 → 새 메뉴로 자동 전환
  if st.session_state.active_menu == "📅 개설 강의 조회":
    st.session_state.active_menu = "👨‍🏫 교수님별 강의 조회"
  if st.session_state.active_menu == "📅 강의 조회":
    st.session_state.active_menu = "👨‍🏫 교수님별 강의 조회"
  if st.session_state.active_menu == "🧮 학점 · 졸업 계산":
    st.session_state.active_menu = "🧮 졸업요건 확인"
  if st.session_state.active_menu not in MENU_OPTIONS:
    st.session_state.active_menu = MENU_OPTIONS[0]
  if "selected_교양_과목" not in st.session_state:
    st.session_state.selected_교양_과목 = None
  if "선택_학번" not in st.session_state:
    st.session_state.선택_학번 = STUDENT_YEARS[0]
  if "inp_교직" not in st.session_state:
    st.session_state.inp_교직 = 0
  if "inp_생물전공" not in st.session_state:
    st.session_state.inp_생물전공 = 0
  if "inp_전선" not in st.session_state:
    st.session_state.inp_전선 = 0
  if "inp_심화" not in st.session_state:
    st.session_state.inp_심화 = 0
  if "inp_일선" not in st.session_state:
    st.session_state.inp_일선 = 0
  if "교양_과목" not in st.session_state:
    st.session_state.교양_과목 = {area: [] for area in ALL_LIBERAL_ARTS_AREAS}
  if "교직_이수" not in st.session_state:
    st.session_state.교직_이수 = {key: [] for key in TEACHING_LICENSE_KEYS}
  if "조회_학년" not in st.session_state:
    st.session_state.조회_학년 = 1
  if "조회_학기" not in st.session_state:
    st.session_state.조회_학기 = 1
  if "selected_required_courses" not in st.session_state:
    st.session_state.selected_required_courses = []
  if "selected_elective_courses" not in st.session_state:
    st.session_state.selected_elective_courses = []
  if "student_id" not in st.session_state:
    st.session_state.student_id = ""
  if "user_logged_in" not in st.session_state:
    st.session_state.user_logged_in = False
  # 과목별 이수 여부 체크 상태 {과목명: True/False}
  if "course_checks" not in st.session_state:
    st.session_state.course_checks = {}
  if "inp_기초교양" not in st.session_state:
    st.session_state.inp_기초교양 = 0


init_session_state()


# =============================================================================
# JSON 저장소 (교양 후기 · 졸업팁 게시판)
# =============================================================================

def load_json_data(path: Path, default):
  """JSON 파일을 읽습니다. 없으면 기본값을 반환합니다."""
  if path.exists():
    with open(path, encoding="utf-8") as f:
      return json.load(f)
  return default


def save_json_data(path: Path, data) -> None:
  """JSON 파일로 저장합니다."""
  path.parent.mkdir(parents=True, exist_ok=True)
  with open(path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)


# =============================================================================
# 학번별 개인 데이터 저장 (졸업요건 입력 내용 유지)
# =============================================================================

def load_user_data(student_id: str) -> dict:
  """학번으로 저장된 개인 데이터를 불러옵니다."""
  path = USER_DATA_DIR / f"{student_id}.json"
  return load_json_data(path, {})


def save_user_data(student_id: str, data: dict) -> None:
  """학번 기준으로 개인 데이터를 저장합니다."""
  USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
  path = USER_DATA_DIR / f"{student_id}.json"
  save_json_data(path, data)


def get_current_user_save_data() -> dict:
  """현재 세션 상태에서 저장할 졸업요건 데이터를 추출합니다."""
  return {
    "선택_학번": st.session_state.get("선택_학번", STUDENT_YEARS[0]),
    "course_checks": st.session_state.get("course_checks", {}),
    "교양_과목": st.session_state.get("교양_과목", {}),
    "교직_이수": st.session_state.get("교직_이수", {}),
    "inp_일선": st.session_state.get("inp_일선", 0),
  }


def get_course_prefix(name: str) -> str:
  """과목명으로 체크리스트 위젯 prefix를 반환합니다."""
  if name in MAJOR_REQUIRED_COURSES:
    return "전필"
  if name in TEACHING_REQUIRED_COURSES:
    return "교직필수"
  if name in TEACHING_THEORY_POOL:
    return "교직이론"
  if name in BASIC_LIBERAL_COURSE_NAMES:
    return "기초교양"
  return "전선"


def get_widget_checked_credits(courses_df: pd.DataFrame, prefix: str) -> int:
  """Streamlit 위젯 키에서 직접 체크 상태를 읽어 학점 합계를 반환합니다.
  (course_checks 딕셔너리 대신 위젯 키를 사용하므로 렌더링 순서 버그가 없습니다.)"""
  if courses_df.empty:
    return 0
  total = 0
  for _, row in courses_df.iterrows():
    name = str(row["과목명"])
    if st.session_state.get(f"chk_{prefix}_{name}", False):
      total += int(row.get("학점", 0))
  return total


def apply_user_data(data: dict) -> None:
  """저장된 데이터를 세션 상태에 적용합니다."""
  if "선택_학번" in data and data["선택_학번"] in STUDENT_YEARS:
    st.session_state.선택_학번 = data["선택_학번"]
  if "course_checks" in data:
    st.session_state.course_checks = data["course_checks"]
    # 위젯 키도 함께 설정해야 체크박스가 올바른 상태로 렌더링됩니다
    for name, val in data["course_checks"].items():
      prefix = get_course_prefix(name)
      st.session_state[f"chk_{prefix}_{name}"] = bool(val)
  if "교양_과목" in data:
    merged = {area: [] for area in ALL_LIBERAL_ARTS_AREAS}
    merged.update(data["교양_과목"])
    st.session_state.교양_과목 = merged
  if "교직_이수" in data:
    merged = {key: [] for key in TEACHING_LICENSE_KEYS}
    merged.update(data["교직_이수"])
    st.session_state.교직_이수 = merged
  if "inp_일선" in data:
    st.session_state.inp_일선 = data["inp_일선"]


def course_review_key(과목명: str, 과목코드: str = "") -> str:
  """후기 저장용 고유 키 (과목코드 우선)."""
  return 과목코드.strip() if 과목코드 and str(과목코드) != "nan" else 과목명.strip()


def get_course_reviews(key: str) -> list:
  all_reviews = load_json_data(LIBERAL_REVIEWS_PATH, {})
  return all_reviews.get(key, [])


def add_course_review(key: str, 별점: int, 작성자: str, 내용: str) -> None:
  all_reviews = load_json_data(LIBERAL_REVIEWS_PATH, {})
  if key not in all_reviews:
    all_reviews[key] = []
  all_reviews[key].append({
      "별점": 별점,
      "작성자": 작성자.strip() or "익명",
      "내용": 내용.strip(),
      "작성일": datetime.now().strftime("%Y-%m-%d %H:%M"),
  })
  save_json_data(LIBERAL_REVIEWS_PATH, all_reviews)


def average_rating(reviews: list) -> float | None:
  if not reviews:
    return None
  return sum(r["별점"] for r in reviews) / len(reviews)


def stars_text(rating: float | None) -> str:
  if rating is None:
    return "아직 평가 없음"
  full = int(round(rating))
  return "⭐" * full + "☆" * (5 - full) + f" **{rating:.1f}** / 5"


def get_graduation_tips() -> list:
  return load_json_data(GRADUATION_TIPS_PATH, [])


def add_graduation_tip(제목: str, 작성자: str, 학번: str, 내용: str) -> None:
  tips = get_graduation_tips()
  tips.insert(0, {
      "id": str(uuid.uuid4())[:8],
      "제목": 제목.strip(),
      "작성자": 작성자.strip() or "익명",
      "학번": 학번.strip(),
      "내용": 내용.strip(),
      "작성일": datetime.now().strftime("%Y-%m-%d %H:%M"),
  })
  save_json_data(GRADUATION_TIPS_PATH, tips)


# =============================================================================
# 데이터 조회 · 분석 함수
# =============================================================================

def get_courses_by_semester(학년: int, 학기: int) -> pd.DataFrame:
  """개설 학년·학기에 해당하는 전공 과목을 필터링합니다."""
  if MAJOR_COURSE_CATALOG.empty:
    return MAJOR_COURSE_CATALOG
  return MAJOR_COURSE_CATALOG[
      (MAJOR_COURSE_CATALOG["개설학년"] == 학년)
      & (MAJOR_COURSE_CATALOG["개설학기"] == 학기)
  ].sort_values(["구분", "과목명"])


def get_courses_by_professor() -> dict:
  """교수님별로 개설 강의 목록을 묶어 반환합니다."""
  if MAJOR_COURSE_CATALOG.empty:
    return {}
  result = {}
  for professor in sorted(MAJOR_COURSE_CATALOG["담당교수"].fillna("").unique()):
    professor = str(professor)
    courses = MAJOR_COURSE_CATALOG[
        MAJOR_COURSE_CATALOG["담당교수"] == professor
    ].sort_values(["개설학년", "개설학기", "구분", "과목명"])
    result[professor] = courses
  return result


def get_liberal_arts_by_category() -> dict:
  """대분류·분야별 교양 과목 목록을 묶어 반환합니다."""
  result = {}
  for category, areas in LIBERAL_ARTS_STRUCTURE.items():
    result[category] = {}
    for area in areas:
      if LIBERAL_ARTS_CATALOG.empty:
        result[category][area] = pd.DataFrame()
      else:
        result[category][area] = LIBERAL_ARTS_CATALOG[
            LIBERAL_ARTS_CATALOG["분야"] == area
        ].sort_values("과목명")
  return result


def sum_liberal_arts_credits(교양_과목: dict) -> int:
  total = 0
  for courses in 교양_과목.values():
    for course in courses:
      total += course["학점"]
  return total


def calc_effective_credits(학번: str, credits: dict) -> dict:
  기준 = GRADUATION_REQUIREMENTS[학번]
  교양 = credits["교양"]
  일선 = credits["일선"]
  교양_최소 = 기준["교양"]["최소"]
  교양_최대 = 기준["교양"]["최대인정"]
  일선_대체_한도 = 기준["교양"]["일선대체최대"]
  교양_인정 = min(교양, 교양_최대)
  교양_초과 = max(0, 교양 - 교양_최소)
  일선_교양대체 = min(교양_초과, 일선_대체_한도)
  일선_유효 = 일선 + 일선_교양대체
  총학점_인정 = (
      교양_인정 + credits["교직"] + credits["생물전공"]
      + credits["전선"] + 일선_유효   # 심화는 전선에 통합, 일선은 교양대체 포함
  )
  return {
      "교양_인정": 교양_인정,
      "교양_초과": 교양_초과,
      "일선_교양대체": 일선_교양대체,
      "일선_유효": 일선_유효,
      "총학점_인정": 총학점_인정,
  }


def _status_line(영역: str, 현재: int, 기준값: int, 유효: int | None = None) -> str:
  비교값 = 유효 if 유효 is not None else 현재
  부족 = 기준값 - 비교값
  if 부족 > 0:
    if 유효 is not None and 유효 != 현재:
      return (
          f"- **{영역}**: 이수 {현재}점 + 교양대체 {유효 - 현재}점 "
          f"= 유효 {유효}점 / 기준 {기준값}점 → **{부족}점 부족**"
      )
    return f"- **{영역}**: {현재}점 / 기준 {기준값}점 → **{부족}점 부족**"
  if 유효 is not None and 유효 != 현재:
    return (
        f"- **{영역}**: 이수 {현재}점 + 교양대체 {유효 - 현재}점 "
        f"= 유효 {유효}점 / 기준 {기준값}점 → ✅ **요건 충족 완료**"
    )
  return f"- **{영역}**: {현재}점 / 기준 {기준값}점 → ✅ **요건 충족 완료**"


def analyze_liberal_arts_areas(교양_과목: dict) -> str:
  줄 = ["\n---\n📚 **교양 분야별 이수 현황**\n"]
  미이수_분야 = []
  for category, areas in LIBERAL_ARTS_STRUCTURE.items():
    줄.append(f"**{category}**")
    for area in areas:
      courses = 교양_과목.get(area, [])
      if courses:
        과목_목록 = ", ".join(f"{c['과목명']}({c['학점']}점)" for c in courses)
        줄.append(f"- **{area}**: ✅ {과목_목록}")
      else:
        줄.append(f"- **{area}**: ❌ **미이수** — 해당 분야 과목 1개 이상 필요")
        미이수_분야.append(area)
    줄.append("")
  if 미이수_분야:
    줄.append(f"⚠️ 아직 채워야 할 분야: **{', '.join(미이수_분야)}**")
  else:
    줄.append("✅ **모든 교양 분야 요건을 충족했습니다!**")
  return "\n".join(줄)


def analyze_teaching_license(교직_이수: dict) -> str:
  줄 = ["\n---\n🪪 **교직 자격증 필수 이수 현황**\n"]
  전체_충족 = True
  for 항목, 기준 in TEACHING_LICENSE_REQUIREMENTS.items():
    records = 교직_이수.get(항목, [])
    이수_횟수 = len(records)
    필수 = 기준["필수횟수"]
    줄.append(f"**{항목}** ({기준['설명']})")
    if records:
      for r in sorted(records, key=lambda x: (x["년도"], x["학기"])):
        줄.append(f"  - {r['년도']}년 {r['학기']}학기 이수")
    else:
      줄.append("  - (이수 기록 없음)")
    if 이수_횟수 >= 필수:
      줄.append(f"  → ✅ **{이수_횟수}/{필수}회 충족**")
    else:
      줄.append(f"  → ❌ **{이수_횟수}/{필수}회** — **{필수 - 이수_횟수}회** 더 필요")
      전체_충족 = False
    if 기준["연간최대"] == 1:
      년도_카운트 = Counter(r["년도"] for r in records)
      중복_년도 = [y for y, cnt in 년도_카운트.items() if cnt > 1]
      if 중복_년도:
        줄.append(
            f"  → ⚠️ **{', '.join(str(y) for y in 중복_년도)}년**에 "
            f"2회 이상 기록됨 (연 1회 제한 확인 필요)"
        )
        전체_충족 = False
    줄.append("")
  if 전체_충족:
    줄.append("✅ **교직 자격증 필수 이수 요건을 모두 충족했습니다!**")
  else:
    줄.append("⚠️ 위 항목을 확인하고 부족한 이수를 완료해 주세요.")
  return "\n".join(줄)


def analyze_graduation(학번: str, credits: dict, 교양_과목: dict, 교직_이수: dict) -> str:
  기준 = GRADUATION_REQUIREMENTS[학번]
  유효 = calc_effective_credits(학번, credits)
  결과_줄 = [f"📋 **{학번} 졸업 요건 종합 분석**\n", "### 📊 학점 현황\n"]
  총_부족 = 기준["총학점"] - 유효["총학점_인정"]
  if 총_부족 > 0:
    결과_줄.append(
        f"- **총 학점(인정)**: {유효['총학점_인정']}점 / 기준 {기준['총학점']}점 "
        f"→ **{총_부족}점 부족**"
    )
  else:
    결과_줄.append(
        f"- **총 학점(인정)**: {유효['총학점_인정']}점 / 기준 {기준['총학점']}점 "
        f"→ ✅ **충족 완료**"
    )
  교양 = credits["교양"]
  교양_최소 = 기준["교양"]["최소"]
  교양_최대 = 기준["교양"]["최대인정"]
  if 교양 < 교양_최소:
    결과_줄.append(
        f"- **교양**: {교양}점 / 최소 {교양_최소}점 → **{교양_최소 - 교양}점 부족**"
    )
  else:
    결과_줄.append(
        f"- **교양**: {교양}점 / 최소 {교양_최소}점 → ✅ **최소 요건 충족**"
    )
  if 교양 > 교양_최대:
    결과_줄.append(f"  - ℹ️ 교양 {교양}점 중 **{교양_최대}점까지만** 총학점에 인정")
  if 유효["일선_교양대체"] > 0:
    결과_줄.append(f"  - ℹ️ 교양 초과분 **{유효['일선_교양대체']}점**이 일선에 대체됨")
  for 영역 in ["교직", "생물전공", "전선", "심화"]:
    결과_줄.append(_status_line(영역, credits[영역], 기준[영역]))
  결과_줄.append(
      _status_line("일선", credits["일선"], 기준["일선"], 유효=유효["일선_유효"])
  )
  전필_합 = credits["교직"] + credits["생물전공"]
  전필_기준 = 기준["교직"] + 기준["생물전공"]
  결과_줄.append(f"\n📌 **전공필수 합계**: {전필_합}점 / 기준 {전필_기준}점")
  결과_줄.append(analyze_liberal_arts_areas(교양_과목))
  결과_줄.append(analyze_teaching_license(교직_이수))
  return "\n".join(결과_줄)


def get_semester_courses_text(학년: int, 학기: int) -> str:
  courses = get_courses_by_semester(학년, 학기)
  if courses.empty:
    return (
        f"📅 **{학년}학년 {학기}학기** 개설 과목이 등록되어 있지 않습니다.\n\n"
        f"`app.py` 상단 **MAJOR_COURSE_CATALOG** 에 과목을 추가해 주세요."
    )
  줄 = [f"📅 **{학년}학년 {학기}학기** 개설 전공 과목\n"]
  for 구분 in courses["구분"].unique():
    구분_과목 = courses[courses["구분"] == 구분]
    줄.append(f"\n**{구분}**")
    for _, row in 구분_과목.iterrows():
      줄.append(
          f"- **{row['과목명']}** ({row['학점']}학점) · {row['담당교수']}"
      )
  return "\n".join(줄)


def generate_bot_response(
    user_message: str,
    학번: str,
    credits: dict,
    교양_과목: dict,
    교직_이수: dict,
    조회_학년: int,
    조회_학기: int,
) -> str:
  원문 = user_message.strip()
  if any(k in 원문 for k in ["졸업", "요건", "학점 확인", "부족", "종합"]):
    return analyze_graduation(학번, credits, 교양_과목, 교직_이수)
  if any(k in 원문 for k in ["교양 분야", "역량", "균형", "기초SW", "창의", "감성", "공동체"]):
    return analyze_liberal_arts_areas(교양_과목)
  if any(k in 원문 for k in ["교직 자격", "적성검사", "응급처치", "심폐소생", "성인지"]):
    return analyze_teaching_license(교직_이수)
  if any(k in 원문 for k in ["개설", "열리", "과목", "학기"]):
    return get_semester_courses_text(조회_학년, 조회_학기)
  if "교양" in 원문:
    return analyze_liberal_arts_areas(교양_과목)
  if any(k in 원문 for k in ["안녕", "hello", "hi"]):
    return (
        "안녕하세요! 🎓 **생물교육과 교육과정 및 졸업요건** 챗봇입니다.\n\n"
        "**교수님별 강의 조회**, **교양 과목 안내**, **졸업요건 확인** 메뉴를 이용해 보세요!"
    )
  return (
      "질문을 이해하지 못했어요. 😅\n\n"
      "예시:\n"
      '- "내 졸업 요건 확인해줘"\n'
      '- "선택한 학기 개설 과목 알려줘"\n'
      '- "교양 분야별 이수 현황 알려줘"\n\n'
      "또는 FAQ 버튼을 눌러 주세요."
  )


def add_message(role: str, content: str) -> None:
  st.session_state.messages.append({"role": role, "content": content})


def get_user_credits() -> dict:
  """학점 계산 메뉴에 입력한 값을 챗봇에서도 사용할 수 있게 반환합니다.
  교양 = 역량/균형/기초SW 교양 + 기초교양필수(일반생물/물리/화학/지구과학) 합계."""
  return {
      "교양": (
          sum_liberal_arts_credits(st.session_state.교양_과목)
          + st.session_state.get("inp_기초교양", 0)
      ),
      "교직": st.session_state.inp_교직,
      "생물전공": st.session_state.inp_생물전공,
      "전선": st.session_state.inp_전선,
      "심화": st.session_state.inp_심화,
      "일선": st.session_state.inp_일선,
  }


def render_chatbot() -> None:
  """홈 화면 챗봇 UI (FAQ 버튼 + 대화창)."""
  user_credits = get_user_credits()
  학번 = st.session_state.선택_학번

  st.subheader("💬 자주 묻는 질문")
  faq_cols = st.columns(len(FAQ_LIST))
  for i, faq_question in enumerate(FAQ_LIST):
    if faq_cols[i].button(faq_question, key=f"faq_{i}", use_container_width=True):
      st.session_state.pending_faq = faq_question
      st.rerun()

  st.caption(
      "졸업 요건·교양·교직 질문은 **졸업요건 확인** 메뉴에 입력한 데이터를 바탕으로 답합니다."
  )

  if st.session_state.pending_faq:
    faq_q = st.session_state.pending_faq
    faq_a = generate_bot_response(
        faq_q, 학번, user_credits,
        st.session_state.교양_과목, st.session_state.교직_이수,
        st.session_state.조회_학년, st.session_state.조회_학기,
    )
    add_message("user", faq_q)
    add_message("assistant", faq_a)
    st.session_state.pending_faq = None

  for message in st.session_state.messages:
    with st.chat_message(message["role"]):
      st.markdown(message["content"])

  if user_input := st.chat_input("질문을 입력하세요... (예: 내 졸업 요건 확인해줘)"):
    add_message("user", user_input)
    bot_reply = generate_bot_response(
        user_input, 학번, user_credits,
        st.session_state.교양_과목, st.session_state.교직_이수,
        st.session_state.조회_학년, st.session_state.조회_학기,
    )
    add_message("assistant", bot_reply)
    st.rerun()


# =============================================================================
# UI 컴포넌트
# =============================================================================

def render_graduation_dashboard(
    학번: str,
    전필_점: int,
    교직_점: int,
    전선_점: int,
    교양_점: int,     # 역량교양+기초SW+균형교양 학점
    기초교양_점: int, # 일반생물/물리/화학/지구과학 학점
    일선_점: int,
) -> None:
  """상단 진행률 대시보드 — 졸업요건 충족 현황을 한눈에 표시합니다."""
  req = GRADUATION_REQUIREMENTS[학번]

  교양_총 = 교양_점 + 기초교양_점
  교양_최소 = req["교양"]["최소"]        # 32
  교양_최대 = req["교양"]["최대인정"]    # 45
  일선_대체_한도 = req["교양"]["일선대체최대"]  # 12
  교양_인정 = min(교양_총, 교양_최대)
  교양_초과 = max(0, 교양_총 - 교양_최소)
  일선_교양대체 = min(교양_초과, 일선_대체_한도)
  일선_유효 = 일선_점 + 일선_교양대체
  일선_목표 = req["일선"]               # 24

  def _bar(label: str, current: int, target: int) -> None:
    pct = min(current / target, 1.0) if target > 0 else 0.0
    icon = "✅" if current >= target else ("⚠️" if pct >= 0.5 else "❌")
    st.markdown(f"**{label}** {icon}&nbsp; {current} / {target}점")
    st.progress(pct)

  col1, col2, col3, col4, col5 = st.columns(5)
  with col1:
    _bar("🔬 전공필수(생물)", 전필_점, req["생물전공"])
  with col2:
    _bar("📋 교직", 교직_점, req["교직"])
  with col3:
    # 전선 27점 + 심화 21점 통합 표시
    전선_목표 = req["전선"]   # 48 (심화 포함)
    _bar("📖 전공선택·심화", 전선_점, 전선_목표)
  with col4:
    교양_icon = "✅" if 교양_총 >= 교양_최소 else ("⚠️" if 교양_총 >= 교양_최소 * 0.5 else "❌")
    st.markdown(f"**🌱 교양** {교양_icon}&nbsp; {교양_총} / {교양_최소}점")
    st.progress(min(교양_총 / 교양_최소, 1.0) if 교양_최소 > 0 else 0.0)
    if 일선_교양대체 > 0:
      st.caption(f"→ 교양 초과 {일선_교양대체}점 일선 자동 인정")
  with col5:
    _bar("📝 일선(자동포함)", 일선_유효, 일선_목표)
    if 일선_교양대체 > 0:
      st.caption(f"= {일선_점}점 + 교양대체 {일선_교양대체}점")

  총계 = 교양_인정 + 전필_점 + 교직_점 + 전선_점 + 일선_유효
  총기준 = req["총학점"]
  총icon = "✅ 졸업 가능" if 총계 >= 총기준 else f"❌ {총기준 - 총계}점 부족"
  st.markdown(f"#### 총 이수학점 {총icon} — **{총계} / {총기준}점**")
  st.progress(min(총계 / 총기준, 1.0))


def render_course_checklist(courses_df: pd.DataFrame, prefix: str) -> None:
  """과목 체크리스트 그리드를 렌더링합니다.
  학점 합계는 get_widget_checked_credits()로 렌더링 전에 읽어야 정확합니다."""
  if courses_df.empty:
    st.info("등록된 과목 데이터가 없습니다.")
    return

  sorted_df = courses_df.sort_values(["개설학년", "개설학기", "과목명"]).reset_index(drop=True)
  cols = st.columns(3)
  for i, row in sorted_df.iterrows():
    name = str(row["과목명"])
    credit = int(row.get("학점", 0))
    yr = row.get("개설학년", "")
    sem = row.get("개설학기", "")
    semester_hint = f"{yr}-{sem}학기" if yr and sem else ""

    with cols[i % 3]:
      checked = st.checkbox(
          f"{name} ({credit}점)",
          key=f"chk_{prefix}_{name}",   # Streamlit이 위젯 상태 관리
          help=semester_hint or None,
      )
      # course_checks 딕셔너리도 동기화 (저장 기능에 사용)
      st.session_state.course_checks[name] = checked


def render_liberal_arts_course_input(area: str) -> None:
  """학점 계산 메뉴: 본인이 이수한 교양 과목 등록."""
  st.markdown(f"**{area}**")
  courses = st.session_state.교양_과목[area]

  # 카탈로그에 등록된 과목이 있으면 선택해서 추가 가능
  if not LIBERAL_ARTS_CATALOG.empty:
    catalog_in_area = LIBERAL_ARTS_CATALOG[LIBERAL_ARTS_CATALOG["분야"] == area]
    if not catalog_in_area.empty:
      catalog_options = ["직접 입력"] + catalog_in_area["과목명"].tolist()
      selected = st.selectbox(
          f"{area} 과목 선택",
          catalog_options,
          key=f"catalog_{area}",
          label_visibility="collapsed",
      )
      if selected != "직접 입력":
        row = catalog_in_area[catalog_in_area["과목명"] == selected].iloc[0]
        if st.button("목록에서 추가", key=f"catalog_add_{area}"):
          courses.append({"과목명": row["과목명"], "학점": int(row["학점"])})
          st.rerun()

  if courses:
    for i, course in enumerate(courses):
      col1, col2 = st.columns([4, 1])
      col1.caption(f"· {course['과목명']} ({course['학점']}점)")
      if col2.button("삭제", key=f"del_{area}_{i}"):
        courses.pop(i)
        st.rerun()

  col_name, col_credit, col_btn = st.columns([3, 1, 1])
  with col_name:
    new_name = st.text_input(
        "과목명", key=f"name_{area}",
        placeholder="과목명 직접 입력", label_visibility="collapsed",
    )
  with col_credit:
    new_credit = st.number_input(
        "학점", 1, 6, 3, key=f"credit_{area}", label_visibility="collapsed",
    )
  with col_btn:
    st.write("")
    if st.button("추가", key=f"add_{area}"):
      if new_name.strip():
        courses.append({"과목명": new_name.strip(), "학점": new_credit})
        st.rerun()
      else:
        st.warning("과목명을 입력하세요.")


def render_teaching_license_input(항목: str) -> None:
  기준 = TEACHING_LICENSE_REQUIREMENTS[항목]
  st.markdown(f"**{항목}**")
  st.caption(f"필수 {기준['필수횟수']}회 · {기준['설명']}")
  records = st.session_state.교직_이수[항목]
  if records:
    for i, record in enumerate(records):
      col1, col2 = st.columns([4, 1])
      col1.caption(f"· {record['년도']}년 {record['학기']}학기")
      if col2.button("삭제", key=f"del_{항목}_{i}"):
        records.pop(i)
        st.rerun()
  col_y, col_s, col_btn = st.columns([2, 2, 1])
  with col_y:
    new_year = st.selectbox(
        "년도", RECORD_YEARS, key=f"year_{항목}", label_visibility="collapsed",
    )
  with col_s:
    new_sem = st.selectbox(
        "학기", RECORD_SEMESTERS, key=f"sem_{항목}", label_visibility="collapsed",
    )
  with col_btn:
    st.write("")
    if st.button("추가", key=f"add_{항목}"):
      records.append({"년도": new_year, "학기": new_sem})
      st.rerun()


# =============================================================================
# 페이지: 홈
# =============================================================================

def page_home() -> None:
  st.title("🎓 생물교육과 교육과정 및 졸업요건")
  st.markdown(
      "**24~26학번** 교육과정 기준 | 궁금한 점을 챗봇에게 물어보거나 아래 메뉴를 이용하세요."
  )

  col1, col2, col3 = st.columns(3)
  with col1:
    if st.button("👨‍🏫 교수님별 강의", use_container_width=True):
      st.session_state.active_menu = "👨‍🏫 교수님별 강의 조회"
      st.session_state.show_home = False
      st.rerun()
  with col2:
    if st.button("📚 교양 과목", use_container_width=True):
      st.session_state.active_menu = "📚 교양 과목 안내"
      st.session_state.show_home = False
      st.rerun()
  with col3:
    if st.button("💡 졸업팁 게시판", use_container_width=True):
      st.session_state.active_menu = "💡 졸업팁"
      st.session_state.show_home = False
      st.rerun()
  if st.button("🧮 졸업요건 확인", use_container_width=True):
    st.session_state.active_menu = "🧮 졸업요건 확인"
    st.session_state.show_home = False
    st.rerun()

  st.divider()
  render_chatbot()


# =============================================================================
# 페이지: 강의 조회 (학년·학기)
# =============================================================================

def page_semester_courses() -> None:
  st.title("📅 강의 조회")
  st.markdown("학년·학기별로 개설되는 전공 과목을 확인하고 4년 수강 계획을 세워 보세요.")
  st.caption(f"전공 과목 **{len(MAJOR_COURSE_CATALOG)}개**")

  col1, col2 = st.columns(2)
  with col1:
    조회_학년 = st.selectbox(
        "몇 학년 과정을 볼까요?",
        [1, 2, 3, 4],
        index=st.session_state.조회_학년 - 1,
        key="page_조회_학년",
    )
  with col2:
    조회_학기 = st.selectbox(
        "몇 학기?",
        [1, 2],
        index=st.session_state.조회_학기 - 1,
        key="page_조회_학기",
    )
  st.session_state.조회_학년 = 조회_학년
  st.session_state.조회_학기 = 조회_학기

  st.subheader(f"🗓️ {조회_학년}학년 {조회_학기}학기 개설 과목")
  semester_courses = get_courses_by_semester(조회_학년, 조회_학기)
  if semester_courses.empty:
    st.info("등록된 과목이 없습니다.")
  else:
    show_cols = [c for c in ["과목명", "학점", "구분", "담당교수", "개설학년", "개설학기"]
                 if c in semester_courses.columns]
    st.dataframe(semester_courses[show_cols], use_container_width=True, hide_index=True)

  st.divider()
  st.subheader("📋 4년 전공 과목 로드맵")
  if MAJOR_COURSE_CATALOG.empty:
    st.caption("과목 데이터를 추가하면 학년·학기별 표가 표시됩니다.")
  else:
    for 학년 in [1, 2, 3, 4]:
      st.markdown(f"**{학년}학년**")
      c1, c2 = st.columns(2)
      with c1:
        st.markdown("*1학기*")
        df = get_courses_by_semester(학년, 1)
        if df.empty:
          st.caption("(개설 과목 없음)")
        else:
          for _, row in df.iterrows():
            st.caption(f"· [{row['구분']}] {row['과목명']} ({row['학점']}점) — {row['담당교수']}")
      with c2:
        st.markdown("*2학기*")
        df = get_courses_by_semester(학년, 2)
        if df.empty:
          st.caption("(개설 과목 없음)")
        else:
          for _, row in df.iterrows():
            prof = row.get("담당교수", "") or ""
            st.caption(f"· [{row['구분']}] {row['과목명']} ({row['학점']}점)" + (f" — {prof}" if prof else ""))


# =============================================================================
# 페이지: 교수님별 강의 조회
# =============================================================================

def page_professor_courses() -> None:
  st.title("👨‍🏫 교수님별 강의 조회")
  st.markdown("교수님별 개설 강의를 확인합니다. 학년-학기 순으로 정렬되어 있습니다.")
  st.caption("구분은 요청 기준에 맞게 전필/전선으로 표시됩니다.")

  professor_courses = get_courses_by_professor()
  if not professor_courses:
    st.info("등록된 교수·강의 정보가 없습니다.")
    return

  교수_목록 = sorted([p for p in professor_courses.keys() if p and str(p).strip()])
  if not 교수_목록:
    st.info("담당교수 정보가 없습니다. `major_course_catalog.json`에서 교수명을 입력해 주세요.")
    return

  prof_labels = [f"{PROFESSOR_EMOJI.get(p, '👨‍🏫')} {p}" for p in 교수_목록]
  label_to_prof = {f"{PROFESSOR_EMOJI.get(p, '👨‍🏫')} {p}": p for p in 교수_목록}
  선택_라벨 = st.selectbox("교수님 선택", prof_labels, key="prof_select")
  선택_교수 = label_to_prof[선택_라벨]

  courses = professor_courses[선택_교수].copy()
  courses["학년-학기"] = courses["개설학년"].astype(str) + "-" + courses["개설학기"].astype(str)
  courses = courses.sort_values(["개설학년", "개설학기", "구분", "과목명"])

  emoji = PROFESSOR_EMOJI.get(선택_교수, "👨‍🏫")
  st.subheader(f"{emoji}{선택_교수} 개설 강의 ({len(courses)}과목)")
  st.dataframe(
      courses[["학년-학기", "구분", "과목명", "학점"]],
      use_container_width=True,
      hide_index=True,
  )

  st.divider()
  st.subheader("전체 교수님 목록")
  for professor in 교수_목록:
    c = professor_courses[professor].copy()
    c["학년-학기"] = c["개설학년"].astype(str) + "-" + c["개설학기"].astype(str)
    c = c.sort_values(["개설학년", "개설학기", "구분", "과목명"])
    emoji = PROFESSOR_EMOJI.get(professor, "👨‍🏫")
    with st.expander(f"{emoji}{professor} ({len(c)}과목)"):
      st.dataframe(
          c[["학년-학기", "구분", "과목명", "학점"]],
          use_container_width=True,
          hide_index=True,
      )


# =============================================================================
# 페이지: 교양 과목 안내 + 후기
# =============================================================================

def render_liberal_course_detail(과목명: str, 과목코드: str, 학점: int, 분야: str, 대분류: str) -> None:
  """선택한 교양 과목의 추천 지수·후기 표시 및 작성."""
  key = course_review_key(과목명, 과목코드)
  reviews = get_course_reviews(key)
  avg = average_rating(reviews)

  st.markdown(f"### {과목명}")
  st.caption(f"{대분류} · {분야} · {학점}학점" + (f" · `{과목코드}`" if 과목코드 else ""))
  st.markdown(f"**추천 지수** {stars_text(avg)} ({len(reviews)}개의 평가)")

  st.divider()
  st.markdown("#### 📝 수강 후기")
  if reviews:
    for r in reversed(reviews):
      st.markdown(
          f"**{r['작성자']}** · {'⭐' * r['별점']} · {r['작성일']}\n\n{r['내용']}"
      )
      st.divider()
  else:
    st.info("아직 작성된 후기가 없습니다. 첫 후기를 남겨 보세요!")

  st.markdown("#### ✍️ 후기 작성")
  with st.form(f"review_form_{key}", clear_on_submit=True):
    c1, c2 = st.columns([1, 2])
    with c1:
      별점 = st.select_slider("추천 별점", options=[1, 2, 3, 4, 5], value=5)
    with c2:
      작성자 = st.text_input("닉네임 (선택)", placeholder="익명 가능")
    내용 = st.text_area("후기 내용", placeholder="수업 난이도, 추천 이유 등을 자유롭게 작성해 주세요.", height=120)
    if st.form_submit_button("후기 등록", type="primary", use_container_width=True):
      if not 내용.strip():
        st.warning("후기 내용을 입력해 주세요.")
      else:
        add_course_review(key, 별점, 작성자, 내용)
        st.success("후기가 등록되었습니다!")
        st.rerun()


def page_liberal_arts_catalog() -> None:
  st.title("📚 교양 과목 안내")
  st.markdown(
      "영역별 교양 과목을 확인하고, **과목명을 클릭**해 추천 지수(별점)와 후기를 작성할 수 있습니다."
  )
  st.caption(f"총 **{len(LIBERAL_ARTS_CATALOG)}개** 과목")

  if LIBERAL_ARTS_CATALOG.empty:
    st.info("등록된 교양 과목이 없습니다.")
    return

  st.subheader("영역별 과목 목록")
  for category, areas in LIBERAL_ARTS_STRUCTURE.items():
    with st.expander(category, expanded=(category == "역량교양")):
      for area in areas:
        st.markdown(f"**{area}**")
        area_df = LIBERAL_ARTS_CATALOG[LIBERAL_ARTS_CATALOG["분야"] == area].copy()
        if area_df.empty:
          st.caption("(등록된 과목 없음)")
          st.divider()
          continue

        cols = st.columns(2)
        for idx, (_, row) in enumerate(area_df.iterrows()):
          key = course_review_key(row["과목명"], row.get("과목코드", ""))
          avg = average_rating(get_course_reviews(key))
          label = f"{row['과목명']} ({row['학점']}점)"
          if avg:
            label += f" · ⭐{avg:.1f}"
          with cols[idx % 2]:
            if st.button(label, key=f"la_course_btn_{area}_{idx}", use_container_width=True):
              st.session_state.selected_교양_과목 = row.to_dict()
              st.rerun()
        st.divider()

  selected_row = st.session_state.selected_교양_과목
  if not selected_row:
    st.info("위 목록에서 교양 과목명을 클릭하면 해당 과목의 평점·후기를 확인할 수 있습니다.")
    return

  st.divider()
  render_liberal_course_detail(
      selected_row["과목명"],
      str(selected_row.get("과목코드", "") or ""),
      int(selected_row["학점"]),
      selected_row["분야"],
      selected_row["대분류"],
  )


# =============================================================================
# 페이지: 졸업팁 게시판
# =============================================================================

def page_graduation_tips() -> None:
  st.title("💡 졸업팁")
  st.markdown(
      "선배들의 졸업 경험·수강 팁을 공유하는 게시판입니다. "
      "졸업하신 분들의 조언을 읽거나 직접 글을 남겨 보세요."
  )

  tab_목록, tab_작성 = st.tabs(["📋 팁 목록", "✍️ 글쓰기"])

  with tab_작성:
    st.subheader("졸업팁 작성")
    with st.form("graduation_tip_form", clear_on_submit=True):
      제목 = st.text_input("제목", placeholder="예: 24학번 졸업 수강 플랜 / 교직 실습 팁")
      c1, c2 = st.columns(2)
      with c1:
        작성자 = st.text_input("닉네임", placeholder="익명 가능")
      with c2:
        학번 = st.selectbox("학번 (선택)", ["", *STUDENT_YEARS, "기타"])
      내용 = st.text_area(
          "내용",
          placeholder="어떤 순서로 과목을 들었는지, 졸업 전 꼭 챙길 것, 추천 교양 등을 적어 주세요.",
          height=200,
      )
      if st.form_submit_button("게시하기", type="primary", use_container_width=True):
        if not 제목.strip() or not 내용.strip():
          st.warning("제목과 내용을 모두 입력해 주세요.")
        else:
          add_graduation_tip(제목, 작성자, 학번, 내용)
          st.success("졸업팁이 등록되었습니다!")
          st.rerun()

  with tab_목록:
    tips = get_graduation_tips()
    if not tips:
      st.info("아직 등록된 졸업팁이 없습니다. **글쓰기** 탭에서 첫 글을 남겨 보세요!")
    else:
      st.caption(f"총 **{len(tips)}**개의 글")
      for tip in tips:
        학번_표시 = f" · {tip['학번']}" if tip.get("학번") else ""
        with st.container(border=True):
          st.markdown(f"### {tip['제목']}")
          st.caption(f"**{tip['작성자']}**{학번_표시} · {tip['작성일']}")
          st.markdown(tip["내용"])


# =============================================================================
# 페이지: 졸업요건 확인 (체크리스트 그리드 + 진행률 대시보드)
# =============================================================================

def page_credit_calculator() -> None:
  st.title("🧮 졸업요건 확인")

  # 학번 선택
  학번_인덱스 = STUDENT_YEARS.index(st.session_state.선택_학번)
  선택_학번 = st.selectbox(
      "학번 선택", STUDENT_YEARS, index=학번_인덱스, key="calc_학번",
  )
  st.session_state.선택_학번 = 선택_학번

  # 과목 분류
  catalog = MAJOR_COURSE_CATALOG.copy()
  major_required_df = catalog[catalog["과목명"].isin(MAJOR_REQUIRED_COURSES)].copy()
  teaching_required_df = catalog[catalog["과목명"].isin(TEACHING_REQUIRED_COURSES)].copy()
  teaching_theory_df = catalog[catalog["과목명"].isin(TEACHING_THEORY_POOL)].copy()
  basic_liberal_df = get_basic_liberal_df()  # 일반생물/물리/화학/지구과학

  # 전공선택: 전필·교직·교직이론·기초교양필수를 모두 제외한 나머지
  excluded_names = set(
      MAJOR_REQUIRED_COURSES + TEACHING_REQUIRED_COURSES
      + TEACHING_THEORY_POOL + BASIC_LIBERAL_COURSE_NAMES
  )
  elective_df = catalog[~catalog["과목명"].isin(excluded_names)].copy()

  # ── 위젯 키에서 직접 학점 계산 (렌더링 전에 읽어도 정확)
  전필_점 = get_widget_checked_credits(major_required_df, "전필")
  교직필수_점 = get_widget_checked_credits(teaching_required_df, "교직필수")
  교직이론_점 = get_widget_checked_credits(teaching_theory_df, "교직이론")
  교직_점 = 교직필수_점 + 교직이론_점
  전선_점 = get_widget_checked_credits(elective_df, "전선")
  기초교양_점 = get_widget_checked_credits(basic_liberal_df, "기초교양")
  교양_점 = sum_liberal_arts_credits(st.session_state.교양_과목)   # 역량/균형/기초SW
  일선_점 = st.session_state.inp_일선

  # 교직이론 과목 수 (위젯 키 직접 읽기)
  theory_cnt = sum(
      1 for n in TEACHING_THEORY_POOL
      if st.session_state.get(f"chk_교직이론_{n}", False)
  )

  # 세션 상태 동기화 (챗봇 분석에 사용)
  st.session_state.inp_생물전공 = 전필_점
  st.session_state.inp_교직 = 교직_점
  st.session_state.inp_전선 = 전선_점
  st.session_state.inp_심화 = 0
  st.session_state.inp_기초교양 = 기초교양_점

  # ── 진행률 대시보드 (상단 항상 표시) ──────────────────────────────────
  with st.container(border=True):
    st.markdown("##### 📊 현재 졸업요건 달성 현황")
    render_graduation_dashboard(
        선택_학번, 전필_점, 교직_점, 전선_점, 교양_점, 기초교양_점, 일선_점,
    )

  st.markdown("")

  # ── 탭별 체크리스트 ────────────────────────────────────────────────────
  tab_전필, tab_교직필수, tab_교직이론, tab_전선, tab_기초교양, tab_교양, tab_교직, tab_결과 = st.tabs([
      "📌 전공필수", "📌 교직필수", "📚 교직이론(8→6)", "📖 전공선택·심화",
      "🔬 기초교양필수", "🌱 교양 이수", "📝 교직 자격", "📊 분석 결과",
  ])

  with tab_전필:
    st.caption(f"이수한 과목에 체크하세요 — 현재 **{전필_점}점** 선택됨 (목표 23점)")
    if major_required_df.empty:
      st.info("전공필수 과목 데이터가 없습니다. major_course_catalog.json을 확인해 주세요.")
    else:
      render_course_checklist(major_required_df, "전필")

  with tab_교직필수:
    st.caption(f"이수한 과목에 체크하세요 — 현재 **{교직필수_점}점** 선택됨")
    if teaching_required_df.empty:
      st.info("교직필수 과목 데이터가 없습니다.")
    else:
      render_course_checklist(teaching_required_df, "교직필수")

  with tab_교직이론:
    t_status = "✅ 충족" if theory_cnt >= 6 else f"❌ {6 - theory_cnt}과목 더 필요"
    st.caption(
        f"8과목 중 **6과목 이상** 이수 필요 — "
        f"현재 **{theory_cnt}/6과목** {t_status} ({교직이론_점}점)"
    )
    if teaching_theory_df.empty:
      st.info("교직이론 과목 데이터가 없습니다.")
    else:
      render_course_checklist(teaching_theory_df, "교직이론")

  with tab_전선:
    req = GRADUATION_REQUIREMENTS[선택_학번]
    전선_목표 = req["전선"]   # 48 (전선 27 + 심화 21)
    st.caption(
        f"전공선택·심화(전선 27점 + 심화 21점 = 48점) — 현재 **{전선_점}점** 선택됨"
    )
    if elective_df.empty:
      st.info("전공선택 과목 데이터가 없습니다.")
    else:
      render_course_checklist(elective_df, "전선")

    st.divider()
    st.session_state.inp_일선 = st.number_input(
        "일선(일반선택) 학점 직접 입력",
        min_value=0, max_value=200,
        value=st.session_state.inp_일선,
        step=1, key="ilsun_input",
        help="교양 초과분은 자동으로 일선에 더해집니다. 이 칸은 그 외의 일선 학점을 입력하세요.",
    )

  with tab_기초교양:
    st.caption(
        f"1학년 필수 이수 교양 과목 — 현재 **{기초교양_점}점** 선택됨 "
        f"(교필: 일반생물1/2, 교선필수: 일반물리·화학·지구과학 각 1/2)"
    )
    render_course_checklist(basic_liberal_df, "기초교양")

  with tab_교양:
    st.caption("이수한 교양 과목을 분야별로 등록하세요. (분야당 1과목 이상 필요)")
    for category, areas in LIBERAL_ARTS_STRUCTURE.items():
      with st.expander(category, expanded=(category == "역량교양")):
        for area in areas:
          render_liberal_arts_course_input(area)
          st.divider()

  with tab_교직:
    st.caption("교직 자격증 필수 이수 항목의 년도·학기를 등록하세요.")
    for 항목 in TEACHING_LICENSE_KEYS:
      render_teaching_license_input(항목)
      st.divider()

  with tab_결과:
    user_credits = get_user_credits()
    유효_학점 = calc_effective_credits(선택_학번, user_credits)

    req_r = GRADUATION_REQUIREMENTS[선택_학번]
    st.info(
        f"**{선택_학번}** | 교양(기초포함) {user_credits['교양']}점 | "
        f"인정 총학점 **{유효_학점['총학점_인정']}점** / "
        f"기준 {req_r['총학점']}점"
    )

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("교직", f"{user_credits['교직']}점")
    c2.metric("생물전공(전필)", f"{user_credits['생물전공']}점")
    c3.metric("전공선택·심화", f"{user_credits['전선']}점")
    c4.metric("교양(기초포함)", f"{user_credits['교양']}점")
    c5.metric("일선(자동포함)", f"{유효_학점['일선_유효']}점")

    t_status_r = "✅ 충족" if theory_cnt >= 6 else "❌ 미충족"
    st.caption(f"교직이론 8과목 중 6과목 이수: **{t_status_r}** ({theory_cnt}과목 선택)")

    if 유효_학점["일선_교양대체"] > 0:
      st.caption(
          f"💡 교양 초과 {유효_학점['일선_교양대체']}점이 일선으로 자동 인정됩니다."
      )

    if st.button("📋 졸업 요건 종합 분석 보기", type="primary", use_container_width=True):
      st.markdown(analyze_graduation(
          선택_학번, user_credits,
          st.session_state.교양_과목, st.session_state.교직_이수,
      ))

    st.divider()
    if st.session_state.student_id:
      if st.button("💾 내 입력 내용 저장", use_container_width=True, key="save_in_result_tab"):
        save_user_data(st.session_state.student_id, get_current_user_save_data())
        st.success(f"✅ **{st.session_state.student_id}** 데이터가 저장되었습니다!")
    else:
      st.info("💡 왼쪽 사이드바에서 학번을 입력하면 입력 내용을 저장·불러올 수 있습니다.")


# =============================================================================
# 메인: 사이드바 메뉴 + 페이지 라우팅
# =============================================================================

with st.sidebar:
  st.header("🎓 생물교육과")
  st.caption("24~26학번 교육과정")

  if st.button("🏠 홈으로", use_container_width=True, type="primary"):
    st.session_state.show_home = True
    st.rerun()

  current_index = 0
  if st.session_state.active_menu in MENU_OPTIONS:
    current_index = MENU_OPTIONS.index(st.session_state.active_menu)
  menu = st.radio(
      "메뉴",
      MENU_OPTIONS,
      index=current_index,
      label_visibility="collapsed",
      key="sidebar_menu_radio",
  )
  if st.session_state.show_home:
    if menu != st.session_state.active_menu:
      st.session_state.active_menu = menu
      st.session_state.show_home = False
  else:
    st.session_state.active_menu = menu

  st.divider()

  # ── 내 데이터 (학번 코드 저장) ──────────────────────────────────────
  st.subheader("👤 내 데이터 저장")
  st.caption("학번을 입력하면 졸업요건 입력 내용이 저장됩니다.\n링크를 닫아도 다음에 같은 학번으로 불러올 수 있습니다.")

  input_id = st.text_input(
    "학번 입력",
    placeholder="예: 2024001",
    value=st.session_state.student_id,
    label_visibility="collapsed",
    key="sidebar_student_id_input",
  )

  col_load, col_save = st.columns(2)
  with col_load:
    if st.button("📂 불러오기", use_container_width=True, key="btn_load_user"):
      sid = input_id.strip()
      if sid:
        st.session_state.student_id = sid
        saved = load_user_data(sid)
        if saved:
          apply_user_data(saved)
          st.session_state.user_logged_in = True
          st.success("데이터를 불러왔습니다!")
          st.rerun()
        else:
          st.session_state.user_logged_in = True
          st.info("저장된 데이터가 없습니다.\n졸업요건 확인 후 저장해 주세요.")
      else:
        st.warning("학번을 입력해 주세요.")
  with col_save:
    if st.button("💾 저장하기", use_container_width=True, type="primary", key="btn_save_user"):
      sid = input_id.strip() or st.session_state.student_id
      if sid:
        st.session_state.student_id = sid
        st.session_state.user_logged_in = True
        save_user_data(sid, get_current_user_save_data())
        st.success("저장 완료!")
      else:
        st.warning("먼저 학번을 입력해 주세요.")

  if st.session_state.user_logged_in and st.session_state.student_id:
    st.caption(f"✅ **{st.session_state.student_id}** 로 연결됨")

  st.divider()
  st.caption(
      "데이터:\n"
      "· major_course_catalog.json\n"
      "· liberal_arts_catalog.json\n"
      "· data/ (후기·졸업팁·개인저장)"
  )

if st.session_state.show_home:
  page_home()
elif st.session_state.active_menu == "👨‍🏫 교수님별 강의 조회":
  page_professor_courses()
elif st.session_state.active_menu == "📚 교양 과목 안내":
  page_liberal_arts_catalog()
elif st.session_state.active_menu == "💡 졸업팁":
  page_graduation_tips()
elif st.session_state.active_menu == "🧮 졸업요건 확인":
  page_credit_calculator()
else:
  page_home()
