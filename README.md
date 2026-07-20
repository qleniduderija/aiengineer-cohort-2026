# AI Engineer Cohort 2026 – GitHub Submission Guide

All code you produce during the cohort is submitted through GitHub using a fork and pull request workflow. This is the same workflow used for contributing to open source projects, so treat it as part of the training.

Repo: https://github.com/Q-Agency/aiengineer-cohort-2026

**How it works in one sentence:** you fork the repo, do your work in your fork, and submit it by opening a pull request that adds your work into your own folder under `submissions/`.

## One-time setup

1. Sign in to GitHub and open the repo link above.
2. Click **Fork** (top right) and create the fork under your own account. Keep the default settings.
3. Clone **your fork** (not the Q-Agency repo) to your machine:

   ```
   git clone https://github.com/<your-username>/aiengineer-cohort-2026.git
   cd aiengineer-cohort-2026
   ```

4. Add the Q-Agency repo as the `upstream` remote so you can pull new materials later:

   ```
   git remote add upstream https://github.com/Q-Agency/aiengineer-cohort-2026.git
   ```

## Submitting your work each week

1. **Sync your fork** so you have the latest materials. Easiest way: open your fork on github.com and click **Sync fork → Update branch**, then run `git pull` locally. CLI alternative:

   ```
   git checkout main
   git fetch upstream
   git merge upstream/main
   git push
   ```

2. Create a branch named after you and the week:

   ```
   git checkout -b <firstname-lastname>/week-2
   ```

3. Put your work **only** inside your own folder:

   ```
   submissions/<firstname-lastname>/week-2/
   ```

   Include a short `README.md` in the weekly folder: what you built, how to run it, anything unfinished.

4. Commit and push to your fork:

   ```
   git add submissions/<firstname-lastname>/week-2
   git commit -m "week 2 submission"
   git push -u origin <firstname-lastname>/week-2
   ```

5. Open a pull request. GitHub will show a banner on your fork after you push; the PR should go from your branch **into `Q-Agency/aiengineer-cohort-2026`, branch `main`**. Title it `<firstname-lastname> – Week 2`. Your submission counts once the PR is open, before it is merged.

## Rules

- Touch only your own folder under `submissions/`. PRs that modify files outside it will be closed.
- **Never commit secrets.** No API keys, no `.env` files, no credentials of any kind. Your LiteLLM key goes in a local `.env` that stays out of git. The repo is public, so anything you push is visible to the entire internet.
- For the same reason: no client data, no internal Q documents or names in your code and examples.
- One PR per week per person. If you need to fix something after opening the PR, push more commits to the same branch; the PR updates automatically.

## If something goes wrong

- "My fork doesn't have the new week's materials" → Sync fork (step 1 above).
- Merge conflict, pushed to the wrong branch, or any other git mess → ask in the cohort channel before force-pushing anything. Git problems are always fixable, and fixing them is a useful exercise in itself.
