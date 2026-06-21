def evaluate(content):

    words = len(content.split())

    score = 0

    if words > 300:
        score += 50

    if words > 600:
        score += 50

    return {
        "word_count": words,
        "score": score
    }