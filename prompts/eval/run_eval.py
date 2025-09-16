import pandas as pd
import json
import re
from backend import rag_query  # assume you wrap your RAG pipeline in rag_query()

df = pd.read_csv("eval/golden_set.csv")
results = []

for _, row in df.iterrows():
    answer, sources = rag_query(row["query"])
    match = row["expected_answer"].lower() in answer.lower()
    source_match = row["expected_source"].lower() in " ".join(sources).lower()
    results.append({
        "query": row["query"],
        "got_answer": match,
        "got_source": source_match,
        "answer": answer,
        "sources": sources
    })

pd.DataFrame(results).to_csv("eval/results.csv", index=False)
print("Evaluation complete. Results saved to eval/results.csv")
