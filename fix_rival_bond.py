"""라이벌 본드 이벤트 일괄 수정:
1) Stage 3 보상 대폭 축소 (A안 × 2/3)
2) 모든 이벤트 도입 대사 추가 ('할 말 있어' → '무슨 일인데?')
"""
import re, os, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PATH = r'C:\Users\pdy\변호사가되자\game.html'
with open(PATH, encoding='utf-8') as f:
    src = f.read()

original = src

# ============================================================
# 1) 보상 축소
# ============================================================
REWARD_SUBS = [
    # Stage 3 comrade 정답
    ("effects:{reputation:50, mental:20, sociability:10, funds:50000000}",
     "effects:{reputation:10, mental:3, sociability:2, funds:3000000}"),
    # Stage 3 rival 정답 (승)
    ("effects:{reputation:100, fame:30, funds:100000000, mental:30, _rivalFame:-50}",
     "effects:{reputation:20, fame:5, funds:5000000, mental:5, _rivalFame:-15}"),
    # Stage 3 rival 오답 1 (양형 후퇴 / 한 발 물러서)
    ("effects:{reputation:-50, mental:-30, stress:30}",
     "effects:{reputation:-10, mental:-5, stress:5}"),
    # Stage 3 rival 오답 2 (합의 제안)
    ("effects:{reputation:-30, mental:-20}",
     "effects:{reputation:-7, mental:-3}"),
]
print("=== 보상 축소 ===")
for old, new in REWARD_SUBS:
    cnt = src.count(old)
    src = src.replace(old, new)
    print(f"  {cnt}건 치환: {old[:55]}...")

# ============================================================
# 2) 도입 대사 추가
# ============================================================
INTRO_TEXTS = {
    '이기승': '{name} 변호사, 잠깐 시간 좀 돼? 할 얘기가 있어.',
    '강하주': '{name}~ 잠깐 시간 좀 내줄 수 있어? 할 얘기가 있어.',
    '안진담': '{name}, 할 말이 있어. 잠깐 시간 돼?',
    '성리나': '{name}, 잠깐 시간 좀 내줘. 할 말이 있어.',
}
INTRO_KEYWORDS = ['할 말', '할 얘기', '시간 좀 내줄', '시간 좀 내', '시간 돼?', '시간 됩니까', '잠깐 시간', '잠시 시간', '잠시 시간될까']

# 패턴: dialogues: [ \n  {speaker:'<rival>', text:'<first>'}, \n  {next}? \n
# 두 번째 라인까지 캡처 (이미 '무슨 일인데?' 있는지 확인용)
pat = re.compile(
    r"(dialogues:\s*\[\n)"            # group 1: 'dialogues: [\n'
    r"(\s*)"                          # group 2: indent
    r"\{speaker:'(이기승|강하주|안진담|성리나)',\s*text:'([^']*)'\},\n"  # group 3: rival, group 4: first text
    r"(\s*\{[^}]*\},\n)?",            # group 5: optional second entry
    re.UNICODE
)

def fix(m):
    prefix = m.group(1)
    indent = m.group(2)
    rival = m.group(3)
    first_text = m.group(4)
    second = m.group(5) or ''

    # 이미 주인공의 '무슨 일인데?' 응답이 두 번째 라인에 있으면 스킵
    if "speaker:'{name}', text:'무슨 일인데?'" in second:
        return m.group(0)

    has_intro_already = any(kw in first_text for kw in INTRO_KEYWORDS)

    first_entry = f"{{speaker:'{rival}', text:'{first_text}'}},\n"
    player_entry = f"{indent}{{speaker:'{{name}}', text:'무슨 일인데?'}},\n"

    if has_intro_already:
        # 라이벌 인사 라인은 이미 있음 → 주인공 응답만 사이에 끼워넣기
        return prefix + indent + first_entry + player_entry + (second or '')
    else:
        # 라이벌 인사 + 주인공 응답 둘 다 prepend
        intro_entry = f"{{speaker:'{rival}', text:'{INTRO_TEXTS[rival]}'}},\n"
        return prefix + indent + intro_entry + player_entry + indent + first_entry + (second or '')

before = src
src = pat.sub(fix, src)
# 단순 카운트: 라이벌별 변경 건수
print("\n=== 도입 대사 변경 ===")
for r in INTRO_TEXTS:
    delta_intro = src.count(f"text:'{INTRO_TEXTS[r]}'") - before.count(f"text:'{INTRO_TEXTS[r]}'")
    print(f"  {r} 신규 인사 추가: {delta_intro}건")
delta_player = src.count("speaker:'{name}', text:'무슨 일인데?'") - before.count("speaker:'{name}', text:'무슨 일인데?'")
print(f"  '무슨 일인데?' 응답 신규 추가: {delta_player}건")

# 저장
if src == original:
    print("\n변경사항 없음.")
else:
    with open(PATH, 'w', encoding='utf-8') as f:
        f.write(src)
    print(f"\n저장 완료: {PATH}")
