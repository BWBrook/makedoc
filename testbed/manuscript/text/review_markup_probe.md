# Review Markup Probe

## Abstract

This probe checks whether human-editable review markup can stay in Markdown
source and render visibly in generated outputs [@alpha2020SyntheticWorkflow].

## Body

The sentence keeps **ordinary Markdown** intact while showing {++ inserted review text ++}, {-- removed review text --}, {~~ outdated wording ~> revised wording ~~}, and {>> reviewer asks for a clearer transition <<}.

Inline examples such as `{++ literal addition ++}` must remain untouched.

```markdown
{-- fenced deletion should remain literal --}
```

## References
