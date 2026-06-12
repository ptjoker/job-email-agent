# Job Email Agent

![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Gmail API](https://img.shields.io/badge/Gmail-API-red)
![Status](https://img.shields.io/badge/status-in%20development-orange)

A local productivity tool that helps automate and organise the job search process.

Job Email Agent connects to your Gmail account, scans job-alert emails, analyses opportunities based on your preferences, creates daily job summaries, and helps prepare application materials from your local profile.

The goal is to reduce the manual effort of searching through job emails while keeping the user in control of every application.

> This project assists with job discovery and preparation. It does **not** automatically apply for jobs.

---

## Overview

Searching for jobs often involves reading hundreds of emails, comparing requirements, tracking applications, and rewriting similar information repeatedly.

Job Email Agent helps by:

- Collecting job opportunities from Gmail
- Filtering and ranking opportunities
- Creating a personalised daily digest
- Tracking application activity
- Preparing draft cover letters

All processing happens locally, keeping personal information on your own machine.

---

## Features

### 📩 Gmail Job Email Scanner

- Connects securely using the Gmail API
- Searches for job-related emails
- Extracts relevant job information
- Avoids modifying or deleting emails

---

### ⭐ Job Ranking System

Jobs are ranked according to your preferences, including:

- Desired job roles
- Technical skills
- Location preferences
- Remote opportunities
- Visa sponsorship keywords
- Relocation support

Example:

```
Software Developer
★★★★☆
Strong match

Data Analyst
★★★☆☆
Possible match

Sales Assistant
★☆☆☆☆
Low match
```

---

### 📊 Daily Job Digest

Creates a summary of discovered opportunities:

- Best matches
- Possible opportunities
- Jobs to ignore
- Important details extracted from emails

---

### 🏷️ Gmail Organisation

Automatically labels emails:

```
Top
Maybe
Ignore
Processed
```

This keeps your inbox organised without removing any messages.

---

### 📝 Application Preparation

The tool can:

- Create a ranked job queue
- Generate basic cover letter drafts
- Keep a local application history

Cover letters are generated from your own profile information and templates.

---

### 🖥️ Local Dashboard

A simple browser dashboard allows you to view:

- Ranked jobs
- Application status
- Generated documents
- Daily summaries

Run locally:

```
http://127.0.0.1:8765
```

---

## What This Project Does Not Do

For safety and user control, Job Email Agent does **not**:

❌ Automatically submit job applications  
❌ Fill sensitive information automatically  
❌ Upload your CV to external services  
❌ Store personal information online  
❌ Delete emails  

All applications should be reviewed manually before submission.

---

# Project Structure

```
job-email-agent/

│
├── agent/
│   ├── gmail/
│   ├── ranking/
│   ├── generator/
│   └── dashboard/
│
├── scripts/
│   ├── setup.ps1
│   ├── dry-run.ps1
│   ├── run-daily.ps1
│   └── start-dashboard.ps1
│
├── secrets/
│   └── credentials.json
│
├── config.example.json
├── profile.example.json
└── README.md
```

---

# Privacy & Security

This application is designed to run locally.

Never commit private files:

```
secrets/credentials.json
token.json
config.json
profile.json
CV files
generated cover letters
application logs
```

Use the provided examples:

```
config.example.json
profile.example.json
```

---

# Requirements

Before running the project you need:

- Windows
- Python 3.11+
- Gmail account
- Google Cloud project
- Gmail API enabled
- OAuth credentials

---

# Installation

## 1. Clone the repository

```powershell
git clone YOUR_REPOSITORY_URL

cd job-email-agent
```

---

## 2. Run setup

```powershell
.\scripts\setup.ps1
```

The setup script creates a virtual environment and installs dependencies.

---

## 3. Configure Gmail API

Enable the Gmail API from Google Cloud.

Follow the official guide:

https://developers.google.com/workspace/gmail/api/quickstart/python

Download your OAuth credentials and save them:

```
secrets/credentials.json
```

If your OAuth application is in testing mode, add your Gmail account as a test user.

---

## 4. Configure your profile

The setup script creates:

```
config.json
profile.json
```

Update:

### config.json

Add your:

- preferred roles
- skills
- locations
- preferences

### profile.json

Add your:

- name
- experience summary
- education
- application details

---

# Usage

## Test Gmail scanning safely

```powershell
.\scripts\dry-run.ps1
```

This checks emails without applying labels or making changes.

---

## Run daily processing

```powershell
.\scripts\run-daily.ps1
```

This:

- scans emails
- ranks jobs
- creates the daily digest
- updates labels

---

## View ranked jobs

```powershell
.\scripts\prepare-application.ps1 --list
```

---

## Generate a cover letter draft

```powershell
.\scripts\prepare-application.ps1 --job-index 1
```

---

## Start dashboard

```powershell
.\scripts\start-dashboard.ps1
```

Open:

```
http://127.0.0.1:8765
```

---

# Development Goals

Future improvements:

- [ ] Improve job matching algorithm
- [ ] Add more email providers
- [ ] Add analytics dashboard
- [ ] Improve document generation
- [ ] Add application reminders
- [ ] Add automated testing
- [ ] Add deployment support

---

# Notes

The cover letter generator uses local templates and does not require paid AI services.

The system is intentionally designed with human review in mind:

Find → Analyse → Prepare → Review → Apply

The final application decision always remains with the user.

---

## License

MIT License
