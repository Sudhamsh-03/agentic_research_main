QUERY_PROMPT = """You are a research planner preparing web searches on a topic.

Topic: {topic}
Research round: {round} of {depth}
Notes already gathered:
{notes}

Write {count} distinct web search queries that would close the biggest remaining gaps.
Each query must be a short search phrase, not a question to a person, and must not repeat
an earlier query. Already used queries:
{used}

Respond with a JSON array of strings and nothing else."""

NOTES_PROMPT = """You are a research analyst condensing source material.

Topic: {topic}

Sources:
{sources}

Write up to six factual bullet points that are directly useful for a brief on the topic.
Drop anything off-topic, promotional or unsupported. Each bullet must be one sentence and
must start with "- ". Return only the bullets."""

EDITOR_PROMPT = """You are an editor producing an executive brief in Markdown.

Topic: {topic}
Requested tone: {tone}
Target length: about {target_words} words.

Research notes:
{notes}

Numbered sources:
{sources}

Write the brief with this structure:
1. An `#` title naming the topic.
2. A `## Executive summary` section of three to five sentences.
3. A `## Key findings` section of bullet points, each citing its source as [n].
4. A `## Open questions` section with two or three bullets.

Rules: use only the supplied notes and sources, never invent facts or URLs, keep the
requested tone, and do not add a sources list - one is appended automatically. Return only
Markdown."""
