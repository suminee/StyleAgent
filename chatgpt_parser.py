"""Parser for extracting user messages from ChatGPT exported data"""
import json
import re
from pathlib import Path
from typing import List, Optional, Dict, Tuple


# Keywords to identify email-related conversations
EMAIL_KEYWORDS = [
    'email', 'mail', 'proofread', 'review', 'correct', 'check',
    'draft', 'reply', 'respond', 'message', 'letter',
    'dear', 'regards', 'sincerely', 'best regards',
    'hi ', 'hello', 'thank you for', 'i am writing',
    'please find', 'attached', 'following up',
    '이메일', '메일', '교정', '첨삭', '검토',
]

# Patterns that indicate the user is asking for email help
EMAIL_REQUEST_PATTERNS = [
    r'proofread.*email',
    r'review.*email',
    r'correct.*email',
    r'check.*email',
    r'draft.*email',
    r'write.*email',
    r'이메일.*교정',
    r'이메일.*검토',
    r'메일.*첨삭',
]


def parse_conversations(json_path: str, output_dir: Optional[str] = None) -> List[str]:
    """
    Extract ChatGPT (assistant) responses from conversations.json
    [Legacy function - kept for backwards compatibility]
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assistant_messages = []

    for conversation in data:
        title = conversation.get("title", "Untitled")
        mapping = conversation.get("mapping", {})

        for node_id, node in mapping.items():
            message = node.get("message")
            if not message:
                continue

            author = message.get("author", {})
            role = author.get("role", "")

            if role == "assistant":
                content = message.get("content", {})
                parts = content.get("parts", [])

                for part in parts:
                    if isinstance(part, str) and part.strip():
                        assistant_messages.append(part.strip())

    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        all_text_path = output_path / "chatgpt_responses.txt"
        with open(all_text_path, "w", encoding="utf-8") as f:
            f.write("\n\n---\n\n".join(assistant_messages))

        print(f"저장 완료: {all_text_path}")
        print(f"총 {len(assistant_messages)}개의 ChatGPT 응답 추출됨")

    return assistant_messages


def parse_user_messages(json_path: str, output_dir: Optional[str] = None) -> List[str]:
    """
    Extract USER messages from conversations.json

    Args:
        json_path: Path to conversations.json file
        output_dir: Optional directory to save extracted texts

    Returns:
        List of user messages
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    user_messages = []

    for conversation in data:
        mapping = conversation.get("mapping", {})

        for node_id, node in mapping.items():
            message = node.get("message")
            if not message:
                continue

            author = message.get("author", {})
            role = author.get("role", "")

            # Only get USER messages
            if role == "user":
                content = message.get("content", {})
                parts = content.get("parts", [])

                for part in parts:
                    if isinstance(part, str) and part.strip():
                        # Filter out very short messages (likely just commands)
                        if len(part.strip()) > 50:
                            user_messages.append(part.strip())

    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        all_text_path = output_path / "user_messages.txt"
        with open(all_text_path, "w", encoding="utf-8") as f:
            f.write("\n\n---\n\n".join(user_messages))

        print(f"저장 완료: {all_text_path}")
        print(f"총 {len(user_messages)}개의 사용자 메시지 추출됨")

    return user_messages


def is_email_content(text: str) -> bool:
    """Check if text looks like email content"""
    text_lower = text.lower()

    # Check for email structure indicators
    email_indicators = [
        'dear ', 'hi ', 'hello ',
        'best regards', 'best,', 'regards,', 'sincerely',
        'thank you for your', 'thanks for',
        'i am writing to', 'i\'m writing to',
        'please find', 'please let me know',
        'looking forward', 'get back to',
        'hope this email', 'hope this finds you',
        'attached', 'following up',
        'as discussed', 'as per our',
    ]

    score = 0
    for indicator in email_indicators:
        if indicator in text_lower:
            score += 1

    # Also check for email-like structure
    if re.search(r'^(dear|hi|hello)\s+\w+', text_lower, re.MULTILINE):
        score += 2
    if re.search(r'(regards|sincerely|best|thanks)[,\s]*$', text_lower, re.MULTILINE):
        score += 2

    return score >= 2


def extract_email_from_message(text: str) -> Optional[str]:
    """
    Extract the actual email content from a user message.
    Users often include instructions before/after the email.
    """
    lines = text.split('\n')

    # Find email content boundaries
    email_start = 0
    email_end = len(lines)

    # Look for common patterns that indicate email start
    for i, line in enumerate(lines):
        line_lower = line.lower().strip()
        # Skip instruction lines
        if any(p in line_lower for p in ['proofread', 'review', 'correct', 'check', 'please', '교정', '검토', '첨삭']):
            if i < len(lines) // 3:  # Only if in first third
                email_start = i + 1
                continue
        # Look for email greeting
        if re.match(r'^(dear|hi|hello)\s+', line_lower):
            email_start = i
            break

    # Extract email portion
    email_lines = lines[email_start:email_end]
    email_text = '\n'.join(email_lines).strip()

    # Only return if it looks like actual email content
    if len(email_text) > 100 and is_email_content(email_text):
        return email_text

    return None


def parse_email_conversations(json_path: str, output_dir: Optional[str] = None) -> Tuple[List[str], Dict]:
    """
    Extract user's email drafts from email-related conversations.

    Args:
        json_path: Path to conversations.json file
        output_dir: Optional directory to save extracted texts

    Returns:
        Tuple of (list of email texts, stats dict)
    """
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    email_messages = []
    stats = {
        "total_conversations": len(data),
        "email_conversations": 0,
        "emails_extracted": 0,
    }

    for conversation in data:
        title = conversation.get("title", "").lower()
        mapping = conversation.get("mapping", {})

        # Check if conversation is email-related
        is_email_conv = any(kw in title for kw in EMAIL_KEYWORDS)

        # Get all messages in order
        messages_in_conv = []
        for node_id, node in mapping.items():
            message = node.get("message")
            if not message:
                continue

            author = message.get("author", {})
            role = author.get("role", "")
            create_time = message.get("create_time", 0)

            content = message.get("content", {})
            parts = content.get("parts", [])
            text = ""
            for part in parts:
                if isinstance(part, str):
                    text += part

            if text.strip():
                messages_in_conv.append({
                    "role": role,
                    "text": text.strip(),
                    "time": create_time or 0
                })

        # Sort by time
        messages_in_conv.sort(key=lambda x: x["time"])

        # Check first few user messages for email patterns
        for msg in messages_in_conv[:5]:
            if msg["role"] != "user":
                continue

            text = msg["text"]
            text_lower = text.lower()

            # Check if asking for email help
            is_email_request = any(re.search(p, text_lower) for p in EMAIL_REQUEST_PATTERNS)

            if is_email_request or is_email_conv:
                is_email_conv = True

                # Try to extract the email content
                email_content = extract_email_from_message(text)
                if email_content:
                    email_messages.append(email_content)
                    stats["emails_extracted"] += 1
                # Also check if the message itself is an email
                elif is_email_content(text) and len(text) > 200:
                    email_messages.append(text)
                    stats["emails_extracted"] += 1

        if is_email_conv:
            stats["email_conversations"] += 1

    # Save results
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        email_path = output_path / "user_emails.txt"
        with open(email_path, "w", encoding="utf-8") as f:
            f.write("\n\n---\n\n".join(email_messages))

        print(f"저장 완료: {email_path}")
        print(f"총 대화: {stats['total_conversations']}개")
        print(f"이메일 관련 대화: {stats['email_conversations']}개")
        print(f"추출된 이메일: {stats['emails_extracted']}개")

    return email_messages, stats


def filter_by_language(messages: List[str], language: str = "korean") -> List[str]:
    """
    Filter messages by language (simple heuristic)

    Args:
        messages: List of messages
        language: "korean" or "english"
    """
    filtered = []

    for msg in messages:
        # Simple language detection
        korean_chars = len([c for c in msg if '가' <= c <= '힣'])
        total_chars = len([c for c in msg if c.isalpha()])

        if total_chars == 0:
            continue

        korean_ratio = korean_chars / total_chars

        if language == "korean" and korean_ratio > 0.3:
            filtered.append(msg)
        elif language == "english" and korean_ratio < 0.1:
            filtered.append(msg)

    return filtered


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("사용법: python chatgpt_parser.py <conversations.json 경로> [출력 폴더] [모드]")
        print("")
        print("모드:")
        print("  assistant  - ChatGPT 응답 추출 (기본)")
        print("  user       - 사용자 메시지 추출")
        print("  emails     - 사용자의 이메일 초안만 추출")
        print("")
        print("예시:")
        print("  python chatgpt_parser.py ./conversations.json ./samples/chatgpt emails")
        sys.exit(1)

    json_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "./samples/chatgpt"
    mode = sys.argv[3] if len(sys.argv) > 3 else "assistant"

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    if mode == "emails":
        # Extract only user's email drafts
        print("=== 이메일 추출 모드 ===")
        emails, stats = parse_email_conversations(json_path, output_dir)

        # Filter to English only
        english_emails = filter_by_language(emails, "english")
        if english_emails:
            with open(output_path / "user_emails_english.txt", "w", encoding="utf-8") as f:
                f.write("\n\n---\n\n".join(english_emails))
            print(f"영어 이메일: {len(english_emails)}개")

    elif mode == "user":
        # Extract all user messages
        print("=== 사용자 메시지 추출 모드 ===")
        messages = parse_user_messages(json_path, output_dir)

        korean_msgs = filter_by_language(messages, "korean")
        if korean_msgs:
            with open(output_path / "user_korean.txt", "w", encoding="utf-8") as f:
                f.write("\n\n---\n\n".join(korean_msgs))
            print(f"한국어 메시지: {len(korean_msgs)}개")

        english_msgs = filter_by_language(messages, "english")
        if english_msgs:
            with open(output_path / "user_english.txt", "w", encoding="utf-8") as f:
                f.write("\n\n---\n\n".join(english_msgs))
            print(f"영어 메시지: {len(english_msgs)}개")

    else:
        # Original mode: extract assistant responses
        print("=== ChatGPT 응답 추출 모드 ===")
        messages = parse_conversations(json_path, output_dir)

        korean_msgs = filter_by_language(messages, "korean")
        if korean_msgs:
            with open(output_path / "chatgpt_korean.txt", "w", encoding="utf-8") as f:
                f.write("\n\n---\n\n".join(korean_msgs))
            print(f"한국어 응답: {len(korean_msgs)}개")

        english_msgs = filter_by_language(messages, "english")
        if english_msgs:
            with open(output_path / "chatgpt_english.txt", "w", encoding="utf-8") as f:
                f.write("\n\n---\n\n".join(english_msgs))
            print(f"영어 응답: {len(english_msgs)}개")
