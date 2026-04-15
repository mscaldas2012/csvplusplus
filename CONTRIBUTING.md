# Contributing to CSV++

Thanks for your interest in CSV++! This is an open specification project, and feedback from real-world implementers and users is what makes a good spec great. Here's how to get involved.

---

## Ways to Contribute

### 🐛 Report an Issue with the Spec

Found an ambiguity, a contradiction, or something that just doesn't make sense? Please open a GitHub Issue. Good spec issues include:

- Unclear or underspecified behavior (e.g., "what happens if a structured field has an empty component?")
- Edge cases that aren't covered
- Conflicts between sections
- Security or injection concerns

Use the label **`spec-clarification`** for ambiguities, **`design-question`** for deeper questions about intent, or **`editorial`** for typos and wording fixes.

### 🔨 Share Implementation Feedback

If you've built a CSV++ parser, encoder, or tool — we especially want to hear from you. Real-world implementation experience surfaces problems that are hard to catch on paper.

Open an issue labeled **`implementation-feedback`** and tell us what you built, what worked, and what didn't. This kind of feedback directly shapes future drafts.

### ✏️ Propose a Change

For small fixes (typos, grammar, broken links), feel free to open a Pull Request directly.

For anything more substantial — new examples, wording changes, structural additions — please open an issue first so we can discuss it before you invest time writing it up. The source of truth is `spec/draft-mscaldas-csvpp-02.xml` (RFC XML v3 format), so PRs should target that file.

### 💬 Start a Discussion

Not sure if something is a bug or a feature? Just want to think out loud about the format? Open a GitHub Discussion — it's a lower-stakes space for exploratory conversations.

---

## What Makes a Good Issue

- **Be specific.** Quote the section or text you're referring to.
- **Show an example.** A sample CSV++ snippet goes a long way.
- **Describe the impact.** Is this a corner case or does it affect common usage?

---

## Get in Touch

Prefer email? Reach us at [csvplusplus@gmail.com](mailto:csvplusplus@gmail.com). This is useful for longer-form feedback, private concerns, or if you're working on an implementation and want to coordinate.

---

## Code of Conduct

Be kind. This is a small, open project and we want it to stay welcoming. Constructive disagreement about spec design is great — personal attacks are not.

---

*CSV++ is an IETF Internet-Draft. Significant contributions may eventually be subject to IETF intellectual property policies as the spec matures.*
