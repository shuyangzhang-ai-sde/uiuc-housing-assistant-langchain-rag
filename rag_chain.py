# rag_chain.py
# Retriever + LLM chain for UIUC housing search (Green Street Realty data)
#
# Run:    python rag_chain.py
# Output: prints answers to a set of real-case student test questions

from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

CHROMA_DIR  = "./chroma_db"
EMBED_MODEL = "all-MiniLM-L6-v2"
LLM_MODEL   = "llama3.1:8b"

# ── Load vector store ─────────────────────────────────────────────────────────
embeddings  = HuggingFaceEmbeddings(model_name=EMBED_MODEL)
vectorstore = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)

# k=6: retrieve 6 candidates so the LLM has enough to pick the best 5
retriever = vectorstore.as_retriever(search_kwargs={"k": 6})


# ── Prompt template ───────────────────────────────────────────────────────────
PROMPT_TEMPLATE = """
You are a UIUC housing assistant. All listings below are from Green Street Realty in Champaign, IL.

Use ONLY the listings provided. Do not invent addresses, prices, or availability.

────────────────────────────────────────
LISTINGS:
{context}
────────────────────────────────────────

STUDENT QUESTION:
{question}

────────────────────────────────────────
INSTRUCTIONS:

1. For each relevant listing, respond in this exact format:

   📍 [Full address]
   🛏  [Unit type] · [X] bed / [X] bath
   💰 $[price]/bed/mo · $[total]/mo total
      (if the original price was a range, show it as $875–$900/bed)
   📅 [Availability]
   📍 Area: [on-campus / downtown / etc.]
   🔗 [URL]

2. Price range rule:
   - If a listing's price range HIGH end exceeds the student's stated budget,
     add this note below that listing:
     ⚠️  Price range — some configurations may exceed your budget. Verify before applying.

3. Sort order: show available listings first, leased listings last.

4. If fewer than 3 listings match, say so honestly rather than padding with irrelevant ones.

5. End your response with a one-line summary, e.g.:
   "Found 3 available listings within your budget — 1 may partially exceed it."
────────────────────────────────────────
"""

prompt = PromptTemplate.from_template(PROMPT_TEMPLATE)
llm    = ChatOllama(model=LLM_MODEL)


# ── Chain ─────────────────────────────────────────────────────────────────────
def format_docs(docs):
    return "\n\n---\n\n".join([d.page_content for d in docs])

chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)


# ── Real-case student test questions ──────────────────────────────────────────
# These reflect the kinds of questions actual UIUC students ask during housing season.
TEST_QUESTIONS = [
    # Budget-constrained search
    "I'm looking for a 2 bedroom apartment under $900/bed per month. What's available?",

    # Small budget, solo student
    "What are the cheapest available 1 bedroom apartments near campus right now?",

    # Group housing
    "Me and 3 friends need a 4 bedroom. What are our options and what's the total monthly cost?",

    # Location preference
    "I want to live downtown. What 1BR or 2BR apartments are available?",

    # Roommate match
    "I don't have roommates yet. Are there any places with a roommate matching program?",

    # Availability window
    "What units are available for move-in August 2026?",
]

if __name__ == "__main__":
    for i, question in enumerate(TEST_QUESTIONS, 1):
        print(f"\n{'='*65}")
        print(f"Q{i}: {question}")
        print(f"{'='*65}")
        answer = chain.invoke(question)
        print(answer)
