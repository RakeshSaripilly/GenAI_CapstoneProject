from llm_config import llm, with_retry


@with_retry
def editor_agent(article):
    """Editor agent with retry logic"""
    prompt = f"""
    Improve the article.

    Fix:
    - Grammar
    - Structure
    - Readability

    Article:
    {article}
    """

    try:
        result = llm.invoke(prompt)
        return result.content
    except Exception as e:
        raise Exception(f"Editor agent failed: {str(e)}")