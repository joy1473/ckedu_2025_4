import os
import sys
import datetime
from pymongo import MongoClient

# ==========================================
# 1. DB 연결 함수 (Get)
# ==========================================
def get_mongodb_collection(in_db_name, in_col_name):
    # (주의) 모든 내부 줄은 왼쪽에서 공백 4칸을 유지해야 합니다.
    v_client = MongoClient('mongodb://localhost:27017/')
    v_db = v_client[in_db_name]
    out_collection = v_db[in_col_name]
    return out_collection

# ==========================================
# 2. 특정 단일 파일 데이터 추출 함수 (Get)
# ==========================================
# 설명 : 지정된 하나의 파일 경로를 읽어 단어 리스트를 반환합니다.
def get_terms_from_one_file(in_file_path):
    out_term_list = set()

    # 파일이 실제로 존재하는지 확인
    if not os.path.exists(in_file_path):
        print(f"🔴 오류: '{in_file_path}' 파일을 찾을 수 없습니다.")
        return []

    print(f"📄 단일 파일 분석 시작: {in_file_path}")

    try:
        # 인코딩 오류 방지를 위해 utf-8로 읽습니다.
        with open(in_file_path, 'r', encoding='utf-8') as v_file:
            for v_line in v_file:
                v_term = v_line.strip()
                # [필터링] 빈 줄 제외
                if v_term:
                    out_term_list.add(v_term)
    except Exception as e:
        print(f"🔴 파일 처리 중 오류: {e}")
        return []

    return list(out_term_list)

# ==========================================
# 3. 추출된 단어 일괄 DB 적재 함수 (Set)
# ==========================================
def set_slang_bulk_insert(in_col, in_term_list, category="imported_1"):
    """in_term_list(리스트)을 받아 중복검사 후 DB에 일괄 저장하고 저장 건수를 반환합니다."""
    v_insert_docs = []
    v_duplicate_count = 0

    for v_term in in_term_list:
        if not in_col.find_one({"term": v_term}):
            v_insert_docs.append({
                "term": v_term,
                "status": "raw",
                "category": category,
                "created_at": datetime.datetime.now()
            })
        else:
            v_duplicate_count += 1

    if v_insert_docs:
        v_result = in_col.insert_many(v_insert_docs)
        out_count = len(v_result.inserted_ids)
    else:
        out_count = 0

    print(f"ℹ️ 기존 DB 중복 제외: {v_duplicate_count}건")
    return out_count

# ==========================================
# 메인 실행 엔진 (Main)
# ==========================================
if __name__ == "__main__":
    v_db_name = "game_db"
    v_col_name = "game_terms"

    # [Step 1] DB 연결
    v_col = get_mongodb_collection(v_db_name, v_col_name)

    # CLI 인자 처리: none -> 기본 DATA/1.txt, 'all' -> DATA/*.txt, '3-7' 같은 범위 지정, 또는 파일경로/파일명 직접 지정
    arg = sys.argv[1] if len(sys.argv) > 1 else None

    if arg is None:
        v_target_files = ["./DATA/1.txt"]
        print("🚀 [게으른 달걀] 기본: DATA/1.txt 단일 파일 주입 모드")
    else:
        if arg.lower() == "all":
            files = sorted([os.path.join("DATA", f) for f in os.listdir("DATA") if f.endswith(".txt")])
            if not files:
                print("🔴 DATA 폴더에 처리할 .txt 파일이 없습니다.")
                sys.exit(1)
            v_target_files = files
            print(f"🚀 [게으른 달걀] 'all' 모드: {len(files)}개 파일 처리")
        else:
            # 숫자 범위 형식 허용: '3-7', '3~7', '3:7', '3..7' 등
            import re
            range_match = None
            m = re.match(r"^\s*(\d+)\s*[-~:]\s*(\d+)\s*$", arg)
            if not m:
                m2 = re.match(r"^\s*(\d+)\s*\.\.\s*(\d+)\s*$", arg)
                if m2:
                    range_match = (int(m2.group(1)), int(m2.group(2)))
            else:
                range_match = (int(m.group(1)), int(m.group(2)))

            if range_match:
                start, end = range_match
                if start > end:
                    start, end = end, start
                candidate_files = [os.path.join("DATA", f"{i}.txt") for i in range(start, end + 1)]
                existing = [f for f in candidate_files if os.path.exists(f)]
                missing = [f for f in candidate_files if not os.path.exists(f)]
                if not existing:
                    print(f"🔴 지정한 범위에 해당하는 파일이 없습니다: {arg}")
                    if missing:
                        print(f"🔍 누락된 파일: {', '.join(missing)}")
                    sys.exit(1)
                v_target_files = existing
                print(f"🚀 범위 모드: {start}~{end} -> 처리 파일 {len(existing)}개 (누락 {len(missing)}개)")
                if missing:
                    print(f"🔍 누락된 파일: {', '.join(missing)}")
            else:
                candidate = arg
                if not os.path.exists(candidate) and os.path.exists(os.path.join("DATA", candidate)):
                    candidate = os.path.join("DATA", candidate)
                if not os.path.exists(candidate):
                    if not candidate.endswith(".txt"):
                        candidate2 = candidate + ".txt"
                        if os.path.exists(candidate2):
                            candidate = candidate2
                        elif os.path.exists(os.path.join("DATA", candidate2)):
                            candidate = os.path.join("DATA", candidate2)
                if not os.path.exists(candidate):
                    print(f"🔴 지정한 파일을 찾을 수 없습니다: {arg}")
                    sys.exit(1)
                v_target_files = [candidate]
                print(f"🚀 [게으른 달걀] 지정 파일 처리: {candidate}")

    total_inserted = 0
    for file_path in v_target_files:
        print("-" * 50)
        v_terms = get_terms_from_one_file(file_path)
        print(f"📦 총 {len(v_terms)}개의 유효 단어 추출 성공")

        if v_terms:
            base = os.path.basename(file_path)
            name_noext = os.path.splitext(base)[0]
            if name_noext.isdigit():
                category = f"imported_{name_noext}"
            else:
                category = "imported_file"

            v_final_count = set_slang_bulk_insert(v_col, v_terms, category=category)
            total_inserted += v_final_count
            print(f"✅ {base} 저장 완료: {v_final_count}건")

    print("-" * 50)
    print(f"🏁 최종 DB 총 데이터 보유량: {v_col.count_documents({})}건 (이번 실행 저장: {total_inserted}건)")