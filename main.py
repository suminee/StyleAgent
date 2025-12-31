"""CLI interface for Style Agent"""
import click
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from config import SAMPLES_DIR, STYLE_PROFILE_DIR, ANTHROPIC_API_KEY
from doc_parser import load_sample_documents, extract_text_from_docx, extract_text_from_txt
from style_analyzer import StyleAnalyzer
from writing_agent import WritingAgent

console = Console()


@click.group()
def cli():
    """Style Agent - 당신처럼 글 쓰는 AI 에이전트"""
    pass


def _load_texts_from_source(source_path: Path) -> list:
    """Helper to load texts from file or directory"""
    texts = []

    if source_path.is_file():
        if source_path.suffix.lower() == ".docx":
            texts.append(extract_text_from_docx(str(source_path)))
        elif source_path.suffix.lower() == ".txt":
            texts.append(extract_text_from_txt(str(source_path)))
    elif source_path.is_dir():
        docs = load_sample_documents(str(source_path))
        texts = [doc["content"] for doc in docs]

    return texts


@cli.command()
@click.argument("source", type=click.Path(exists=True))
@click.option("--profile-name", "-n", default="default", help="저장할 프로필 이름")
def learn(source: str, profile_name: str):
    """샘플 문서에서 글쓰기 스타일 학습

    SOURCE: 학습할 문서 파일 또는 폴더 경로
    """
    console.print(Panel("[bold blue]스타일 학습 시작[/bold blue]"))

    source_path = Path(source)
    texts = []

    if source_path.is_file():
        # Single file
        console.print(f"파일 로드 중: {source_path.name}")
        if source_path.suffix.lower() == ".docx":
            texts.append(extract_text_from_docx(str(source_path)))
        elif source_path.suffix.lower() == ".txt":
            texts.append(extract_text_from_txt(str(source_path)))
        else:
            console.print(f"[red]지원하지 않는 파일 형식: {source_path.suffix}[/red]")
            return
    elif source_path.is_dir():
        # Directory
        console.print(f"폴더 스캔 중: {source_path}")
        docs = load_sample_documents(str(source_path))
        texts = [doc["content"] for doc in docs]
        console.print(f"  - {len(docs)}개 문서 로드됨")

    if not texts:
        console.print("[red]학습할 문서가 없습니다.[/red]")
        return

    # Analyze style
    console.print("스타일 분석 중...")
    analyzer = StyleAnalyzer()
    profile = analyzer.analyze(texts)

    # Save profile
    profile_path = STYLE_PROFILE_DIR / f"{profile_name}.json"
    analyzer.save_profile(str(profile_path))
    console.print(f"[green]프로필 저장됨: {profile_path}[/green]")

    # Save sample texts for context
    samples_path = STYLE_PROFILE_DIR / f"{profile_name}_samples.txt"
    with open(samples_path, "w", encoding="utf-8") as f:
        f.write("\n\n---\n\n".join(texts))

    # Show summary
    console.print("\n")
    console.print(Markdown(analyzer.get_style_summary()))


@cli.command("learn-append")
@click.argument("source", type=click.Path(exists=True))
@click.option("--profile-name", "-n", default="default", help="업데이트할 프로필 이름")
def learn_append(source: str, profile_name: str):
    """기존 프로필에 새로운 데이터 추가 학습 (점진적 학습)

    SOURCE: 추가 학습할 문서 파일 또는 폴더 경로
    """
    console.print(Panel("[bold cyan]점진적 학습 시작[/bold cyan]"))

    # Check if profile exists
    profile_path = STYLE_PROFILE_DIR / f"{profile_name}.json"
    samples_path = STYLE_PROFILE_DIR / f"{profile_name}_samples.txt"

    if not profile_path.exists():
        console.print(f"[yellow]기존 프로필이 없습니다. 새로 생성합니다: {profile_name}[/yellow]")
        existing_profile = None
        existing_samples = []
    else:
        console.print(f"기존 프로필 로드: {profile_name}")
        analyzer = StyleAnalyzer()
        existing_profile = analyzer.load_profile(str(profile_path))

        # Load existing samples
        if samples_path.exists():
            with open(samples_path, "r", encoding="utf-8") as f:
                existing_samples = f.read().split("\n\n---\n\n")
        else:
            existing_samples = []

        old_docs = existing_profile.get("metadata", {}).get("total_documents", 0)
        old_chars = existing_profile.get("metadata", {}).get("total_characters", 0)
        console.print(f"  - 기존: {old_docs}개 문서, {old_chars:,}자")

    # Load new texts
    source_path = Path(source)
    texts = _load_texts_from_source(source_path)

    if source_path.is_file():
        console.print(f"새 파일 로드: {source_path.name}")
    elif source_path.is_dir():
        console.print(f"새 폴더 스캔: {source_path}")
        console.print(f"  - {len(texts)}개 문서 로드됨")

    if not texts:
        console.print("[red]추가 학습할 문서가 없습니다.[/red]")
        return

    # Analyze new texts
    console.print("새 데이터 분석 중...")
    analyzer = StyleAnalyzer()
    new_profile = analyzer.analyze(texts)

    new_docs = new_profile.get("metadata", {}).get("total_documents", 0)
    new_chars = new_profile.get("metadata", {}).get("total_characters", 0)
    console.print(f"  - 새로운: {new_docs}개 문서, {new_chars:,}자")

    # Merge profiles
    if existing_profile:
        console.print("프로필 병합 중...")
        merged_profile = analyzer.merge_profiles(existing_profile, new_profile)
    else:
        merged_profile = new_profile

    # Save merged profile
    analyzer.style_profile = merged_profile
    analyzer.save_profile(str(profile_path))

    total_docs = merged_profile.get("metadata", {}).get("total_documents", 0)
    total_chars = merged_profile.get("metadata", {}).get("total_characters", 0)
    console.print(f"[green]프로필 업데이트 완료: {total_docs}개 문서, {total_chars:,}자[/green]")

    # Append new samples (keep recent ones)
    combined_samples = texts + existing_samples
    max_samples = 100  # Keep last 100 samples
    with open(samples_path, "w", encoding="utf-8") as f:
        f.write("\n\n---\n\n".join(combined_samples[:max_samples]))

    console.print(f"[green]샘플 텍스트 업데이트: {min(len(combined_samples), max_samples)}개 보관[/green]")

    # Show summary
    console.print("\n")
    console.print(Markdown(analyzer.get_style_summary()))


@cli.command()
@click.option("--profile-name", "-n", default="default", help="사용할 프로필 이름")
@click.option("--doc-type", "-t", default="일반 문서", help="문서 종류 (이메일, 보고서, 제안서 등)")
@click.option("--length", "-l", type=click.Choice(["short", "medium", "long"]), default="medium")
def write(profile_name: str, doc_type: str, length: str):
    """새로운 글 초안 작성

    대화형으로 주제를 입력받아 글을 작성합니다.
    """
    if not ANTHROPIC_API_KEY:
        console.print("[red]ANTHROPIC_API_KEY가 설정되지 않았습니다.[/red]")
        console.print("  .env 파일에 ANTHROPIC_API_KEY를 설정해주세요.")
        return

    # Load profile
    profile_path = STYLE_PROFILE_DIR / f"{profile_name}.json"
    samples_path = STYLE_PROFILE_DIR / f"{profile_name}_samples.txt"

    if not profile_path.exists():
        console.print(f"[red]프로필을 찾을 수 없습니다: {profile_name}[/red]")
        console.print("  먼저 'learn' 명령어로 스타일을 학습해주세요.")
        return

    analyzer = StyleAnalyzer()
    profile = analyzer.load_profile(str(profile_path))

    sample_texts = []
    if samples_path.exists():
        with open(samples_path, "r", encoding="utf-8") as f:
            sample_texts = f.read().split("\n\n---\n\n")

    console.print(Panel(f"[bold green]글쓰기 모드[/bold green] - 프로필: {profile_name}"))

    # Get topic
    topic = click.prompt("작성할 글의 주제를 입력하세요")
    context = click.prompt("추가 맥락이나 포함할 내용 (없으면 Enter)", default="", show_default=False)

    console.print("\n[dim]글 작성 중...[/dim]\n")

    # Generate
    agent = WritingAgent(profile, sample_texts)
    result = agent.write(
        topic=topic,
        context=context if context else None,
        doc_type=doc_type,
        length=length
    )

    console.print(Panel(result, title="[bold]작성된 글[/bold]", border_style="green"))


@cli.command()
@click.option("--profile-name", "-n", default="default", help="사용할 프로필 이름")
def rewrite(profile_name: str):
    """기존 글을 내 스타일로 다시 작성"""
    if not ANTHROPIC_API_KEY:
        console.print("[red]ANTHROPIC_API_KEY가 설정되지 않았습니다.[/red]")
        return

    # Load profile
    profile_path = STYLE_PROFILE_DIR / f"{profile_name}.json"
    samples_path = STYLE_PROFILE_DIR / f"{profile_name}_samples.txt"

    if not profile_path.exists():
        console.print(f"[red]프로필을 찾을 수 없습니다: {profile_name}[/red]")
        return

    analyzer = StyleAnalyzer()
    profile = analyzer.load_profile(str(profile_path))

    sample_texts = []
    if samples_path.exists():
        with open(samples_path, "r", encoding="utf-8") as f:
            sample_texts = f.read().split("\n\n---\n\n")

    console.print(Panel(f"[bold yellow]다시 쓰기 모드[/bold yellow] - 프로필: {profile_name}"))

    console.print("원본 글을 입력하세요 (입력 완료 후 빈 줄에서 Enter 두 번):")
    lines = []
    empty_count = 0
    while empty_count < 2:
        line = input()
        if line == "":
            empty_count += 1
        else:
            empty_count = 0
            lines.append(line)
    original_text = "\n".join(lines)

    instructions = click.prompt("추가 지시사항 (없으면 Enter)", default="", show_default=False)

    console.print("\n[dim]다시 쓰는 중...[/dim]\n")

    agent = WritingAgent(profile, sample_texts)
    result = agent.rewrite(original_text, instructions if instructions else None)

    console.print(Panel(result, title="[bold]다시 작성된 글[/bold]", border_style="yellow"))


@cli.command()
def profiles():
    """저장된 스타일 프로필 목록"""
    console.print(Panel("[bold]저장된 프로필[/bold]"))

    profile_files = list(STYLE_PROFILE_DIR.glob("*.json"))

    if not profile_files:
        console.print("저장된 프로필이 없습니다.")
        console.print("  'learn' 명령어로 새 프로필을 만들어주세요.")
        return

    for pf in profile_files:
        name = pf.stem
        console.print(f"  - {name}")


@cli.command()
@click.argument("profile-name")
def show(profile_name: str):
    """특정 프로필의 스타일 분석 결과 표시"""
    profile_path = STYLE_PROFILE_DIR / f"{profile_name}.json"

    if not profile_path.exists():
        console.print(f"[red]프로필을 찾을 수 없습니다: {profile_name}[/red]")
        return

    analyzer = StyleAnalyzer()
    analyzer.load_profile(str(profile_path))

    console.print(Markdown(analyzer.get_style_summary()))


@cli.command()
@click.argument("profile-name")
@click.option("--output", "-o", default=None, help="출력 파일 경로 (기본: profiles/{name}_style_guide.md)")
def export(profile_name: str, output: str):
    """Claude Projects용 스타일 가이드 문서 생성

    웹/모바일 Claude에서 사용할 수 있는 마크다운 문서를 생성합니다.
    """
    import json

    profile_path = STYLE_PROFILE_DIR / f"{profile_name}.json"
    samples_path = STYLE_PROFILE_DIR / f"{profile_name}_samples.txt"

    if not profile_path.exists():
        console.print(f"[red]프로필을 찾을 수 없습니다: {profile_name}[/red]")
        return

    with open(profile_path, "r", encoding="utf-8") as f:
        profile = json.load(f)

    # Load samples
    sample_texts = []
    if samples_path.exists():
        with open(samples_path, "r", encoding="utf-8") as f:
            sample_texts = f.read().split("\n\n---\n\n")[:20]  # Keep 20 samples

    # Generate style guide document
    doc = _generate_style_guide(profile_name, profile, sample_texts)

    # Output path
    if output:
        output_path = Path(output)
    else:
        output_path = STYLE_PROFILE_DIR / f"{profile_name}_style_guide.md"

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(doc)

    console.print(f"[green]스타일 가이드 생성 완료: {output_path}[/green]")
    console.print("\n[bold]사용 방법:[/bold]")
    console.print("1. Claude 웹/앱에서 새 Project 생성")
    console.print("2. Project Knowledge에 이 파일 업로드")
    console.print("3. '내 스타일로 글 써줘'라고 요청")


def _generate_style_guide(name: str, profile: dict, samples: list) -> str:
    """Generate a comprehensive style guide document for Claude Projects"""
    lines = []

    # Header
    lines.append(f"# {name.upper()} 글쓰기 스타일 가이드")
    lines.append("")
    lines.append("> 이 문서는 사용자의 글쓰기 스타일을 분석한 결과입니다.")
    lines.append("> 글을 작성할 때 이 가이드를 참고하여 사용자의 스타일을 따라주세요.")
    lines.append("")

    # Metadata
    meta = profile.get("metadata", {})
    lines.append("## 분석 기반 데이터")
    lines.append(f"- 분석 문서 수: {meta.get('total_documents', 0):,}개")
    lines.append(f"- 총 문자 수: {meta.get('total_characters', 0):,}자")
    lines.append("")

    # Core style guidelines
    lines.append("## 핵심 스타일 가이드라인")
    lines.append("")

    # Sentence style
    ss = profile.get("sentence_stats", {})
    avg_len = ss.get("avg_length_chars", 100)
    if avg_len < 80:
        lines.append("### 문장 길이: 짧고 간결하게")
        lines.append("- 평균 문장 길이: 약 80자 이하")
        lines.append("- 짧고 명확한 문장을 선호합니다")
    elif avg_len < 150:
        lines.append("### 문장 길이: 적당한 길이")
        lines.append(f"- 평균 문장 길이: 약 {avg_len:.0f}자")
        lines.append("- 너무 짧지도, 너무 길지도 않은 적당한 문장을 선호합니다")
    else:
        lines.append("### 문장 길이: 상세한 설명")
        lines.append(f"- 평균 문장 길이: 약 {avg_len:.0f}자")
        lines.append("- 충분한 설명이 담긴 긴 문장도 자주 사용합니다")
    lines.append("")

    # Tone
    tone = profile.get("tone_analysis", {})
    lines.append("### 톤 & 격식")

    if name == "korean" or "korean" in name.lower():
        kr_form = tone.get("korean_formality", {})
        kr_tone = tone.get("primary_korean_tone", "formal")
        if kr_tone == "formal":
            lines.append("- **격식체 사용**: -습니다/-입니다 형태의 존댓말")
            lines.append(f"  - 격식체 사용: {kr_form.get('formal_high', 0):,}회")
        else:
            lines.append("- **비격식체/해요체 사용**: 친근하면서도 공손한 톤")
            lines.append(f"  - 해요체 사용: {kr_form.get('formal_polite', 0):,}회")
    else:
        en_form = tone.get("english_formality", {})
        en_tone = tone.get("primary_english_tone", "formal")
        if en_tone == "formal":
            lines.append("- **Formal/Professional tone**")
            lines.append("- Use polite, professional language")
        else:
            lines.append("- **Casual/Friendly tone**")
            lines.append("- Conversational but respectful")

    emotional = tone.get("emotional_indicators", {})
    if emotional.get("enthusiastic", 0) > emotional.get("cautious", 0):
        lines.append("- 열정적이고 긍정적인 톤 선호")
    if emotional.get("direct", 0) > 500:
        lines.append("- 직접적이고 명확한 표현 사용")
    lines.append("")

    # Opening patterns
    opening = profile.get("opening_patterns", {})
    lines.append("### 시작 패턴")
    first_phrases = opening.get("common_first_phrases", [])[:5]
    if first_phrases:
        lines.append("자주 사용하는 시작 표현:")
        for phrase, count in first_phrases:
            if count > 50:  # Only significant patterns
                lines.append(f"- \"{phrase}\"")
    greetings = opening.get("greeting_patterns", {})
    if greetings:
        top_greeting = max(greetings.items(), key=lambda x: x[1])
        if top_greeting[1] > 10:
            lines.append(f"- 주요 인사말: \"{top_greeting[0]}\"")
    lines.append("")

    # Closing patterns
    closing = profile.get("closing_patterns", {})
    lines.append("### 마무리 패턴")
    signoffs = closing.get("signoff_patterns", {})
    if signoffs:
        sorted_signoffs = sorted(signoffs.items(), key=lambda x: x[1], reverse=True)[:3]
        lines.append("자주 사용하는 마무리 표현:")
        for signoff, count in sorted_signoffs:
            if count > 5:
                lines.append(f"- \"{signoff}\"")
    lines.append("")

    # Structure
    struct = profile.get("structural_patterns", {})
    patterns = struct.get("patterns", {})
    counts = struct.get("counts", {})
    lines.append("### 구조적 특징")
    if patterns.get("uses_bullet_points"):
        lines.append(f"- **불릿 포인트 사용**: 자주 사용 ({counts.get('bullet_count', 0):,}회)")
    if patterns.get("uses_numbering"):
        lines.append(f"- **번호 목록 사용**: 사용 ({counts.get('number_count', 0):,}회)")
    if patterns.get("uses_headers"):
        lines.append(f"- **헤더/제목 사용**: 사용 ({counts.get('header_count', 0):,}회)")
    if patterns.get("uses_bold"):
        lines.append("- **굵은 글씨 강조**: 중요 내용에 **bold** 사용")
    if patterns.get("uses_tables"):
        lines.append("- **표 사용**: 데이터 정리에 표 활용")
    lines.append("")

    # Transition words
    trans = profile.get("transition_analysis", {})
    lines.append("### 연결어/전환어")
    if name == "korean" or "korean" in name.lower():
        kr_trans = trans.get("top_korean_transitions", [])[:7]
        if kr_trans:
            trans_str = ", ".join([f"\"{t[0]}\"" for t in kr_trans if t[1] > 10])
            if trans_str:
                lines.append(f"자주 사용하는 연결어: {trans_str}")
    else:
        en_trans = trans.get("top_english_transitions", [])[:7]
        if en_trans:
            trans_str = ", ".join([f"\"{t[0]}\"" for t in en_trans if t[1] > 50])
            if trans_str:
                lines.append(f"Frequently used transitions: {trans_str}")
    lines.append("")

    # Signature phrases
    sig = profile.get("signature_phrases", {})
    bigrams = sig.get("signature_bigrams", [])[:10]
    trigrams = sig.get("signature_trigrams", [])[:5]
    if bigrams or trigrams:
        lines.append("### 시그니처 표현")
        lines.append("이 사용자가 자주 쓰는 특징적인 표현:")
        for phrase, count in bigrams[:7]:
            if count > 100 and not phrase.startswith("entity"):  # Filter noise
                lines.append(f"- \"{phrase}\"")
        lines.append("")

    # Sample sentences
    if samples:
        lines.append("## 스타일 참고 예시")
        lines.append("실제 작성된 글의 예시입니다. 이러한 톤과 스타일을 참고하세요:")
        lines.append("")
        for i, sample in enumerate(samples[:10], 1):
            # Clean and truncate sample
            clean_sample = sample.strip()[:500]
            if len(sample) > 500:
                clean_sample += "..."
            lines.append(f"### 예시 {i}")
            lines.append("```")
            lines.append(clean_sample)
            lines.append("```")
            lines.append("")

    # Instructions for Claude
    lines.append("---")
    lines.append("")
    lines.append("## Claude에게 보내는 지시사항")
    lines.append("")
    lines.append("글을 작성할 때 위의 스타일 가이드를 따라주세요:")
    lines.append("1. 문장 길이와 구조를 맞춰주세요")
    lines.append("2. 톤과 격식 수준을 일관되게 유지해주세요")
    lines.append("3. 시작/마무리 패턴을 참고해주세요")
    lines.append("4. 시그니처 표현을 자연스럽게 활용해주세요")
    lines.append("5. 구조적 특징(불릿, 헤더 등)을 비슷하게 사용해주세요")
    lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    cli()
