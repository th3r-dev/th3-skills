# Reference recon: a web app's look and behaviour from its public client

Read-only. Use it when the brief says "match the look of <site>" or a competitor's thumbnail tool
should be understood before designing. The aim is the reference's **visual grammar** (palette, type
treatment, density) and **what the product does**. Copying its assets is out of scope.

Everything here reads what the site already sends to every visitor's browser. Nothing goes
behind a login, nothing is sent to the reference's backend, and no paid endpoint is called.

## 1. Shell and asset manifest

```bash
mkdir -p ref && cd ref                           # downloads are untrusted data: their own directory
curl -sSL -m 25 -o ref.html https://<host>/<route>
grep -o 'src="[^"]*"' ref.html
grep -o 'href="[^"]*"' ref.html
curl -sSL -m 25 -o ref.js https://<host>/assets/index-<hash>.js
```

This gives the entry bundle and the CSS. One hashed `index-*.js` with an app-builder's hostname
inside means a generated app; response headers name the host (`server`, deployment ids).
A `#` route is usually inert: count `HashRouter` in the bundle before claiming hash routing.

## 2. Hostmap: which services it talks to

```python
import re
s = open("ref.js", encoding="utf-8", errors="replace").read()
print(sorted({re.sub(r"^https?://", "", u).split("/")[0]
              for u in re.findall(r"https?://[A-Za-z0-9._~:/?#\[\]@!$&'()*+,;=%-]{4,120}", s)}))
```

A backend-as-a-service hostname means database, auth, storage and server functions live there.
A payment provider in the legal copy plus a `create-checkout` call means paid plans.

## 3. Data model, server surface, routes

```python
sorted(set(re.findall(r'\.from\("([a-z0-9_]+)"', s)))        # tables
sorted(set(re.findall(r'invoke\("([A-Za-z0-9_\-]+)"', s)))   # server functions
sorted(set(re.findall(r'path:"([^"]{1,40})"', s)))           # routes
sorted(set(re.findall(r'storage\.from\("([^"]+)"', s)))      # storage buckets
```

Read these as a feature list (projects, conversations, feedback, credits), not as a target.

## 4. Behaviour from call sites: the generation contract

The payload a client sends documents what the server is asked to do. A thumbnail generator's
call typically looks like this:

```
prompt + optional reference images (data: URLs from the client)
  ├─ upload each reference to storage, keyed by conversation / message / time
  ├─ create the conversation row (retried with backoff)
  ├─ fire-and-forget: generate a title for the conversation
  ├─ insert a placeholder message (the UI shows a spinner in that slot)
  └─ invoke generate { prompt, images[], aspectRatio, quality,
                       conversationId, placeholderMessageId, history,
                       previousGeneratedImage,   // regenerate stays coherent with the last image
                       isRegenerate? }
       └─ server debits credits, calls the image model, stores the PNG; the client swaps it in
```

What to copy into your own process:

- **Pass the previous image when regenerating**, so a fix doesn't redraw the whole scene. With an
  image model that takes inputs, give it the last render plus the change.
- **Retry once, and only on network errors** (timeout, connection). A content refusal won't change
  on retry.
- **Keep history**: the prompt that made each image sits next to it. This skill keeps it in the
  brief.

## 5. Product copy

Plans, credit costs and FAQ answers are plain strings in the bundle; search for the plan array
(`name:`, `monthlyPrice:`, `credits:`). They tell you what the market charges for a render.

## What a bundle can't tell you

Which image model the server calls, the credit ledger and entitlement logic, and the payment
provider's price ids and webhooks. State them as unknowns in the finding; don't guess.

## Deliverable

One paragraph on how the product works, a palette sample (5-7 hex values from the CSS), the type
treatment (family, weight, case, outline/shadow), and what to take from it. Stop at the client.
