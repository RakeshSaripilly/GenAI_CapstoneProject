from llm_config import llm, with_retry


@with_retry
def research_agent(topic):
    """Research agent with retry logic"""
    prompt = f"""
    Research the topic:

    {topic}

    Provide:
    1. Key Facts
    2. Statistics
    3. Important Points
    """

    try:
        result = llm.invoke(prompt)
        return result.content
    except Exception as e:
        raise Exception(f"Research agent failed: {str(e)}")