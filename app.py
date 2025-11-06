import streamlit as st
import ollama
import random

# ========== 페이지 설정 ==========
st.set_page_config(page_title="인생 상담소", page_icon="💬", layout="wide")

# ========== 데이터 ==========
male_names = ["민준", "지훈", "준호", "시우", "도윤", "현우", "건우", "태양", "재현", "동혁", "승현", "정우"]
female_names = ["수진", "예린", "서연", "하은", "지우", "은서", "아인", "채원", "다은", "가은", "민지", "수아"]
counselor_names = ['상민', '지섭', '범섭', '유타', '하쿠지', '재석', '하원', '병건']

problem_categories = {
    "경제 문제": [
        "빚이 너무 많아서 갚을 방법이 없어요.",
        "사업 실패로 파산 위기에 놓였어요.",
        "실직 후 경제적으로 너무 힘들어요.",
        "도박으로 큰 빚을 졌어요.",
        "부모님 병원비가 너무 부담돼요."
    ],
    "친구 관계": [
        "친한 친구가 갑자기 연락을 끊었어요.",
        "친구에게 배신당한 것 같아요.",
        "친구가 없어서 외로워요.",
        "친구와 사소한 일로 크게 싸웠어요.",
        "친구가 저를 이용하는 것 같아요."
    ],
    "직장 생활": [
        "업무 압박이 너무 심해서 번아웃이 왔어요.",
        "승진에서 계속 탈락해요.",
        "이직을 고민 중인데 결정하기 어려워요.",
        "일이 적성에 안 맞는 것 같아요.",
        "야근이 너무 많아서 힘들어요."
    ],
    "직장 인간관계": [
        "상사가 저만 미워하는 것 같아요.",
        "동료들이 저를 따돌려요.",
        "부하직원이 말을 안 들어요.",
        "직장 내 괴롭힘을 당하고 있어요.",
        "동료와 갈등이 심해요."
    ],
    "부모님 관계": [
        "부모님이 제 선택을 존중해주지 않아요.",
        "부모님과 소통이 안 돼요.",
        "부모님이 계속 간섭하셔서 힘들어요.",
        "부모님 건강이 안 좋아져서 걱정돼요.",
        "부모님이 이혼하셨어요."
    ],
    "연애 관계": [
        "연인과 자주 싸워요.",
        "연인이 바람을 피운 것 같아요.",
        "이별을 고민 중이에요.",
        "연인이 저를 이해해주지 않아요.",
        "연애를 시작해야 할지 모르겠어요."
    ],
    "가족 문제": [
        "배우자와 관계가 소원해졌어요.",
        "자녀와 대화가 안 돼요.",
        "시댁/처가와 갈등이 심해요.",
        "가정폭력을 당하고 있어요.",
        "이혼을 고민 중이에요."
    ],
    "건강 문제": [
        "우울증으로 힘들어요.",
        "불면증이 심해요.",
        "공황장애가 있어요.",
        "건강이 안 좋은데 병원 갈 여유가 없어요.",
        "스트레스로 몸이 망가지고 있어요."
    ],
    "학업 문제": [
        "성적이 안 올라요.",
        "진로를 결정하지 못했어요.",
        "학교 폭력을 당하고 있어요.",
        "수험 스트레스가 너무 심해요.",
        "공부 의욕이 없어요."
    ],
    "자아 정체성": [
        "제가 누군지 모르겠어요.",
        "삶의 의미를 찾지 못하겠어요.",
        "자존감이 너무 낮아요.",
        "미래가 불안해요.",
        "저 자신이 싫어요."
    ]
}

# ========== Counselee 클래스 ==========
class Counselee:
    def __init__(self, name, gender, age, problem_category, initial_concern, counselor_name):
        self.name = name
        self.gender = gender
        self.age = age
        self.problem_category = problem_category
        self.counselor_name = counselor_name
        
        self.satisfaction = 0
        self.turn_count = 0
        self.last_concern = initial_concern
        
        self.messages = [{
            "role": "system",
            "content": f"""당신은 {name} ({age}세, {gender})입니다.
상담사: {counselor_name}
문제: {problem_category}

**역할:**
- 상담사에게 고민 상담
- 150자 이내로 진솔하게
- 매번 이전과 다른 내용으로 발전
- 잘 들어주면 감사하며 더 깊은 고민 공유
- 못 들어주면 실망

**첫 고민:**
{initial_concern}"""
        }]
    
    def get_current_concern(self):
        return self.last_concern
    
    def receive_counseling(self, counselor_words):
        self.turn_count += 1
        
        eval_prompt = f"""상담사가 말했습니다: "{counselor_words}"

**평가 (-5~5점):**
- 5: 완벽한 공감과 도움
- 3: 잘 들어줌
- 0: 평범
- -3: 성의 없음
- -5: 무시당한 느낌

**중요: 다음고민은 반드시 이전과 다른 새로운 내용이어야 합니다.**

**출력 형식:**
점수: [숫자]
반응: [한 문장]
다음고민: [이전과 완전히 다른 새로운 고민, 최소 20자]"""

        response = ollama.chat(
            model='EEVE-Korean-10.8B',
            messages=self.messages + [
                {"role": "user", "content": f"상담사: {counselor_words}"},
                {"role": "user", "content": eval_prompt}
            ],
            stream=False
        )
        
        result = response['message']['content'].strip()
        
        # 파싱
        score = 0
        reaction = ""
        next_concern = ""
        
        try:
            import re
            lines = result.split('\n')
            for line in lines:
                if '점수:' in line or 'Score:' in line:
                    numbers = re.findall(r'-?\d+', line)
                    if numbers:
                        score = max(-5, min(5, int(numbers[0])))
                elif '반응:' in line or 'Response:' in line:
                    reaction = line.split(':', 1)[1].strip()
                elif '다음고민:' in line or '다음 고민:' in line:
                    next_concern = line.split(':', 1)[1].strip()
            
            if not reaction:
                reaction = result[:100]
        except:
            score = 0
            reaction = result[:100]
        
        self.satisfaction += score
        
        # 히스토리 추가
        self.messages.append({"role": "user", "content": f"상담사: {counselor_words}"})
        self.messages.append({"role": "assistant", "content": reaction})
        
        # 다음 고민 업데이트
        if next_concern and len(next_concern) >= 20 and next_concern != "만족":
            self.last_concern = next_concern
            self.messages.append({"role": "assistant", "content": next_concern})
        else:
            force_prompt = "이전 고민과 다른 새로운 측면의 고민을 50자 이내로 말해주세요."
            force_response = ollama.chat(
                model='EEVE-Korean-10.8B',
                messages=self.messages + [{"role": "user", "content": force_prompt}],
                stream=False
            )
            self.last_concern = force_response['message']['content'].strip()[:150]
            self.messages.append({"role": "assistant", "content": self.last_concern})
        
        is_satisfied = self.satisfaction >= 10
        
        return reaction, is_satisfied, score
    
    def get_final_thoughts(self):
        prompt = f"""상담이 끝났습니다.

턴: {self.turn_count}회
만족도: {self.satisfaction}점

80자로 상담이 어땠는지 평가해주세요."""

        response = ollama.chat(
            model='EEVE-Korean-10.8B',
            messages=self.messages + [{"role": "user", "content": prompt}],
            stream=False
        )
        
        return response['message']['content'].strip()

# ========== 헬퍼 함수 ==========
def create_counselee(used_categories, counselor_name):
    available = [cat for cat in problem_categories.keys() if cat not in used_categories]
    if not available:
        available = list(problem_categories.keys())
    
    category = random.choice(available)
    used_categories.add(category)
    
    gender = random.choice(["남성", "여성"])
    name_pool = male_names if gender == "남성" else female_names
    name = random.choice(name_pool)
    age = random.randint(20, 65)
    
    initial_concern = random.choice(problem_categories[category])
    
    return Counselee(name, gender, age, category, initial_concern, counselor_name)

def init_game():
    """게임 초기화"""
    counselor = random.choice(counselor_names)
    used_categories = set()
    counselees = [create_counselee(used_categories, counselor) for _ in range(4)]
    
    st.session_state.counselor = counselor
    st.session_state.counselees = counselees
    st.session_state.completed = []
    st.session_state.used_categories = used_categories
    st.session_state.turn = 1
    st.session_state.selected_idx = None
    st.session_state.counseling_mode = False
    st.session_state.game_over = False

# ========== 메인 앱 ==========
def main():
    st.title("💬 상담실")
    
    # 초기화
    if 'counselor' not in st.session_state:
        init_game()
    
    # 사이드바
    with st.sidebar:
        st.header("게임 정보")
        st.write(f"**상담사:** {st.session_state.counselor}")
        st.write(f"**턴:** {st.session_state.turn}/5")
        st.write(f"**완료:** {len(st.session_state.completed)}명")
        
        st.divider()
        
        if st.button("🔄 게임 재시작", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # 게임 오버
    if st.session_state.game_over:
        st.success("### 🎉 상담 종료!")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("✅ 상담 완료")
            if st.session_state.completed:
                for c in st.session_state.completed:
                    st.write(f"- **{c.name}** ({c.problem_category})")
                    st.write(f"  상담 {c.turn_count}회, 만족도 {c.satisfaction:+d}점")
            else:
                st.write("없음")
        
        with col2:
            st.subheader("⏳ 미완료")
            if st.session_state.counselees:
                for c in st.session_state.counselees:
                    st.write(f"- **{c.name}** ({c.problem_category})")
                    st.write(f"  상담 {c.turn_count}회, 만족도 {c.satisfaction:+d}점")
            else:
                st.write("없음")
        
        return
    
    # ========== [수정된 부분 1: 상담 진행 중] ==========
    if st.session_state.counseling_mode and st.session_state.selected_idx is not None:
        selected = st.session_state.counselees[st.session_state.selected_idx]
        
        st.info(f"### 🗣️ {selected.name}님 상담 중")

        # "뒤로 가기" 버튼 추가
        if st.button("🔙 뒤로 가기 (내담자 선택)"):
            st.session_state.counseling_mode = False
            st.session_state.selected_idx = None
            st.rerun()

        st.write(f"**{selected.age}세, {selected.gender} - {selected.problem_category}**")
        st.write(f"상담 {selected.turn_count}회, 만족도 {selected.satisfaction:+d}점")
        
        st.divider()
        
        # "지난 대화 보기" expander 삭제됨

        st.write(f"**{selected.name}:** {selected.get_current_concern()}")
        
        # 상담 입력
        with st.form("counseling_form"):
            counseling = st.text_area(
                f"{st.session_state.counselor}의 상담:",
                height=100,
                placeholder="상담 내용을 입력하세요..."
            )
            submitted = st.form_submit_button("💬 상담하기", use_container_width=True)
        
        if submitted and counseling:
            with st.spinner("상담 중..."):
                reaction, is_satisfied, score = selected.receive_counseling(counseling)
            
            st.success(f"**{selected.name}:** {reaction}")
            st.metric("점수", f"{score:+d}점", delta=f"만족도: {selected.satisfaction:+d}/10")
            
            # 만족 시
            if is_satisfied:
                final = selected.get_final_thoughts()
                st.balloons()
                st.success(f"✅ **{selected.name}:** {final}")
                st.info("상담을 마치고 돌아갔습니다.")
                
                st.session_state.completed.append(selected)
                st.session_state.counselees.pop(st.session_state.selected_idx)
                
                # 새 내담자 추가
                if st.session_state.turn < 5:
                    new = create_counselee(st.session_state.used_categories, st.session_state.counselor)
                    st.session_state.counselees.append(new)
                    st.info(f"📥 새로운 내담자 **{new.name}**님이 도착했습니다.")
            
            # 상담 모드 종료
            st.session_state.counseling_mode = False
            st.session_state.selected_idx = None
            
            # 턴 증가 및 게임 오버 체크
            if not is_satisfied or st.session_state.turn < 5:
                st.session_state.turn += 1
            
            if st.session_state.turn > 5 or not st.session_state.counselees:
                st.session_state.game_over = True
            
            st.rerun()
    
    # ========== [수정된 부분 2: 내담자 선택] ==========
    else:
        st.header(f"턴 {st.session_state.turn}/5")
        
        if not st.session_state.counselees:
            st.session_state.game_over = True
            st.rerun()
        
        st.subheader("📋 대기 중인 내담자")
        
        cols = st.columns(2)
        
        for i, c in enumerate(st.session_state.counselees):
            with cols[i % 2]:
                with st.container(border=True):
                    st.write(f"### {c.name}")
                    st.write(f"**{c.age}세, {c.gender}**")
                    st.write(f"**문제:** {c.problem_category}")
                    st.write(f"상담 {c.turn_count}회 | 만족도 {c.satisfaction:+d}점")
                    
                    st.info(f"💬 {c.get_current_concern()}")
                    
                    # "지난 대화 보기" expander 추가
                    with st.expander("지난 대화 보기"):
                        # 시스템 메시지 제외
                        history_messages = [msg for msg in c.messages if msg['role'] != 'system']
                        
                        # 현재 고민은 제외하고 표시
                        current_concern = c.get_current_concern()
                        if history_messages and history_messages[-1]['content'] == current_concern:
                            history_to_display = history_messages[:-1]
                        else:
                            history_to_display = history_messages

                        if not history_to_display:
                            st.write("첫 상담입니다.")
                        else:
                            for msg in history_to_display:
                                if msg['role'] == 'user':
                                    st.write(f"**{st.session_state.counselor} (나):** {msg['content']}")
                                elif msg['role'] == 'assistant':
                                    st.write(f"**{c.name}:** {msg['content']}")
                    
                    if st.button(f"상담하기", key=f"select_{i}", use_container_width=True):
                        st.session_state.selected_idx = i
                        st.session_state.counseling_mode = True
                        st.rerun()

if __name__ == "__main__":
    main()