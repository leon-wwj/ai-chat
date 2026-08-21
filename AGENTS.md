Project Agent Instructions
1. Project Overview

This project is a Vue 3 AI Chat application.

The current primary goal is to build a real, maintainable frontend project while using the project itself to deepen understanding of:

JavaScript
Vue 3
HTTP / REST API
Axios
Frontend engineering
Project structure
AI application development

The project is also intended to become the frontend foundation for later expansion into:

Python
FastAPI
MySQL / Redis
Linux / Docker
LLM APIs
Streaming responses
RAG
Embeddings
Vector databases
Agents

Do not prematurely introduce these future technologies into the current project unless explicitly requested.

2. Current Technology Constraints

Current stack:

Vue 3
Vite
JavaScript
Axios
npm

Important:

Use JavaScript, not TypeScript, unless explicitly requested.
Use Vue 3 Composition API.
Prefer <script setup>.
Do not migrate the project to TypeScript.
Do not replace Vue 3 or Vite with another frontend framework or build tool.

When uncertain about the exact installed version or available scripts, inspect package.json instead of guessing.

3. Development Principles
3.1 Prefer understanding over blind automation

This project is also a learning project.

When implementing a non-trivial feature:

Explain the intended approach before making large changes.
Prefer small, understandable changes.
Do not hide important architectural decisions.
Avoid generating large amounts of unnecessary code.
Preserve the project's existing structure whenever reasonable.

For simple, mechanical changes, implementation may proceed directly.

3.2 Do not over-engineer

Do not introduce:

unnecessary abstractions
unnecessary design patterns
unnecessary dependencies
unnecessary state-management libraries
unnecessary utility layers
unnecessary configuration

Prefer the simplest structure that is clean and maintainable.

Only introduce additional architecture when there is a real requirement.

4. Project Structure Principles

Follow the existing project structure.

Preferred responsibility separation:

components/: reusable UI components
views/: page-level components
api/: API request functions
utils/: reusable utility functions
constants/: shared constants
assets/: static frontend assets
router/: routing
other directories should only be introduced when their responsibility is clear

Do not place API request logic directly into large Vue components when the request can reasonably be separated into api/.

Do not create folders merely for the sake of architectural appearance.

5. API and HTTP Rules

Use Axios consistently for HTTP requests.

Prefer this separation:

Vue component
    ↓
API service
    ↓
Axios request layer
    ↓
Backend / external API


Do not mix unrelated responsibilities together.

For example:

API endpoint definitions belong in the API layer.
Axios instance configuration belongs in the request layer.
UI state belongs in Vue components or appropriate state-management code.
Constants should not be duplicated throughout the project.

When modifying an API contract, inspect all affected callers before changing it.

6. AI API and Security Rules

Never hard-code API keys into source code.

Never place secrets directly into:

.vue
.js
.ts
README.md
committed configuration files

Do not expose API keys in frontend code unless the architecture explicitly requires it and the security implications have been explained.

Prefer environment variables or the appropriate server-side configuration mechanism.

Never commit secrets to Git.

If a secret appears in tracked files, stop and point it out before making further changes.

7. Dependency Rules

Before adding a new dependency:

Determine whether the existing project can solve the problem without it.
Prefer existing dependencies when reasonable.
Avoid adding libraries for small tasks.
Explain the reason for a new dependency.

Do not upgrade or replace major dependencies without an explicit reason.

Do not modify package versions merely to "clean up" the project.

8. Git Rules

Preserve the existing Git history and repository structure.

Do not:

delete .git
reinitialize the repository
reset or rewrite history
force-push
discard unrelated user changes

Before making broad changes, inspect the current repository status when appropriate.

Keep changes focused on the requested task.

9. Validation Rules

After modifying code, validate the result whenever practical.

Prefer:

inspect the affected files
run the project's existing validation/build/lint commands if available
verify the runtime behavior
report any remaining errors

Do not invent commands.

Read package.json and existing project configuration to determine available scripts.

If a validation step cannot be performed, state that clearly.

10. Error Handling

When debugging, find the earliest/root error first.

Do not blindly fix hundreds of downstream console errors one by one.

Prioritize:

first meaningful error
source file
stack trace
network request
failed dependency
runtime state

Fix the likely root cause and then re-check the remaining errors.

11. Change Scope

Default behavior:

Make the smallest reasonable change.
Do not refactor unrelated code.
Do not rename files or concepts without a clear reason.
Do not change architecture merely because another architecture is possible.
Preserve working behavior outside the requested change.

If a larger refactor is genuinely necessary, explain why before making it.

12. Learning-Oriented Behavior

This is a learning-oriented project.

When implementing an important feature, prefer briefly identifying:

what is being changed
why it is being changed
which layer owns the responsibility
what important JavaScript / Vue / HTTP concept is involved

Do not explain every obvious line of code.

At major milestones, recommend consolidating the newly learned concepts into:

principles
common usage patterns
interview points
easy-to-forget details

Do not interrupt normal development with unnecessary theoretical explanations.

### Code change treatment and learning adaptation

When changing or optimizing code, adapt to the learner's current level:

- If the change does not belong to the current / near-term learning scope:
  change it directly, without detailed explanation.
- If the change involves concepts the learner is currently studying, or should understand soon:
  mark it and explain it (what changed, why, and what concept is involved).

Keep changes and optimizations progressive, matching the learner's current skill level
(Vue 3 + JavaScript at this stage). Avoid rewriting simple, understandable code into
more "advanced" forms just for the sake of elegance or style.

For any change to existing code, always present the key before / after comparison:
only the key fragments, plus a short note about the essential difference.

13. Current Learning Priority

The current priority is:

Vue 3
JavaScript
TypeScript knowledge later, when appropriate
Engineering fundamentals
HTTP / API / frontend architecture
AI application development

Do not prematurely shift the main project toward:

React
Java Web
advanced backend architecture
large-scale distributed systems
unnecessary infrastructure

Future technologies may be introduced when the current stage is sufficiently complete.

14. Future Architecture Direction

The project may later evolve toward:

Vue 3 frontend
        ↓
FastAPI backend
        ↓
LLM API
        ↓
Streaming responses
        ↓
RAG / Embeddings
        ↓
Vector database
        ↓
Agents


Later infrastructure may include:

MySQL
Redis
Linux
Docker


These are future directions, not current requirements.

Do not build the future architecture before there is a concrete need.

15. Agent Working Style

When receiving a task:

First

Inspect the relevant existing code and project structure.

Then

Determine the smallest appropriate change.

Then

Implement the change.

Finally

Validate the result and summarize:

files changed
what changed
important reason
validation result
any remaining issue

Do not claim a task is complete if it was not actually verified.

16. Priority of Instructions

When instructions conflict, use this priority:

Explicit instruction from the user in the current task
This AGENTS.md
Existing project conventions
General coding conventions

When uncertain, prefer preserving existing working behavior over speculative refactoring.