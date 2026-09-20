# ourshelf — Project Brainstorm

_Last updated: 2026-09-20_

---

## Main Idea

Use a headless browser with cookies to scrape Goodreads data for a user and their friends, then generate a **community bookshelf** that:

- Shows books that multiple friends have **in common**
- Surfaces **recommendations** based on shared reading taste
- Turns individual reading lists into a shared, social experience

---

## Name Inspiration

| Name | Notes |
|---|---|
| **ourshelf** | Warm, possessive — "ours" not "mine" |
| shareable shelf | Descriptive, action-oriented |
| community bookshelf | Clear but generic |

Current working name: **ourshelf**

---

## Feature Areas

### Library
- UI-focused view of all books across the group
- Think: a virtual bookshelf you can browse

### Community Bookshelf
- Core feature — the shared/overlapping reading list
- Shows what everyone has read, is reading, or wants to read

### Book Club
- Recommendation engine built on top of shared data
- Surfaces books one person loved that others haven't read yet
- Potential feature: **shared reading calendar** (schedule what to read next together)

### Embeddable Widget
- A widget version of the shelf that can be dropped into other sites/pages

### Centrally Hosted
- The app would be hosted in one place (not self-hosted per user)
- Users connect their Goodreads accounts and the data is pulled centrally

---

## Data & Auth

| Concern | Approach |
|---|---|
| Auth | User logs in (account system TBD) |
| Reading data | Pulled from Goodreads via headless browser using user's cookies |
| Friends data | Also scraped from Goodreads friend lists |
| Data source | Headless browser (no official API — Goodreads deprecated theirs) |

---

## Technical Flow

```
Base repo
   └─> Core setup
          └─> Login (user auth)
                 └─> Run scrape script (headless browser + cookies)
                        └─> Generate site / UI
```

1. **Base repo** — monorepo or starter project scaffold
2. **Core** — shared utilities, data models
3. **Login** — user authentication flow
4. **Run script** — headless browser scrapes user's Goodreads + friends
5. **Generate site** — build the community bookshelf UI from scraped data

---

## Open Questions

- [ ] How do we handle Goodreads scraping at scale / rate limits?
- [ ] Do users need to provide their own cookies, or do we handle login?
- [ ] What does the "book club" recommendation algorithm look like?
- [ ] Should the embeddable widget be a separate package?
- [ ] Centrally hosted — what's the deployment target? (Vercel, Railway, etc.)
