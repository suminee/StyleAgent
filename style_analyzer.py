"""Enhanced Style Analyzer for deep writing style analysis"""
import re
import json
import math
from pathlib import Path
from typing import List, Dict, Any, Tuple
from collections import Counter


class StyleAnalyzer:
    """Analyze writing style from sample texts with advanced features"""

    # ChatGPT/LLM noise patterns to filter out
    NOISE_PATTERNS = [
        r'citeturn\d+search\d+',
        r'turn\d+search\d+',
        r'\[citation needed\]',
        r'【\d+†source】',
        r'entity\s*\w+',
        r'^\s*---\s*$',
    ]

    # Common transition words/phrases
    KOREAN_TRANSITIONS = {
        'additive': ['또한', '그리고', '더불어', '아울러', '게다가', '뿐만 아니라', '마찬가지로'],
        'contrast': ['하지만', '그러나', '반면', '반대로', '그렇지만', '다만', '오히려'],
        'causal': ['따라서', '그러므로', '때문에', '그래서', '결과적으로', '이로 인해'],
        'sequential': ['먼저', '다음으로', '그 다음', '마지막으로', '첫째', '둘째', '셋째'],
        'exemplifying': ['예를 들어', '예컨대', '구체적으로', '특히', '가령'],
        'concluding': ['결론적으로', '요약하면', '정리하면', '결국', '마무리하자면'],
    }

    ENGLISH_TRANSITIONS = {
        'additive': ['also', 'additionally', 'furthermore', 'moreover', 'in addition', 'as well'],
        'contrast': ['however', 'but', 'nevertheless', 'on the other hand', 'in contrast', 'yet'],
        'causal': ['therefore', 'thus', 'consequently', 'as a result', 'hence', 'so'],
        'sequential': ['first', 'second', 'third', 'next', 'then', 'finally', 'lastly'],
        'exemplifying': ['for example', 'for instance', 'specifically', 'such as', 'including'],
        'concluding': ['in conclusion', 'to summarize', 'in summary', 'ultimately', 'overall'],
    }

    # Common English words to exclude from signature vocabulary
    ENGLISH_STOPWORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
        'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been', 'be', 'have', 'has', 'had',
        'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must',
        'that', 'this', 'these', 'those', 'it', 'its', 'you', 'your', 'we', 'our', 'they',
        'their', 'he', 'she', 'his', 'her', 'i', 'my', 'me', 'not', 'no', 'yes', 'can',
        'if', 'when', 'where', 'what', 'which', 'who', 'how', 'why', 'all', 'each', 'more',
        'some', 'any', 'there', 'here', 'about', 'into', 'through', 'during', 'before',
        'after', 'above', 'below', 'between', 'under', 'again', 'further', 'then', 'once',
    }

    # Korean particles/endings to exclude
    KOREAN_PARTICLES = {
        '은', '는', '이', '가', '을', '를', '의', '에', '에서', '로', '으로', '와', '과',
        '도', '만', '부터', '까지', '보다', '처럼', '같이', '하고', '이나', '거나',
    }

    def __init__(self):
        self.style_profile = {}
        self.raw_texts = []
        self.cleaned_texts = []

    def analyze(self, texts: List[str]) -> Dict[str, Any]:
        """Analyze multiple texts and create a comprehensive style profile"""
        self.raw_texts = texts

        # Step 1: Clean texts (remove noise)
        self.cleaned_texts = [self._clean_text(t) for t in texts]

        # Step 2: Extract sentences and paragraphs
        all_sentences = []
        all_paragraphs = []

        for text in self.cleaned_texts:
            sentences = self._split_sentences(text)
            paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

            all_sentences.extend(sentences)
            all_paragraphs.extend(paragraphs)

        # Step 3: Build comprehensive profile
        self.style_profile = {
            "metadata": {
                "total_documents": len(texts),
                "total_characters": sum(len(t) for t in self.cleaned_texts),
            },
            "sentence_stats": self._analyze_sentences(all_sentences),
            "paragraph_stats": self._analyze_paragraphs(all_paragraphs),
            "vocabulary": self._analyze_vocabulary(self.cleaned_texts),
            "opening_patterns": self._extract_opening_patterns(all_paragraphs),
            "closing_patterns": self._extract_closing_patterns(all_paragraphs),
            "transition_analysis": self._analyze_transitions(self.cleaned_texts),
            "tone_analysis": self._analyze_tone_detailed(self.cleaned_texts),
            "structural_patterns": self._analyze_structure(self.cleaned_texts),
            "signature_phrases": self._extract_signature_phrases(self.cleaned_texts),
            "sample_sentences": self._get_representative_sentences(all_sentences),
        }

        return self.style_profile

    def _clean_text(self, text: str) -> str:
        """Remove noise patterns from text"""
        cleaned = text

        for pattern in self.NOISE_PATTERNS:
            cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE | re.MULTILINE)

        # Remove excessive whitespace
        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        cleaned = re.sub(r' {2,}', ' ', cleaned)

        return cleaned.strip()

    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences (handles Korean and English)"""
        # Split on sentence endings
        sentences = re.split(r'(?<=[.!?。])\s+', text)

        result = []
        for s in sentences:
            s = s.strip()
            # Filter out too short or noise-like sentences
            if len(s) > 10 and not re.match(r'^[-#*\d\s]+$', s):
                result.append(s)

        return result

    def _analyze_sentences(self, sentences: List[str]) -> Dict[str, Any]:
        """Analyze sentence characteristics with distribution"""
        if not sentences:
            return {}

        lengths = [len(s) for s in sentences]
        word_counts = [len(s.split()) for s in sentences]

        # Calculate standard deviation
        avg_len = sum(lengths) / len(lengths)
        variance = sum((x - avg_len) ** 2 for x in lengths) / len(lengths)
        std_dev = math.sqrt(variance)

        # Categorize sentence lengths
        short = sum(1 for l in lengths if l < 50)
        medium = sum(1 for l in lengths if 50 <= l < 150)
        long = sum(1 for l in lengths if l >= 150)

        return {
            "avg_length_chars": avg_len,
            "std_dev_length": std_dev,
            "avg_word_count": sum(word_counts) / len(word_counts),
            "min_length": min(lengths),
            "max_length": max(lengths),
            "total_sentences": len(sentences),
            "length_distribution": {
                "short_pct": short / len(sentences) * 100,
                "medium_pct": medium / len(sentences) * 100,
                "long_pct": long / len(sentences) * 100,
            }
        }

    def _analyze_paragraphs(self, paragraphs: List[str]) -> Dict[str, Any]:
        """Analyze paragraph characteristics"""
        if not paragraphs:
            return {}

        lengths = [len(p) for p in paragraphs]
        sentence_counts = [len(self._split_sentences(p)) for p in paragraphs]

        return {
            "avg_length_chars": sum(lengths) / len(lengths),
            "avg_sentences_per_para": sum(sentence_counts) / len(sentence_counts),
            "total_paragraphs": len(paragraphs),
            "single_sentence_para_pct": sum(1 for c in sentence_counts if c == 1) / len(paragraphs) * 100,
        }

    def _analyze_vocabulary(self, texts: List[str]) -> Dict[str, Any]:
        """Analyze vocabulary with noise filtering and categorization"""
        combined = " ".join(texts).lower()

        # Extract words
        words = re.findall(r'\b[a-zA-Z가-힣]+\b', combined)

        # Filter out stopwords and particles
        meaningful_words = []
        for w in words:
            if len(w) <= 1:
                continue
            if w in self.ENGLISH_STOPWORDS:
                continue
            if w in self.KOREAN_PARTICLES:
                continue
            # Filter out noise-like patterns
            if re.match(r'^(turn|search|cite|entity)\d*', w):
                continue
            meaningful_words.append(w)

        word_freq = Counter(meaningful_words)
        total = len(meaningful_words)
        unique = len(word_freq)

        # Categorize frequent words
        top_words = word_freq.most_common(50)

        # Separate Korean and English
        korean_words = [(w, c) for w, c in top_words if re.match(r'^[가-힣]+$', w)]
        english_words = [(w, c) for w, c in top_words if re.match(r'^[a-zA-Z]+$', w)]

        return {
            "total_meaningful_words": total,
            "unique_words": unique,
            "vocabulary_richness": unique / total if total > 0 else 0,
            "top_korean_words": korean_words[:20],
            "top_english_words": english_words[:20],
        }

    def _extract_opening_patterns(self, paragraphs: List[str]) -> Dict[str, Any]:
        """Extract common paragraph/document opening patterns"""
        if not paragraphs:
            return {}

        openings = []
        for p in paragraphs:
            # Get first sentence or first 100 chars
            first_sentence = self._split_sentences(p)
            if first_sentence:
                opening = first_sentence[0][:100]
                openings.append(opening)

        # Find common starting words/phrases
        first_words = []
        first_phrases = []

        for o in openings:
            words = o.split()
            if words:
                first_words.append(words[0])
                if len(words) >= 2:
                    first_phrases.append(" ".join(words[:2]))
                if len(words) >= 3:
                    first_phrases.append(" ".join(words[:3]))

        word_freq = Counter(first_words).most_common(15)
        phrase_freq = Counter(first_phrases).most_common(15)

        # Detect greeting patterns
        greeting_patterns = self._detect_greetings(openings)

        return {
            "common_first_words": word_freq,
            "common_first_phrases": phrase_freq,
            "greeting_patterns": greeting_patterns,
            "sample_openings": openings[:10],
        }

    def _detect_greetings(self, texts: List[str]) -> Dict[str, int]:
        """Detect greeting patterns"""
        patterns = {
            "안녕하세요": 0,
            "안녕": 0,
            "Hello": 0,
            "Hi": 0,
            "Dear": 0,
            "Good morning/afternoon": 0,
            "Thank you": 0,
            "감사합니다": 0,
        }

        for t in texts:
            t_lower = t.lower()
            if "안녕하세요" in t:
                patterns["안녕하세요"] += 1
            elif "안녕" in t:
                patterns["안녕"] += 1
            if "hello" in t_lower:
                patterns["Hello"] += 1
            if re.match(r'^hi\b', t_lower):
                patterns["Hi"] += 1
            if "dear" in t_lower:
                patterns["Dear"] += 1
            if "good morning" in t_lower or "good afternoon" in t_lower:
                patterns["Good morning/afternoon"] += 1
            if "thank you" in t_lower:
                patterns["Thank you"] += 1
            if "감사합니다" in t:
                patterns["감사합니다"] += 1

        return {k: v for k, v in patterns.items() if v > 0}

    def _extract_closing_patterns(self, paragraphs: List[str]) -> Dict[str, Any]:
        """Extract common paragraph/document closing patterns"""
        if not paragraphs:
            return {}

        closings = []
        for p in paragraphs:
            sentences = self._split_sentences(p)
            if sentences:
                closing = sentences[-1][-100:] if len(sentences[-1]) > 100 else sentences[-1]
                closings.append(closing)

        # Find common ending words/phrases
        last_words = []
        last_phrases = []

        for c in closings:
            words = c.split()
            if words:
                last_words.append(words[-1])
                if len(words) >= 2:
                    last_phrases.append(" ".join(words[-2:]))
                if len(words) >= 3:
                    last_phrases.append(" ".join(words[-3:]))

        word_freq = Counter(last_words).most_common(15)
        phrase_freq = Counter(last_phrases).most_common(15)

        # Detect sign-off patterns
        signoff_patterns = self._detect_signoffs(closings)

        return {
            "common_last_words": word_freq,
            "common_last_phrases": phrase_freq,
            "signoff_patterns": signoff_patterns,
            "sample_closings": closings[:10],
        }

    def _detect_signoffs(self, texts: List[str]) -> Dict[str, int]:
        """Detect sign-off patterns"""
        patterns = {
            "Best regards": 0,
            "Best": 0,
            "Thanks": 0,
            "Thank you": 0,
            "Sincerely": 0,
            "감사합니다": 0,
            "부탁드립니다": 0,
            "말씀해 주세요": 0,
        }

        for t in texts:
            t_lower = t.lower()
            if "best regards" in t_lower:
                patterns["Best regards"] += 1
            elif "best" in t_lower and len(t) < 50:
                patterns["Best"] += 1
            if "thanks" in t_lower:
                patterns["Thanks"] += 1
            if "thank you" in t_lower:
                patterns["Thank you"] += 1
            if "sincerely" in t_lower:
                patterns["Sincerely"] += 1
            if "감사합니다" in t:
                patterns["감사합니다"] += 1
            if "부탁드립니다" in t:
                patterns["부탁드립니다"] += 1
            if "말씀해 주세요" in t or "말씀해주세요" in t:
                patterns["말씀해 주세요"] += 1

        return {k: v for k, v in patterns.items() if v > 0}

    def _analyze_transitions(self, texts: List[str]) -> Dict[str, Any]:
        """Analyze transition word usage"""
        combined = " ".join(texts)

        korean_usage = {}
        english_usage = {}

        for category, words in self.KOREAN_TRANSITIONS.items():
            count = sum(len(re.findall(rf'\b{re.escape(w)}\b', combined)) for w in words)
            korean_usage[category] = count

        for category, words in self.ENGLISH_TRANSITIONS.items():
            count = sum(len(re.findall(rf'\b{re.escape(w)}\b', combined, re.IGNORECASE)) for w in words)
            english_usage[category] = count

        # Find most used specific transitions
        all_kr_transitions = []
        for words in self.KOREAN_TRANSITIONS.values():
            all_kr_transitions.extend(words)

        all_en_transitions = []
        for words in self.ENGLISH_TRANSITIONS.values():
            all_en_transitions.extend(words)

        kr_specific = Counter()
        for w in all_kr_transitions:
            kr_specific[w] = len(re.findall(rf'{re.escape(w)}', combined))

        en_specific = Counter()
        for w in all_en_transitions:
            en_specific[w] = len(re.findall(rf'\b{re.escape(w)}\b', combined, re.IGNORECASE))

        return {
            "korean_by_category": korean_usage,
            "english_by_category": english_usage,
            "top_korean_transitions": kr_specific.most_common(10),
            "top_english_transitions": en_specific.most_common(10),
        }

    def _analyze_tone_detailed(self, texts: List[str]) -> Dict[str, Any]:
        """Detailed tone analysis"""
        combined = " ".join(texts)
        combined_lower = combined.lower()

        # Korean formality levels
        korean_metrics = {
            "formal_high": len(re.findall(r'습니다|입니다|하십시오|드립니다|되겠습니다', combined)),
            "formal_polite": len(re.findall(r'해요|에요|죠|세요|군요', combined)),
            "informal": len(re.findall(r'해\b|야\b|어\b|지\b|거야|잖아', combined)),
        }

        # English formality indicators
        english_metrics = {
            "formal": len(re.findall(r'\bplease\b|\bkindly\b|\bregards\b|\bsincerely\b|\brespectfully\b', combined_lower)),
            "polite": len(re.findall(r'\bthank you\b|\bappreciate\b|\bwould you\b|\bcould you\b', combined_lower)),
            "casual": len(re.findall(r'\bhey\b|\bthanks\b|\byeah\b|\bnope\b|\bawesome\b|\bcool\b', combined_lower)),
        }

        # Determine primary tone
        kr_total = sum(korean_metrics.values())
        en_total = sum(english_metrics.values())

        kr_tone = "formal" if korean_metrics["formal_high"] > korean_metrics["informal"] else "casual"
        en_tone = "formal" if english_metrics["formal"] > english_metrics["casual"] else "casual"

        # Emotional indicators
        emotional = {
            "enthusiastic": len(re.findall(r'!|정말|너무|아주|great|amazing|excellent|excited', combined_lower)),
            "cautious": len(re.findall(r'아마|perhaps|maybe|might|possibly|조심|주의', combined_lower)),
            "direct": len(re.findall(r'must|should|need to|해야|필요합니다|중요합니다', combined_lower)),
        }

        return {
            "korean_formality": korean_metrics,
            "english_formality": english_metrics,
            "primary_korean_tone": kr_tone,
            "primary_english_tone": en_tone,
            "emotional_indicators": emotional,
        }

    def _analyze_structure(self, texts: List[str]) -> Dict[str, Any]:
        """Analyze structural patterns"""
        combined = "\n".join(texts)

        patterns = {
            "uses_bullet_points": bool(re.search(r'^[\s]*[-•*]\s', combined, re.MULTILINE)),
            "uses_numbering": bool(re.search(r'^[\s]*\d+[.)]\s', combined, re.MULTILINE)),
            "uses_headers": bool(re.search(r'^#+\s|^[A-Z][^.!?\n]{0,50}:$', combined, re.MULTILINE)),
            "uses_bold": bool(re.search(r'\*\*[^*]+\*\*', combined)),
            "uses_code_blocks": bool(re.search(r'```', combined)),
            "uses_tables": bool(re.search(r'\|.+\|', combined)),
        }

        # Count occurrences
        counts = {
            "bullet_count": len(re.findall(r'^[\s]*[-•*]\s', combined, re.MULTILINE)),
            "number_count": len(re.findall(r'^[\s]*\d+[.)]\s', combined, re.MULTILINE)),
            "header_count": len(re.findall(r'^#+\s', combined, re.MULTILINE)),
            "question_count": len(re.findall(r'\?', combined)),
        }

        return {
            "patterns": patterns,
            "counts": counts,
        }

    def _extract_signature_phrases(self, texts: List[str]) -> Dict[str, Any]:
        """Extract phrases that are characteristic of this writer"""
        combined = " ".join(texts)

        # Extract 2-grams and 3-grams
        words = re.findall(r'\b[a-zA-Z가-힣]+\b', combined)

        bigrams = []
        trigrams = []

        for i in range(len(words) - 1):
            bg = f"{words[i]} {words[i+1]}"
            # Filter out common patterns
            if not re.match(r'^(the|a|an|is|are|was|were)\s', bg.lower()):
                bigrams.append(bg)

        for i in range(len(words) - 2):
            tg = f"{words[i]} {words[i+1]} {words[i+2]}"
            trigrams.append(tg)

        bigram_freq = Counter(bigrams).most_common(30)
        trigram_freq = Counter(trigrams).most_common(20)

        # Filter meaningful ones (appears more than once)
        sig_bigrams = [(b, c) for b, c in bigram_freq if c > 2]
        sig_trigrams = [(t, c) for t, c in trigram_freq if c > 2]

        return {
            "signature_bigrams": sig_bigrams[:15],
            "signature_trigrams": sig_trigrams[:10],
        }

    def _get_representative_sentences(self, sentences: List[str], count: int = 15) -> List[str]:
        """Get representative sentences that exemplify the writing style"""
        if not sentences:
            return []

        # Filter out very short or very long
        filtered = [s for s in sentences if 30 < len(s) < 300]

        if len(filtered) <= count:
            return filtered

        # Sample from different parts
        step = len(filtered) // count
        return [filtered[i * step] for i in range(count)]

    def save_profile(self, filepath: str):
        """Save style profile to JSON file"""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(self.style_profile, f, ensure_ascii=False, indent=2)

    def load_profile(self, filepath: str) -> Dict[str, Any]:
        """Load style profile from JSON file"""
        with open(filepath, "r", encoding="utf-8") as f:
            self.style_profile = json.load(f)
        return self.style_profile

    def merge_profiles(self, existing_profile: Dict[str, Any], new_profile: Dict[str, Any]) -> Dict[str, Any]:
        """Merge two style profiles for incremental learning

        Args:
            existing_profile: The existing style profile
            new_profile: The new profile to merge in

        Returns:
            Merged profile with combined statistics
        """
        merged = {}

        # Merge metadata
        merged["metadata"] = {
            "total_documents": (
                existing_profile.get("metadata", {}).get("total_documents", 0) +
                new_profile.get("metadata", {}).get("total_documents", 0)
            ),
            "total_characters": (
                existing_profile.get("metadata", {}).get("total_characters", 0) +
                new_profile.get("metadata", {}).get("total_characters", 0)
            ),
        }

        # Merge sentence stats (weighted average)
        merged["sentence_stats"] = self._merge_sentence_stats(
            existing_profile.get("sentence_stats", {}),
            new_profile.get("sentence_stats", {})
        )

        # Merge paragraph stats
        merged["paragraph_stats"] = self._merge_paragraph_stats(
            existing_profile.get("paragraph_stats", {}),
            new_profile.get("paragraph_stats", {})
        )

        # Merge vocabulary
        merged["vocabulary"] = self._merge_vocabulary(
            existing_profile.get("vocabulary", {}),
            new_profile.get("vocabulary", {})
        )

        # Merge patterns
        merged["opening_patterns"] = self._merge_patterns(
            existing_profile.get("opening_patterns", {}),
            new_profile.get("opening_patterns", {})
        )
        merged["closing_patterns"] = self._merge_patterns(
            existing_profile.get("closing_patterns", {}),
            new_profile.get("closing_patterns", {})
        )

        # Merge transitions
        merged["transition_analysis"] = self._merge_transitions(
            existing_profile.get("transition_analysis", {}),
            new_profile.get("transition_analysis", {})
        )

        # Merge tone
        merged["tone_analysis"] = self._merge_tone(
            existing_profile.get("tone_analysis", {}),
            new_profile.get("tone_analysis", {})
        )

        # Merge structure
        merged["structural_patterns"] = self._merge_structure(
            existing_profile.get("structural_patterns", {}),
            new_profile.get("structural_patterns", {})
        )

        # Merge signatures
        merged["signature_phrases"] = self._merge_signatures(
            existing_profile.get("signature_phrases", {}),
            new_profile.get("signature_phrases", {})
        )

        # Combine sample sentences (keep recent ones)
        existing_samples = existing_profile.get("sample_sentences", [])
        new_samples = new_profile.get("sample_sentences", [])
        merged["sample_sentences"] = (new_samples + existing_samples)[:15]

        self.style_profile = merged
        return merged

    def _merge_sentence_stats(self, existing: Dict, new: Dict) -> Dict:
        """Merge sentence statistics using weighted averages"""
        if not existing:
            return new
        if not new:
            return existing

        existing_count = existing.get("total_sentences", 0)
        new_count = new.get("total_sentences", 0)
        total_count = existing_count + new_count

        if total_count == 0:
            return existing

        # Weighted average
        w1 = existing_count / total_count
        w2 = new_count / total_count

        merged = {
            "avg_length_chars": (
                existing.get("avg_length_chars", 0) * w1 +
                new.get("avg_length_chars", 0) * w2
            ),
            "std_dev_length": (
                existing.get("std_dev_length", 0) * w1 +
                new.get("std_dev_length", 0) * w2
            ),
            "avg_word_count": (
                existing.get("avg_word_count", 0) * w1 +
                new.get("avg_word_count", 0) * w2
            ),
            "min_length": min(existing.get("min_length", 9999), new.get("min_length", 9999)),
            "max_length": max(existing.get("max_length", 0), new.get("max_length", 0)),
            "total_sentences": total_count,
            "length_distribution": {
                "short_pct": (
                    existing.get("length_distribution", {}).get("short_pct", 0) * w1 +
                    new.get("length_distribution", {}).get("short_pct", 0) * w2
                ),
                "medium_pct": (
                    existing.get("length_distribution", {}).get("medium_pct", 0) * w1 +
                    new.get("length_distribution", {}).get("medium_pct", 0) * w2
                ),
                "long_pct": (
                    existing.get("length_distribution", {}).get("long_pct", 0) * w1 +
                    new.get("length_distribution", {}).get("long_pct", 0) * w2
                ),
            }
        }
        return merged

    def _merge_paragraph_stats(self, existing: Dict, new: Dict) -> Dict:
        """Merge paragraph statistics"""
        if not existing:
            return new
        if not new:
            return existing

        existing_count = existing.get("total_paragraphs", 0)
        new_count = new.get("total_paragraphs", 0)
        total_count = existing_count + new_count

        if total_count == 0:
            return existing

        w1 = existing_count / total_count
        w2 = new_count / total_count

        return {
            "avg_length_chars": (
                existing.get("avg_length_chars", 0) * w1 +
                new.get("avg_length_chars", 0) * w2
            ),
            "avg_sentences_per_para": (
                existing.get("avg_sentences_per_para", 0) * w1 +
                new.get("avg_sentences_per_para", 0) * w2
            ),
            "total_paragraphs": total_count,
            "single_sentence_para_pct": (
                existing.get("single_sentence_para_pct", 0) * w1 +
                new.get("single_sentence_para_pct", 0) * w2
            ),
        }

    def _merge_vocabulary(self, existing: Dict, new: Dict) -> Dict:
        """Merge vocabulary analysis"""
        if not existing:
            return new
        if not new:
            return existing

        # Merge word frequencies
        def merge_word_lists(list1: List[Tuple], list2: List[Tuple]) -> List[Tuple]:
            word_dict = {}
            for word, count in list1:
                word_dict[word] = word_dict.get(word, 0) + count
            for word, count in list2:
                word_dict[word] = word_dict.get(word, 0) + count
            sorted_words = sorted(word_dict.items(), key=lambda x: x[1], reverse=True)
            return sorted_words[:20]

        total_words = (
            existing.get("total_meaningful_words", 0) +
            new.get("total_meaningful_words", 0)
        )
        unique_words = (
            existing.get("unique_words", 0) +
            new.get("unique_words", 0)
        )

        return {
            "total_meaningful_words": total_words,
            "unique_words": unique_words,
            "vocabulary_richness": unique_words / total_words if total_words > 0 else 0,
            "top_korean_words": merge_word_lists(
                existing.get("top_korean_words", []),
                new.get("top_korean_words", [])
            ),
            "top_english_words": merge_word_lists(
                existing.get("top_english_words", []),
                new.get("top_english_words", [])
            ),
        }

    def _merge_patterns(self, existing: Dict, new: Dict) -> Dict:
        """Merge opening/closing patterns"""
        if not existing:
            return new
        if not new:
            return existing

        def merge_freq_lists(list1: List, list2: List) -> List:
            freq_dict = {}
            for item, count in list1:
                freq_dict[item] = freq_dict.get(item, 0) + count
            for item, count in list2:
                freq_dict[item] = freq_dict.get(item, 0) + count
            return sorted(freq_dict.items(), key=lambda x: x[1], reverse=True)[:15]

        def merge_pattern_dicts(dict1: Dict, dict2: Dict) -> Dict:
            merged = {}
            for key in set(dict1.keys()) | set(dict2.keys()):
                merged[key] = dict1.get(key, 0) + dict2.get(key, 0)
            return {k: v for k, v in merged.items() if v > 0}

        return {
            "common_first_words": merge_freq_lists(
                existing.get("common_first_words", []),
                new.get("common_first_words", [])
            ) if "common_first_words" in existing else merge_freq_lists(
                existing.get("common_last_words", []),
                new.get("common_last_words", [])
            ),
            "common_first_phrases": merge_freq_lists(
                existing.get("common_first_phrases", []),
                new.get("common_first_phrases", [])
            ) if "common_first_phrases" in existing else merge_freq_lists(
                existing.get("common_last_phrases", []),
                new.get("common_last_phrases", [])
            ),
            "greeting_patterns": merge_pattern_dicts(
                existing.get("greeting_patterns", {}),
                new.get("greeting_patterns", {})
            ) if "greeting_patterns" in existing else merge_pattern_dicts(
                existing.get("signoff_patterns", {}),
                new.get("signoff_patterns", {})
            ),
            "sample_openings": (
                new.get("sample_openings", [])[:5] +
                existing.get("sample_openings", [])[:5]
            ) if "sample_openings" in existing else (
                new.get("sample_closings", [])[:5] +
                existing.get("sample_closings", [])[:5]
            ),
        }

    def _merge_transitions(self, existing: Dict, new: Dict) -> Dict:
        """Merge transition analysis"""
        if not existing:
            return new
        if not new:
            return existing

        def merge_category_dict(dict1: Dict, dict2: Dict) -> Dict:
            merged = {}
            for key in set(dict1.keys()) | set(dict2.keys()):
                merged[key] = dict1.get(key, 0) + dict2.get(key, 0)
            return merged

        def merge_freq_lists(list1: List, list2: List) -> List:
            freq_dict = {}
            for item, count in list1:
                freq_dict[item] = freq_dict.get(item, 0) + count
            for item, count in list2:
                freq_dict[item] = freq_dict.get(item, 0) + count
            return sorted(freq_dict.items(), key=lambda x: x[1], reverse=True)[:10]

        return {
            "korean_by_category": merge_category_dict(
                existing.get("korean_by_category", {}),
                new.get("korean_by_category", {})
            ),
            "english_by_category": merge_category_dict(
                existing.get("english_by_category", {}),
                new.get("english_by_category", {})
            ),
            "top_korean_transitions": merge_freq_lists(
                existing.get("top_korean_transitions", []),
                new.get("top_korean_transitions", [])
            ),
            "top_english_transitions": merge_freq_lists(
                existing.get("top_english_transitions", []),
                new.get("top_english_transitions", [])
            ),
        }

    def _merge_tone(self, existing: Dict, new: Dict) -> Dict:
        """Merge tone analysis"""
        if not existing:
            return new
        if not new:
            return existing

        def merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
            merged = {}
            for key in set(dict1.keys()) | set(dict2.keys()):
                merged[key] = dict1.get(key, 0) + dict2.get(key, 0)
            return merged

        merged_kr = merge_dicts(
            existing.get("korean_formality", {}),
            new.get("korean_formality", {})
        )
        merged_en = merge_dicts(
            existing.get("english_formality", {}),
            new.get("english_formality", {})
        )
        merged_emotional = merge_dicts(
            existing.get("emotional_indicators", {}),
            new.get("emotional_indicators", {})
        )

        # Determine primary tone
        kr_tone = "formal" if merged_kr.get("formal_high", 0) > merged_kr.get("informal", 0) else "casual"
        en_tone = "formal" if merged_en.get("formal", 0) > merged_en.get("casual", 0) else "casual"

        return {
            "korean_formality": merged_kr,
            "english_formality": merged_en,
            "primary_korean_tone": kr_tone,
            "primary_english_tone": en_tone,
            "emotional_indicators": merged_emotional,
        }

    def _merge_structure(self, existing: Dict, new: Dict) -> Dict:
        """Merge structural patterns"""
        if not existing:
            return new
        if not new:
            return existing

        # Merge patterns (OR)
        patterns = {}
        for key in ["uses_bullet_points", "uses_numbering", "uses_headers",
                    "uses_bold", "uses_code_blocks", "uses_tables"]:
            patterns[key] = (
                existing.get("patterns", {}).get(key, False) or
                new.get("patterns", {}).get(key, False)
            )

        # Merge counts (SUM)
        counts = {}
        for key in ["bullet_count", "number_count", "header_count", "question_count"]:
            counts[key] = (
                existing.get("counts", {}).get(key, 0) +
                new.get("counts", {}).get(key, 0)
            )

        return {
            "patterns": patterns,
            "counts": counts,
        }

    def _merge_signatures(self, existing: Dict, new: Dict) -> Dict:
        """Merge signature phrases"""
        if not existing:
            return new
        if not new:
            return existing

        def merge_freq_lists(list1: List, list2: List, limit: int) -> List:
            freq_dict = {}
            for item, count in list1:
                freq_dict[item] = freq_dict.get(item, 0) + count
            for item, count in list2:
                freq_dict[item] = freq_dict.get(item, 0) + count
            return sorted(freq_dict.items(), key=lambda x: x[1], reverse=True)[:limit]

        return {
            "signature_bigrams": merge_freq_lists(
                existing.get("signature_bigrams", []),
                new.get("signature_bigrams", []),
                15
            ),
            "signature_trigrams": merge_freq_lists(
                existing.get("signature_trigrams", []),
                new.get("signature_trigrams", []),
                10
            ),
        }

    def generate_report(self) -> str:
        """Generate a comprehensive style analysis report"""
        if not self.style_profile:
            return "No style profile available. Run analyze() first."

        report = []
        report.append("=" * 60)
        report.append("         WRITING STYLE ANALYSIS REPORT")
        report.append("=" * 60)

        # Metadata
        meta = self.style_profile.get("metadata", {})
        report.append(f"\n## Overview")
        report.append(f"- Documents analyzed: {meta.get('total_documents', 0)}")
        report.append(f"- Total characters: {meta.get('total_characters', 0):,}")

        # Sentence stats
        ss = self.style_profile.get("sentence_stats", {})
        report.append(f"\n## Sentence Characteristics")
        report.append(f"- Average length: {ss.get('avg_length_chars', 0):.1f} chars")
        report.append(f"- Standard deviation: {ss.get('std_dev_length', 0):.1f}")
        report.append(f"- Total sentences: {ss.get('total_sentences', 0):,}")

        dist = ss.get("length_distribution", {})
        report.append(f"- Length distribution:")
        report.append(f"  - Short (<50 chars): {dist.get('short_pct', 0):.1f}%")
        report.append(f"  - Medium (50-150): {dist.get('medium_pct', 0):.1f}%")
        report.append(f"  - Long (>150): {dist.get('long_pct', 0):.1f}%")

        # Tone
        tone = self.style_profile.get("tone_analysis", {})
        report.append(f"\n## Tone & Formality")
        report.append(f"- Korean tone: {tone.get('primary_korean_tone', 'N/A')}")
        report.append(f"- English tone: {tone.get('primary_english_tone', 'N/A')}")

        kr_form = tone.get("korean_formality", {})
        if kr_form:
            report.append(f"- Korean formality breakdown:")
            report.append(f"  - Formal (습니다/입니다): {kr_form.get('formal_high', 0)}")
            report.append(f"  - Polite (해요/세요): {kr_form.get('formal_polite', 0)}")
            report.append(f"  - Informal: {kr_form.get('informal', 0)}")

        # Opening patterns
        opening = self.style_profile.get("opening_patterns", {})
        report.append(f"\n## Opening Patterns")
        greetings = opening.get("greeting_patterns", {})
        if greetings:
            report.append("- Greeting usage:")
            for g, count in greetings.items():
                report.append(f"  - {g}: {count}")

        first_words = opening.get("common_first_words", [])[:5]
        if first_words:
            report.append("- Common first words: " + ", ".join(f"{w}({c})" for w, c in first_words))

        # Closing patterns
        closing = self.style_profile.get("closing_patterns", {})
        report.append(f"\n## Closing Patterns")
        signoffs = closing.get("signoff_patterns", {})
        if signoffs:
            report.append("- Sign-off usage:")
            for s, count in signoffs.items():
                report.append(f"  - {s}: {count}")

        # Transitions
        trans = self.style_profile.get("transition_analysis", {})
        report.append(f"\n## Transition Words")

        kr_trans = trans.get("top_korean_transitions", [])[:5]
        if kr_trans:
            report.append("- Top Korean: " + ", ".join(f"{w}({c})" for w, c in kr_trans if c > 0))

        en_trans = trans.get("top_english_transitions", [])[:5]
        if en_trans:
            report.append("- Top English: " + ", ".join(f"{w}({c})" for w, c in en_trans if c > 0))

        # Structure
        struct = self.style_profile.get("structural_patterns", {})
        patterns = struct.get("patterns", {})
        counts = struct.get("counts", {})
        report.append(f"\n## Structural Patterns")
        report.append(f"- Uses bullet points: {'Yes' if patterns.get('uses_bullet_points') else 'No'} ({counts.get('bullet_count', 0)})")
        report.append(f"- Uses numbering: {'Yes' if patterns.get('uses_numbering') else 'No'} ({counts.get('number_count', 0)})")
        report.append(f"- Uses headers: {'Yes' if patterns.get('uses_headers') else 'No'} ({counts.get('header_count', 0)})")
        report.append(f"- Uses bold: {'Yes' if patterns.get('uses_bold') else 'No'}")
        report.append(f"- Questions asked: {counts.get('question_count', 0)}")

        # Signature phrases
        sig = self.style_profile.get("signature_phrases", {})
        bigrams = sig.get("signature_bigrams", [])[:10]
        report.append(f"\n## Signature Phrases")
        if bigrams:
            report.append("- Common phrases: " + ", ".join(f'"{b}"({c})' for b, c in bigrams[:5]))

        # Vocabulary
        vocab = self.style_profile.get("vocabulary", {})
        report.append(f"\n## Vocabulary")
        report.append(f"- Unique words: {vocab.get('unique_words', 0):,}")
        report.append(f"- Vocabulary richness: {vocab.get('vocabulary_richness', 0):.2%}")

        kr_words = vocab.get("top_korean_words", [])[:10]
        if kr_words:
            report.append("- Top Korean words: " + ", ".join(f"{w}({c})" for w, c in kr_words))

        en_words = vocab.get("top_english_words", [])[:10]
        if en_words:
            report.append("- Top English words: " + ", ".join(f"{w}({c})" for w, c in en_words))

        report.append("\n" + "=" * 60)

        return "\n".join(report)

    def get_style_summary(self) -> str:
        """Generate a concise style summary (legacy support)"""
        return self.generate_report()


if __name__ == "__main__":
    # Test
    sample_texts = [
        "안녕하세요. 오늘 회의 내용을 정리해서 공유드립니다. 주요 논의 사항은 다음과 같습니다.",
        "프로젝트 일정이 변경되었습니다. 새로운 마감일은 다음 주 금요일입니다. 문의사항 있으시면 말씀해 주세요.",
    ]

    analyzer = StyleAnalyzer()
    profile = analyzer.analyze(sample_texts)
    print(analyzer.generate_report())
