# AI Interactions Log

This log explains how I used AI assistance throughout the assignment. I used Claude Code as a learning and development assistant while working in my repository. My main use of AI was to explore implementation ideas, understand unfamiliar concepts, troubleshoot errors, and get suggestions for improving my project. I wrote and implemented the code myself, tested the functionality, and made the final decisions about the project.

## Capstone: Where AI Was Used, by Assignment Part

| Assignment part | How AI helped me | What I did |
|---|---|---|
| **Step 0: Repository setup** (Module 3 repo, folder structure, virtual environment) | Claude helped me understand the Git commands, recommended a folder structure, and guided me through setting up the Python environment when I needed help. | I created the GitHub repository, chose my Module 3 music recommender as the starting point, organized the project files, and set up the development environment. |
| **Architecture diagram** (`diagrams/architecture.mmd`) | Claude suggested ways to represent the system components and helped me understand how to organize the workflow in a Mermaid diagram. | I designed the system workflow and made sure the diagram accurately represented how my implementation works. |
| **Core AI feature: Retrieval-Augmented Recommendation** (`src/retriever.py`, `src/rag.py`, `data/knowledge_base.json`) | Claude helped me understand how RAG works, suggested possible retrieval approaches, and guided me when I had implementation questions or errors. | I decided to extend my existing music recommender, designed the offline approach without requiring an API key, wrote the code, and integrated retrieval with my existing scoring system. |
| **Guardrails, logging, and reliability testing** (`src/guardrails.py`, `tests/`, `src/evaluate.py`) | Claude suggested test scenarios, helped me interpret unexpected results, and provided debugging guidance when the system did not behave as expected. | I implemented the guardrails and tests, ran different queries, identified problems, and updated my implementation to handle negation, multiple genres, spelling variations, and safety-related inputs. |
| **Stretch features** (second data source, agent loop, evaluation harness) | Claude explained different ways to implement an agentic workflow and suggested approaches for handling retries, tool calls, and evaluation. | I selected the stretch features I wanted to include, implemented them, and tested the agent's behavior with different user queries. |
| **Documentation** (README, model card, portfolio entry, presentation outline) | Claude helped me organize the documentation, suggested clearer explanations, and assisted with grammar and wording. | I documented my implementation, reviewed the descriptions against the actual project results, and wrote my reflections and conclusions based on what I learned. |

**Parts that did not require AI assistance:** Choosing the original project, deciding the overall direction, writing and integrating the code, reviewing the final implementation, and preparing to present and explain my work.

## Where AI Suggestions Did Not Work and How I Fixed the Problems

During development, I encountered several issues where AI suggestions were incomplete or did not solve the problem. I used testing and debugging to understand what was happening.

- **Knowledge-base issue:** I noticed that ten knowledge-base entries contained empty text. I checked the generated data and found an issue in the script. I corrected it before continuing with the retrieval system.
- **Agent recovery issue:** The initial approach for handling unknown words was not improving the results because the retriever already ignored those words. After testing different queries, I changed the recovery approach to use spelling correction instead.
- **Retrieval threshold issue:** Some unrelated songs appeared in the recommendations for simple queries such as studying. I tested the retrieval results and adjusted the threshold to make the recommendations more relevant.
- **Testing limitations:** Although the first test suite passed all 13 tests, I discovered additional issues by manually trying different prompts. These included negation, mixed-genre requests, word-form differences, and safety-related inputs. I improved the implementation and expanded the testing based on those findings.

These experiences helped me understand why passing automated tests is not always enough. I learned to check the system with realistic user queries and verify whether suggested fixes actually improved the results.

## Examples of How I Used Claude Code

Most of my interactions with Claude were related to understanding concepts, implementation guidance, and debugging. Some examples of my questions and requests were:

- How can I add RAG to my existing music recommendation system?
- How should I organize the repository and Python files?
- Can you explain why this part of my code is producing an error?
- How can I improve retrieval accuracy?
- How should I handle queries containing negation or multiple genres?
- What additional test cases should I consider?
- How can I implement an agent workflow with retries and tool traces?
- Can you help me make my documentation clearer?

I used the explanations and suggestions to guide my implementation rather than relying on AI outputs without checking them.

## Earlier Origin: Module 3 (VibeFinder 1.0)

My capstone extends my Module 3 project, VibeFinder 1.0, a music recommendation simulation.

During Module 3, I also used AI as a learning assistant. It helped me think through feature selection, scoring logic, recommendation functions, stress-testing scenarios, and bias analysis.

I implemented and tested the recommendation functions, including `load_songs`, `score_song`, and `recommend_songs`. I also ran `python -m src.main` and `pytest` to verify the results.

One useful learning experience was the weight-shift experiment. The AI initially suggested an outcome without verifying the calculations. Instead of accepting the explanation, I checked the results with an actual script and found that the initial prediction was incorrect.

This reminded me of the importance of testing and independently validating AI suggestions.

The earlier work is documented in `vibefinder_1_0_readme.md` and sections 1–7 of `model_card.md`.

## Reflection on AI Use

I mainly used Claude Code as a coding assistant and learning resource. It was helpful when I needed to understand a new concept, explore possible solutions, or debug an issue that I could not immediately identify.

However, I did not assume that every suggestion was correct. I tested my implementation, compared results, and made changes when something was not working.

One of the most important things I learned from this project is that **AI can be useful for guidance and debugging, but understanding the code and verifying the results are still my responsibility.**

The final implementation reflects my design choices, coding work, testing, and the improvements I made throughout the development process.
