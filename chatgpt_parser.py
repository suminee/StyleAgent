"""Parser for extracting ChatGPT responses from exported data"""
import json
from pathlib import Path
from typing import List, Optional


def parse_conversations(json_path: str, output_dir: Optional[str] = None) -> List[str]:
    """
    Extract ChatGPT (assistant) responses from conversations.json

    Args:
        json_path: Path to conversations.json file
        output_dir: Optional directory to save extracted texts

    Returns:
        List of assistant messages
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

            # Only get assistant (ChatGPT) messages
            if role == "assistant":
                content = message.get("content", {})
                parts = content.get("parts", [])

                for part in parts:
                    if isinstance(part, str) and part.strip():
                        assistant_messages.append(part.strip())

    # Save to files if output_dir specified
    if output_dir:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save all messages to one file
        all_text_path = output_path / "chatgpt_responses.txt"
        with open(all_text_path, "w", encoding="utf-8") as f:
            f.write("\n\n---\n\n".join(assistant_messages))

        print(f"저장 완료: {all_text_path}")
        print(f"총 {len(assistant_messages)}개의 ChatGPT 응답 추출됨")

    return assistant_messages


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
        print("사용법: python chatgpt_parser.py <conversations.json 경로> [출력 폴더]")
        print("")
        print("예시:")
        print("  python chatgpt_parser.py ./conversations.json ./samples/chatgpt")
        sys.exit(1)

    json_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "./samples/chatgpt"

    messages = parse_conversations(json_path, output_dir)

    # Also save filtered by language
    output_path = Path(output_dir)

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
