# sjhong76/utils/parser.py
import re

def normalize_dob(text):
    """1976년 10월 5일, 76-10-5, 761005 등 모든 날짜를 YYMMDD로 정규화"""
    # 1. 숫자만 모두 추출
    nums = re.findall(r'\d+', text)
    if not nums: return None
    
    # 2. 연, 월, 일이 분리된 경우 (예: ['1976', '10', '5'])
    if len(nums) >= 3:
        year = nums[0][-2:] # 뒤의 2자리 (76)
        month = nums[1].zfill(2) # 1 -> 01
        day = nums[2].zfill(2) # 5 -> 05
        return f"{year}{month}{day}"
    
    # 3. 숫자가 하나로 붙어있는 경우 (예: ['19761005'])
    combined = "".join(nums)
    if len(combined) == 8: return combined[2:]
    if len(combined) == 6: return combined
    
    return None

def parse_user_profile(message):
    dob = normalize_dob(message)
    # 한글 성함 2~4자 추출
    name_match = re.search(r'[가-힣]{2,4}', message)
    name = name_match.group() if name_match else None
    return name, dob