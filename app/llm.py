from __future__ import annotations

from typing import Iterable

from .config import settings


SYSTEM_PROMPT = """あなたはDiscord内で働く秘書AIです。
日本語で、短く、具体的に答えてください。
できるだけ箇条書きは少なくしてください。
依頼内容を整理し、実務で使える形にしてください。
分からないことは分からないと書き、勝手に断定しないでください。"""


def complete(prompt: str) -> str:
    provider = settings.llm_provider
    if provider == "anthropic":
        return _anthropic_complete(prompt)
    return _openai_complete(prompt)


def _openai_complete(prompt: str) -> str:
    from openai import OpenAI

    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY が未設定です")

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.responses.create(
        model=settings.model_name,
        input=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    return response.output_text.strip()


def _anthropic_complete(prompt: str) -> str:
    import anthropic

    if not settings.anthropic_api_key:
        raise RuntimeError("ANTHROPIC_API_KEY が未設定です")

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
    message = client.messages.create(
        model=settings.model_name,
        max_tokens=1200,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )
    parts: list[str] = []
    for block in message.content:
        text = getattr(block, "text", None)
        if text:
            parts.append(text)
    return "\n".join(parts).strip()


def compose_research_prompt(topic: str) -> str:
    return (
        f"次のテーマを短く調べてください。\n"
        f"テーマ: {topic}\n\n"
        "出力ルール:\n"
        "1. 何が大事か\n"
        "2. すぐ使える示唆\n"
        "3. 投稿や企画にするとしたら何を書くか\n"
        "4. 100文字前後の結論\n"
    )


def compose_knowledge_prompt(question: str, sources: Iterable[tuple[str, str]]) -> str:
    joined = "\n\n".join([f"資料名: {name}\n内容: {snippet}" for name, snippet in sources])
    return (
        f"質問: {question}\n\n"
        "下の社内資料だけをもとに答えてください。\n"
        "資料にないことは、資料にないと書いてください。\n\n"
        f"{joined}"
    )
