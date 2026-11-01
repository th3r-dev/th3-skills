# Interface writing

From Apple's HIG [Writing](https://developer.apple.com/design/human-interface-guidelines/writing).
These rules cover text people see in the product: labels, titles, alerts, errors, hints, empty
states, settings. They apply in any language, Thai included.

## Voice and tone

- **Voice is fixed, tone moves.** Voice comes from who the users are and what the product stands
  for (a bank: steady and trustworthy; a game: lively). Tone shifts with the moment: direct for a
  failed payment, warm for a reached goal.
- **Keep a term list.** One word per concept across the whole product. Read the existing screens
  and reuse their words before writing new ones.
- **Be clear.** Easy words, no word that isn't needed. If fewer words work, use fewer. Read it out loud.
- **Write for everyone.** Plain language, no jargon, no gendered terms, written so it can be
  translated and read by a screen reader.

## Rules

| Rule | Do | Don't |
|---|---|---|
| Purpose per screen | Most important information first; split ideas across screens | Pack several messages into one block |
| Action labels | A verb that says what happens: "Send", "Save draft" | "Let's do it!", "OK" when the action has a name |
| Links | Descriptive: "Learn more about pricing" | "Click here" (useless to screen readers) |
| Capitalization | Pick title or sentence case per element type, use it everywhere | Mix styles within one element type |
| Multi-step flows | Start with "Get Started", move with one choice of "Continue" or "Next", end with "Done" | Change the step verb between screens |
| Pronouns | Leave them out: "Favorites" | "Your Favorites" and "My Favorites" in one app; "we" anywhere |
| Device words | "Tap" on touch, "click" with a pointer | "Click" on a phone |
| Small and far screens | Short text (watch, phone, TV) | Long paragraphs on small or distant screens |
| Empty states | Say what to do next, give the button for it | Put crucial info there (empty states disappear) |
| Errors | Next to the problem, no blame, how to fix: "Choose a password with at least 8 characters" | "That password is too short", "Oops!", "Invalid name" |
| Delivery | Match urgency: inline, notification, alert or action sheet | An alert for something that can wait |
| Settings | Practical label; explain what ON does | Explaining what OFF does; describing a path instead of linking to it |
| Text fields | Clear label plus hint or example ("name@example.com") | Placeholder as the only label |
| Field errors | Say how to enter it: "Use only letters for your name" | "Don't use numbers or symbols" |

If wording alone can't fix an error that many people hit, the interaction is the problem.
Report it as a design finding, not a copy one.

## In flows (design-flow)

- A flow step reads as the user-visible action or check: "Check permission", "Show list".
- Decision labels are the outcome words the file already uses (`True` / `False`, or `Yes` / `No`).
- An alert step quotes the actual alert text and has an exit.

## Check

- [ ] Every button and link starts with a verb or names the destination.
- [ ] One capitalization style per element type.
- [ ] Every error says how to fix it and sits next to its field.
- [ ] Every empty state has a next step.
- [ ] No "we", no "oops", no "click here", no "invalid X" on its own.
- [ ] Terms match the product's existing words.
