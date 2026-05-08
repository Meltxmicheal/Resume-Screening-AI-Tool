def get_similarity(text1, text2):
    text1 = (text1 or '').lower()
    text2 = (text2 or '').lower()

    words1 = set(text1.split())
    words2 = set(text2.split())

    if not words1 or not words2:
        return 0.0

    return len(words1 & words2) / len(words1 | words2)
