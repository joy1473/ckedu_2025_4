# [수정된 함수] GPT에게 시나리오 판단의 최종 권한을 부여합니다.
def get_ai_agent_mentoring(term: str, score: float):
    """
    GPT가 원문을 분석하여 KoELECTRA의 점수를 교정(Override)하고 
    최종 시나리오를 결정하는 지능형 로직입니다. [cite: 2026-01-04]
    """
    v_tag_initial = get_scenario_tag(score) # 모델이 판단한 1차 태그
    
    # GPT에게 보내는 지침 (교정 로직 포함)
    v_system_content = f"""
    {AI_AGENT_PROMPTS["BASE_PERSONA"]}
    
    [중요: 시나리오 교정 지침]
    - 입력값: "{term}"
    - AI 점수: {score} (참고용)
    - 현재 모델 판단: {v_tag_initial}
    
    너는 위 점수에 얽매이지 말고 사용자의 '원문'을 한국 주식 시장 문맥에서 재해석해.
    예를 들어 '빨간 불'은 상승을 의미하므로 점수가 낮아도 긍정 시나리오를 적용해야 해.
    
    답변은 다음 형식을 지켜줘:
    [SCENARIO]: (EXTREME_NEGATIVE / MODERATE_NEGATIVE / NEUTRAL / MODERATE_POSITIVE / EXTREME_POSITIVE 중 하나 선택)
    [RESPONSE]: (선택한 시나리오 전략에 따른 전문 금융 통역 답변)
    """
    
    try:
        response = client_gpt.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": v_system_content}],
            max_tokens=500
        )
        v_full_text = response.choices[0].message.content
        
        # GPT 응답에서 태그와 답변을 분리하여 교정된 태그를 추출합니다. [cite: 2026-01-04]
        v_final_tag = v_tag_initial
        v_final_response = v_full_text
        
        if "[SCENARIO]:" in v_full_text:
            parts = v_full_text.split("[RESPONSE]:")
            v_final_tag = parts[0].replace("[SCENARIO]:", "").strip()
            v_final_response = parts[1].strip()
            
        return v_final_response, v_final_tag, v_system_content
    except Exception as e:
        return f"GPT 엔진 오류: {str(e)}", "ERROR", ""

# [로깅 부분 수정] 
# 이제 log_collection.insert_one 로직에서 
# "model_score_tag": v_tag_initial (모델의 오판)과 
# "final_scenario_tag": v_tag (GPT의 교정)를 비교할 수 있게 됩니다.