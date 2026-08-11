# Design Decisions

## 1. Strict closed-subset parser instead of PyYAML

I initially considered using a YAML library, but decided against it. Since I control the format of these documents, I only need to support scalars, inline lists, and one level of list-of-dicts.

Keeping the parser limited to this makes the output predictable and machine-readable. The downside is that it isn't a full YAML parser, so there are some edge cases that real YAML would handle differently. For example, I don't allow colons in descriptions, and the validator checks for that.

## 2. Document-level hashing instead of section-level hashing

Section-level hashing would be more efficient for larger documents because we could re-process only the part that changed. But with only six sources right now, I felt that was unnecessary complexity.

Hashing the whole source is simple, exact, and easy to test. If this had to scale to a much larger set of documents, section-level hashing would probably be one of the first things I'd add.

## 3. Four subagents instead of one large prompt

I wanted each agent to have a clear responsibility and only the tools it actually needs.

The scout can use bash but can't write files, the extractor is read-only, the validator can read and grep, and the merger is the only agent that can actually write.

This also gives some security by design, instead of just relying on instructions telling the agents not to do something.

## 4. Hook-based validation instead of agent self-validation

I used a hook for validation instead of asking the agent to validate its own work. My thinking was that an instruction inside a prompt can potentially be missed, especially when the context gets large, while a hook will run regardless.

One issue I found during testing was that if the hook uses a relative path for its working directory, it can fail silently and end up validating nothing. That's actually worse than not having the hook, so that's something I had to account for.

## 5. Registry-based discovery instead of open web crawling

I considered having the scout search for new sources automatically, but that brings in a few extra problems: search MCP requirements, deciding which domains to trust, and potentially needing human approval for unknown sources.

So for this version, I made the source registry explicit. The tradeoff is that the system currently maintains the knowledge it is given, but it doesn't discover new sources on its own yet.

## 6. Frontmatter sources and `[S#]` markers instead of OKF section 8 citations

The OKF specification puts citations into a numbered section at the bottom of the document. I didn't find that sufficient for this use case because I wanted provenance at the individual fact level, including things like the source type and fetch date.

That information is also useful later for conflict resolution and confidence scoring. So this is a deliberate deviation from the spec, and I've documented it rather than treating it as an accidental difference.

## 7. Strict producer, permissive consumer

There is a slight difference between what section 9 of the spec says and what my validator does. The spec says consumers shouldn't reject a bundle just because it contains unknown keys, while my validator is stricter and rejects them.

I don't see that as a contradiction because my validator is acting as a producer-side quality gate. I'd rather stop a document from drifting when my system is creating it, while still allowing another consumer to read documents with additional metadata.

## 8. Offline fixtures instead of live scraping for tests

I ran into the practical issue that Amazon blocks a basic `urllib` request with a 403, and some of the pages also depend on JavaScript. Proper live fetching would therefore need something like the Playwright MCP.

For testing, I chose snapshots instead because they make the runs deterministic and mean someone can clone the repo and test it without needing network access.

The tradeoff is that the six fixtures are still hand-made snapshots, so I wouldn't claim they represent six completely independent live sources.