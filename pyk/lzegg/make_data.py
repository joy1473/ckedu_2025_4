import json
import random

def generate_stock_data(count=1000):
    stock_list = []
    categories = ["반도체", "IT", "바이오", "자동차", "에너지", "금융", "엔터테인먼트", "식음료"]
    
    # 기초가 되는 실존 종목 일부
    base_stocks = [
        ("005930", "삼성전자"), ("000660", "SK하이닉스"), ("035420", "NAVER"),
        ("035720", "카카오"), ("005380", "현대차"), ("068270", "셀트리온")
    ]

    for i in range(count):
        if i < len(base_stocks):
            code, name = base_stocks[i]
        else:
            code = f"{random.randint(100000, 999999)}"
            name = f"가상종목_{i}"
        
        # 데이터 생성
        current_price = random.randint(5000, 500000) # 현재가
        buy_price = random.randint(5000, 500000)    # 내가 산 가격 (수익률 계산용)
        quantity = random.randint(1, 100)           # 보유 수량
        
        stock_list.append({
            "code": code,
            "name": name,
            "currentPrice": current_price,
            "buyPrice": buy_price,
            "quantity": quantity,
            "category": random.choice(categories),
            "change": f"{random.uniform(-5, 5):.2f}%"
        })
    
    with open('stocks.json', 'w', encoding='utf-8') as f:
        json.dump(stock_list, f, ensure_ascii=False, indent=4)
    print(f"{count}건의 데이터가 stocks.json으로 저장되었습니다.")

if __name__ == "__main__":
    generate_stock_data(1000)