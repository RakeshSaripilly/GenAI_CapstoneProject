from llm_config import llm, with_retry


@with_retry
def writer_agent(research):
    """Writer agent with retry logic"""
    prompt = f"""
    Write a detailed article from:

    {research}

    Include:
    - Introduction
    - Main Content
    - Conclusion
    """

    try:
        result = llm.invoke(prompt)
        return result.content
    except Exception as e:
        raise Exception(f"Writer agent failed: {str(e)}")