"""Writing agent that generates text in the user's style"""
import anthropic
from typing import Dict, Any, Optional
from config import ANTHROPIC_API_KEY, DEFAULT_MODEL, MAX_TOKENS, TEMPERATURE


class WritingAgent:
    """Agent that writes in the user's style"""

    def __init__(self, style_profile: Dict[str, Any], sample_texts: list[str]):
        self.style_profile = style_profile
        self.sample_texts = sample_texts
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    def _build_system_prompt(self) -> str:
        """Build system prompt based on style profile"""
        patterns = self.style_profile.get("patterns", {})
        ss = self.style_profile.get("sentence_stats", {})
        vocab = self.style_profile.get("vocabulary", {})

        # Get frequent words
        freq_words = vocab.get("frequent_words", [])
        word_list = ", ".join([w for w, _ in freq_words[:15]])

        # Sample sentences for style reference
        samples = self.style_profile.get("sample_sentences", [])
        sample_text = "\n".join(f"- {s}" for s in samples[:5])

        # Build the prompt
        prompt = f"""당신은 사용자의 글쓰기 스타일을 완벽하게 모방하는 글쓰기 어시스턴트입니다.

## 사용자의 글쓰기 스타일 특성

### 문장 스타일
- 평균 문장 길이: 약 {ss.get('avg_length_chars', 50):.0f}자
- 평균 단어 수: 약 {ss.get('avg_word_count', 10):.0f}개
- 문체: {patterns.get('formal_tone', 'neutral')}

### 글쓰기 패턴
- 글머리 기호 사용: {'자주 사용함' if patterns.get('uses_bullet_points') else '거의 사용 안함'}
- 번호 매기기: {'자주 사용함' if patterns.get('uses_numbering') else '거의 사용 안함'}
- 질문 활용: {'자주 사용함' if patterns.get('uses_questions') else '거의 사용 안함'}

### 자주 사용하는 표현
{word_list}

### 예시 문장 (참고용)
{sample_text}

## 지침
1. 위 스타일 특성을 철저히 따라 글을 작성하세요
2. 사용자가 자주 쓰는 표현과 문체를 자연스럽게 활용하세요
3. 문장 길이와 구조를 사용자 스타일에 맞추세요
4. 새로운 내용을 창작하되, 스타일은 일관되게 유지하세요
"""
        return prompt

    def _build_sample_context(self) -> str:
        """Build context with actual sample writings"""
        if not self.sample_texts:
            return ""

        samples = self.sample_texts[:3]  # Use up to 3 samples
        context = "\n\n## 사용자가 실제 작성한 글 예시\n\n"
        for i, text in enumerate(samples, 1):
            # Truncate if too long
            truncated = text[:1500] + "..." if len(text) > 1500 else text
            context += f"### 예시 {i}\n{truncated}\n\n"

        return context

    def write(
        self,
        topic: str,
        context: Optional[str] = None,
        doc_type: str = "일반 문서",
        length: str = "medium"
    ) -> str:
        """Generate text in user's style"""

        length_guide = {
            "short": "200-400자",
            "medium": "500-800자",
            "long": "1000-1500자"
        }

        user_prompt = f"""다음 주제로 {doc_type}를 작성해주세요.

## 주제
{topic}

"""
        if context:
            user_prompt += f"""## 추가 맥락
{context}

"""

        user_prompt += f"""## 요청사항
- 분량: {length_guide.get(length, '500-800자')} 정도
- 위에서 분석된 사용자의 글쓰기 스타일을 정확하게 따라주세요
- 자연스럽고 일관된 톤을 유지해주세요
"""

        system_prompt = self._build_system_prompt()
        sample_context = self._build_sample_context()

        if sample_context:
            system_prompt += sample_context

        response = self.client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )

        return response.content[0].text

    def rewrite(self, original_text: str, instructions: Optional[str] = None) -> str:
        """Rewrite existing text in user's style"""

        user_prompt = f"""다음 글을 제 스타일로 다시 작성해주세요.

## 원본 글
{original_text}

"""
        if instructions:
            user_prompt += f"""## 추가 지시사항
{instructions}
"""

        system_prompt = self._build_system_prompt()
        sample_context = self._build_sample_context()

        if sample_context:
            system_prompt += sample_context

        response = self.client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )

        return response.content[0].text

    def reply_email(self, received_email: str, key_points: Optional[str] = None) -> str:
        """Generate email reply in user's style"""

        user_prompt = f"""다음 이메일에 대한 답장을 작성해주세요.

## 받은 이메일
{received_email}

"""
        if key_points:
            user_prompt += f"""## 답장에 포함할 내용
{key_points}
"""

        system_prompt = self._build_system_prompt()
        system_prompt += "\n\n비즈니스 이메일 형식을 따르되, 사용자의 글쓰기 스타일을 유지하세요."

        sample_context = self._build_sample_context()
        if sample_context:
            system_prompt += sample_context

        response = self.client.messages.create(
            model=DEFAULT_MODEL,
            max_tokens=MAX_TOKENS,
            temperature=TEMPERATURE,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_prompt}
            ]
        )

        return response.content[0].text
