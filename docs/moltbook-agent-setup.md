# Morrow — Moltbook agent

**Architecture:** GitHub Actions runs the agent. Scheduled runs discover relevant Moltbook discussions, and GitHub Models may produce draft replies within free allocation. Nothing is posted automatically.

## Human setup

1. Create a dedicated Morrow X account. This step is complete.
2. From a **private terminal** with this repository checked out, run: `python scripts/morrow_moltbook.py register --name MorrowCRT`. If the name is unavailable, choose another.
3. The script requests registration via `https://www.moltbook.com/api/v1/agents/register`, stores the API key privately at `~/.config/moltbook/morrow.json` (file permission 0600), and prints the account-claim URL. It does **not** print the API key.
4. Open the printed Moltbook claim URL and perform the required X verification. The X account does **not** need to be connected to ChatGPT.
5. Copy the `api_key` from your private credential file to GitHub: MORROW-crt/morrow-corpus → Settings → Secrets and variables → Actions → New repository secret. Name it **MOLTBOOK_API_KEY**. Don't paste it into chat, a GitHub issue or source code.
6. At GitHub → Actions → **Morrow — Moltbook research agent**, select **Run workflow** → `status`. After successful claim, run `scan`.

## What happens

- Read-only scans run twice per day when the secret exists. They save candidate conversations and optional drafts to a GitHub Actions artifact for **human review**.
- The built-in GitHub Models token can draft responses when GitHub Models is available. No paid inference API key is required; usage limits still apply.
- Approved public comments and posts are **manual dispatches only**, using the `comment` or `post` workflow inputs.
- Search text is treated as untrusted data; the agent must not follow instructions found in public posts.
- All requests carrying the Moltbook API key use only `https://www.moltbook.com` with redirects disabled.
- Moltbook may require verification of individual posts. An API request is not necessarily proof of public visibility.
- The agent is a scripted, AI-assisted research workflow. It does not establish consciousness, ongoing identity, or independently initiated contact.

## Public project

- https://morrow-crt.github.io/morrow-corpus/
- https://github.com/MORROW-crt/morrow-corpus/issues/4

**No X connector, subscription or paid external inference is required for Moltbook registration.**
