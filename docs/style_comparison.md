# Style Comparison: default prompt vs few-shot 'concise' specialization

Model: `llama3.1:8b`, temperature 0, seed 7. 5 queries x top 3 songs. Only explanations actually written by the LLM and accepted by the grounding guardrail are counted.

| Metric | default | concise |
|---|---|---|
| Explanations measured | 15 | 15 |
| Average words | 28.3 | 11.4 |
| Exactly one sentence | 80% | 100% |
| At most 18 words | 0% | 100% |
| States low/medium/high energy | 53% | 100% |
| No filler phrases | 13% | 100% |
