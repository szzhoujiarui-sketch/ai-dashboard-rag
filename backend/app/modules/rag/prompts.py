from langchain.prompts import PromptTemplate

QA_PROMPT = PromptTemplate(
    template="""基于以下上下文信息回答问题。如果上下文中没有答案，请说"我不知道"，不要编造答案。

上下文:
{context}

问题: {question}

回答:""",
    input_variables=["context", "question"]
)

SUMMARIZE_PROMPT = PromptTemplate(
    template="""请总结以下文档内容:

{document}

总结:""",
    input_variables=["document"]
)
