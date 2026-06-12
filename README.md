# Job Email Agent

A cautious email triage agent for job-alert emails.

It connects to Gmail, finds likely job-alert messages, labels them by usefulness, and writes a daily "top jobs" digest. It does not delete email.

## What It Does

- Finds job-alert messages from LinkedIn, job boards, recruiters, and ATS systems.
- Scores each message against your role, location, remote, seniority, and keyword preferences.
- Writes a ranked job queue for application prep.
- Applies Gmail labels:
  - `Jobs/Top`
  - `Jobs/Maybe`
  - `Jobs/Ignore`
  - `Jobs/Processed`
- Creates a Markdown digest in `digests/`.
- Creates template-based cover letters from your local CV and profile.
- Logs application drafts in `applications/`.

## Setup

1. Follow Google's Gmail Python quickstart to enable Gmail API access and create an OAuth desktop client:

   https://developers.google.com/workspace/gmail/api/quickstart/python

2. Download the OAuth client JSON file.
3. Save it as:

   ```text
   secrets/credentials.json
   ```

4. In Google Cloud, add your Gmail address as a test user:

   - Open your project in Google Cloud Console.
   - Go to `APIs & Services` -> `OAuth consent screen`.
   - Find the `Test users` section.
   - Add the Gmail address you will use with the agent.
   - Save the changes.

5. Copy the example config:

   ```powershell
   Copy-Item config.example.json config.json
   ```

6. Edit `config.json` with your job preferences and CV path.

7. Edit `profile.json` with your public application details.

8. Install dependencies:

   ```powershell
   .\scripts\setup.ps1
   ```

9. Run a dry run first:

   ```powershell
   .\scripts\dry-run.ps1
   ```

10. If the output looks good, run it for real:

   ```powershell
   .\scripts\run-daily.ps1
   ```

## Prepare A Cover Letter

After a dry run or daily run, list the ranked jobs:

```powershell
.\scripts\prepare-application.ps1 --list
```

Create a cover letter for a specific ranked job:

```powershell
.\scripts\prepare-application.ps1 --job-index 1
```

This creates:

- a cover letter in `cover_letters/`
- an application log entry in `applications/YYYY-MM-DD-applications.md`

It does not submit applications or fill sensitive fields.

## Daily Run

After setup, run this once a day using Windows Task Scheduler:

```powershell
cd "C:\Users\thaba\Documents\Codex\2026-06-03\can-we-build-an-agent-or\job-email-agent"
.\scripts\run-daily.ps1
```

## Safety

The agent never deletes emails. Low-scoring emails are only labeled `Jobs/Ignore` so you can inspect them later.

The application-prep step does not auto-submit jobs. It prepares a cover letter and log entry for your review. ID numbers, passport numbers, and similar fields should be filled manually.

## Troubleshooting

### Access blocked: app has not completed verification

This usually means the OAuth app is still in Google's testing mode, but your Gmail address has not been added as a test user.

Fix it in Google Cloud Console:

1. Open `APIs & Services`.
2. Open `OAuth consent screen`.
3. Add your Gmail address under `Test users`.
4. Save, then run `.\scripts\dry-run.ps1` again.

You do not need Google verification for this personal testing setup. Verification is only needed before making the app broadly available to other users.
