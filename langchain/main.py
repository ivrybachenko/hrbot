from fastapi import FastAPI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate

from elastic import elastic_vector_search
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
import time


class TimerMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response


app = FastAPI()

app.add_middleware(TimerMiddleware)
# Сорри за ужасный код, можно лучше гораздо, даже стыдно, но сейчас 5 утра. Не время делать что-то красиво!
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from elastic import elastic_vector_search

model_path = './models/saiga2'
n_ctx = 2000
top_k = 30
top_p = 0.9
temperature = 0.2
repeat_penalty = 1.1

from langchain.llms import LlamaCpp
from langchain.callbacks.manager import CallbackManager
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

n_batch = 512  # Should be between 1 and n_ctx, consider the amount of RAM of your Apple Silicon Chip.
callback_manager = CallbackManager([StreamingStdOutCallbackHandler()])
llm = LlamaCpp(
    model_path=model_path,
    n_batch=n_batch,
    n_ctx=2048,
    f16_kv=True,  # MUST set to True, otherwise you will run into problem after a couple of calls
    callback_manager=callback_manager,
    verbose=True,
)

B_INST, E_INST = "[INST]", "[/INST]"
B_SYS, E_SYS = "<<SYS>>\n", "\n<</SYS>>\n\n"
DEFAULT_SYSTEM_PROMPT = """\
Ты — Эйчар-бот SmartAI, русскоязычный автоматический ассистент. Ты разговариваешь с людьми и помогаешь им по их вопросам.
"""


@app.get("/")
def foo(query: str):
    # ищем похожие документы в количестве К штук
    docs = elastic_vector_search.similarity_search(query=query, k=7)[2:]
    docs = str([doc.page_content for doc in docs])
    print(docs)

    def get_prompt(instruction, new_system_prompt=DEFAULT_SYSTEM_PROMPT):
        SYSTEM_PROMPT = B_SYS + new_system_prompt + docs + E_SYS
        prompt_template = B_INST + SYSTEM_PROMPT + instruction + E_INST
        return prompt_template

    memory = ConversationBufferMemory(memory_key="chat_history")
    instruction = "Chat History:\n\n{chat_history} \n\nUser: {user_input}"
    system_prompt = "Ты — Эйчар-бот SmartAI, русскоязычный автоматический ассистент. Ты разговариваешь с людьми и помогаешь им по их вопросам."

    template = get_prompt(instruction, system_prompt)
    prompt = PromptTemplate(
        input_variables=["chat_history", "user_input"], template=template
    )
    llm_chain = LLMChain(
        llm=llm,
        prompt=prompt,
        verbose=True,
        memory=memory,
    )
    print(query)
    ans = llm_chain.predict(user_input=query)

    return {'answer': ans, 'found_relevant_docs': docs, 'memory': memory}
