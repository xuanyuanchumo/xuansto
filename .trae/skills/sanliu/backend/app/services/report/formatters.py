from typing import List


class ProgressBarGenerator:
    @staticmethod
    def generate(percentage: float, length: int = 10) -> str:
        filled = int(percentage / (100 / length))
        empty = length - filled
        return "█" * filled + "░" * empty


class MarkdownFormatter:
    @staticmethod
    def heading(text: str, level: int = 1) -> str:
        return "#" * level + " " + text

    @staticmethod
    def bold(text: str) -> str:
        return f"**{text}**"

    @staticmethod
    def list_item(text: str) -> str:
        return f"- {text}"

    @staticmethod
    def numbered_item(index: int, text: str) -> str:
        return f"{index}. {text}"

    @staticmethod
    def table_header(columns: List[str]) -> str:
        return "| " + " | ".join(columns) + " |"

    @staticmethod
    def table_separator(count: int) -> str:
        return "|" + "|".join(["------" for _ in range(count)]) + "|"

    @staticmethod
    def table_row(values: List[str]) -> str:
        return "| " + " | ".join(values) + " |"

    @staticmethod
    def horizontal_rule() -> str:
        return "---"
