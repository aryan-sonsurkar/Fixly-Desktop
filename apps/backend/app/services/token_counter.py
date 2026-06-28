class TokenCounter:
    @staticmethod
    def count_tokens(text: str) -> int:
        return max(1, len(text.split()))
