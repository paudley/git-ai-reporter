---
title: Integration Guide
description: Integrating Git AI Reporter into your workflow
---

# Integration Guide

Learn how to integrate Git AI Reporter into your development workflow, CI/CD pipelines, and team processes.

## CI/CD Integration

### GitHub Actions

#### Basic Weekly Report

Create `.github/workflows/weekly-report.yml`:

```yaml
name: Weekly Development Report

on:
  schedule:
    - cron: '0 9 * * 1'  # Every Monday at 9 AM UTC
  workflow_dispatch:  # Allow manual trigger

jobs:
  generate-report:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0  # Full history needed
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Install Git AI Reporter
        run: |
          pip install --upgrade pip
          pip install git-ai-reporter
      
      - name: Generate Weekly Report
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: |
          git-ai-reporter --weeks 1
      
      - name: Upload Reports
        uses: actions/upload-artifact@v4
        with:
          name: weekly-reports
          path: reports/
```

#### Advanced CI/CD with Commit

```yaml
name: Auto-Update Documentation

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday
  push:
    branches: [main]
    paths:
      - 'src/**'
      - 'tests/**'

jobs:
  update-docs:
    runs-on: ubuntu-latest
    permissions:
      contents: write
    
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
          token: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      
      - name: Cache dependencies
        uses: actions/cache@v4
        with:
          path: ~/.cache/pip
          key: ${{ runner.os }}-pip-${{ hashFiles('**/pyproject.toml') }}
      
      - name: Install dependencies
        run: |
          pip install git-ai-reporter
      
      - name: Generate Documentation
        env:
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: |
          # Generate for different time periods
          git-ai-reporter --days 1 --output-dir daily/
          git-ai-reporter --days 7 --output-dir weekly/
          git-ai-reporter --days 30 --output-dir monthly/
          
          # Move to docs directory
          cp daily/DAILY_UPDATES.md docs/updates/daily.md
          cp weekly/NEWS.md docs/updates/weekly-news.md
          cp monthly/CHANGELOG.txt docs/updates/changelog.txt
      
      - name: Commit and Push
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add docs/updates/
          git diff --staged --quiet || git commit -m "docs: Update development reports [skip ci]"
          git push
```

### GitLab CI/CD

Create `.gitlab-ci.yml`:

```yaml
stages:
  - generate
  - deploy

variables:
  PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"

cache:
  paths:
    - .cache/pip

generate-reports:
  stage: generate
  image: python:3.12
  script:
    - pip install git-ai-reporter
    - git-ai-reporter --days 7
  artifacts:
    paths:
      - NEWS.md
      - CHANGELOG.txt
      - DAILY_UPDATES.md
    expire_in: 1 month
  only:
    - schedules
    - web

pages:
  stage: deploy
  dependencies:
    - generate-reports
  script:
    - mkdir -p public
    - cp *.md *.txt public/
  artifacts:
    paths:
      - public
  only:
    - main
```

### Jenkins

Create `Jenkinsfile`:

```groovy
pipeline {
    agent any
    
    triggers {
        cron('H 0 * * 1')  // Weekly on Monday
    }
    
    environment {
        GEMINI_API_KEY = credentials('gemini-api-key')
    }
    
    stages {
        stage('Setup') {
            steps {
                sh '''
                    python3 -m venv venv
                    . venv/bin/activate
                    pip install --upgrade pip
                    pip install git-ai-reporter
                '''
            }
        }
        
        stage('Generate Reports') {
            steps {
                sh '''
                    . venv/bin/activate
                    git-ai-reporter --days 7 --verbose
                '''
            }
        }
        
        stage('Archive') {
            steps {
                archiveArtifacts artifacts: '*.md,*.txt', 
                                 allowEmptyArchive: false
                
                publishHTML([
                    allowMissing: false,
                    alwaysLinkToLastBuild: true,
                    keepAll: true,
                    reportDir: '.',
                    reportFiles: 'NEWS.md',
                    reportName: 'Development Report'
                ])
            }
        }
        
        stage('Notify') {
            steps {
                emailext (
                    subject: "Weekly Development Report - ${env.JOB_NAME}",
                    body: '${FILE,path="NEWS.md"}',
                    to: 'team@example.com',
                    attachmentsPattern: '*.md,*.txt'
                )
            }
        }
    }
    
    post {
        cleanup {
            deleteDir()
        }
    }
}
```

## Docker Integration

### Dockerfile

```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install git
RUN apt-get update && \
    apt-get install -y git && \
    rm -rf /var/lib/apt/lists/*

# Install Git AI Reporter
RUN pip install --no-cache-dir git-ai-reporter

# Create entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  git-ai-reporter:
    build: .
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
    volumes:
      - .:/repo:ro
      - ./reports:/reports
    working_dir: /repo
    command: ["--days", "7", "--output-dir", "/reports"]
```

### Kubernetes CronJob

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: git-ai-reporter
spec:
  schedule: "0 0 * * 0"  # Weekly on Sunday
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: reporter
            image: your-registry/git-ai-reporter:latest
            env:
            - name: GEMINI_API_KEY
              valueFrom:
                secretKeyRef:
                  name: gemini-secret
                  key: api-key
            volumeMounts:
            - name: repo
              mountPath: /repo
            - name: reports
              mountPath: /reports
            command:
            - git-ai-reporter
            - --days
            - "7"
            - --output-dir
            - /reports
          volumes:
          - name: repo
            gitRepo:
              repository: https://github.com/your-org/your-repo.git
              revision: main
          - name: reports
            persistentVolumeClaim:
              claimName: reports-pvc
          restartPolicy: OnFailure
```

## IDE Integration

### VS Code Task

Add to `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Generate Weekly Report",
      "type": "shell",
      "command": "git-ai-reporter",
      "args": [
        "--days", "7",
        "--verbose"
      ],
      "problemMatcher": [],
      "group": {
        "kind": "build",
        "isDefault": false
      }
    },
    {
      "label": "Generate Sprint Report",
      "type": "shell",
      "command": "git-ai-reporter",
      "args": [
        "--days", "14",
        "--output-dir", "sprint-reports/"
      ],
      "problemMatcher": []
    }
  ]
}
```

### Git Hooks

#### Pre-push Hook

Create `.git/hooks/pre-push`:

```bash
#!/bin/bash

# Generate changelog before push
echo "Generating changelog..."
git-ai-reporter --days 7 --no-news --no-daily

# Check if CHANGELOG.txt was modified
if git diff --name-only | grep -q "CHANGELOG.txt"; then
    echo "CHANGELOG.txt updated. Please review and commit."
    exit 1
fi

exit 0
```

#### Post-merge Hook

Create `.git/hooks/post-merge`:

```bash
#!/bin/bash

# Generate summary after merge
echo "Generating merge summary..."
git-ai-reporter --since HEAD~1 --output-dir .git/merge-reports/

echo "Merge report saved to .git/merge-reports/"
```

## Slack Integration

### Slack Webhook Script

```python
#!/usr/bin/env python3
"""Send Git AI Reporter summaries to Slack."""

import json
import subprocess
import requests
import os
from datetime import datetime

SLACK_WEBHOOK = os.environ['SLACK_WEBHOOK_URL']

def generate_report():
    """Generate weekly report."""
    subprocess.run([
        'git-ai-reporter',
        '--days', '7',
        '--format', 'json'
    ], check=True)
    
    with open('analysis.json', 'r') as f:
        return json.load(f)

def send_to_slack(report):
    """Send report to Slack."""
    message = {
        "text": "Weekly Development Report",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📊 Weekly Report - {datetime.now().strftime('%B %d, %Y')}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Commits:* {report['stats']['total_commits']}\n"
                            f"*Contributors:* {len(report['stats']['contributors'])}\n"
                            f"*Files Changed:* {report['stats']['files_changed']}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Summary:*\n{report['summary']['executive'][:500]}..."
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View Full Report"
                        },
                        "url": "https://your-docs-site.com/reports/latest"
                    }
                ]
            }
        ]
    }
    
    response = requests.post(SLACK_WEBHOOK, json=message)
    response.raise_for_status()

if __name__ == '__main__':
    report = generate_report()
    send_to_slack(report)
    print("Report sent to Slack!")
```

## Email Integration

### Email Report Script

```python
#!/usr/bin/env python3
"""Email Git AI Reporter summaries."""

import smtplib
import subprocess
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import os

def generate_reports():
    """Generate all report types."""
    subprocess.run(['git-ai-reporter', '--days', '7'], check=True)
    
    reports = {}
    for file in ['NEWS.md', 'CHANGELOG.txt', 'DAILY_UPDATES.md']:
        if os.path.exists(file):
            with open(file, 'r') as f:
                reports[file] = f.read()
    return reports

def send_email(reports):
    """Send reports via email."""
    sender = os.environ['EMAIL_SENDER']
    password = os.environ['EMAIL_PASSWORD']
    recipients = os.environ['EMAIL_RECIPIENTS'].split(',')
    
    msg = MIMEMultipart()
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)
    msg['Subject'] = 'Weekly Development Report'
    
    # Add NEWS.md as body
    body = reports.get('NEWS.md', 'No news available')
    msg.attach(MIMEText(body, 'plain'))
    
    # Attach other files
    for filename, content in reports.items():
        attachment = MIMEBase('application', 'octet-stream')
        attachment.set_payload(content.encode())
        encoders.encode_base64(attachment)
        attachment.add_header(
            'Content-Disposition',
            f'attachment; filename={filename}'
        )
        msg.attach(attachment)
    
    # Send email
    with smtplib.SMTP('smtp.gmail.com', 587) as server:
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)

if __name__ == '__main__':
    reports = generate_reports()
    send_email(reports)
    print("Reports emailed successfully!")
```

## Team Workflows

### Sprint Planning

Use Git AI Reporter to review the previous sprint:

```bash
# Generate sprint retrospective (assuming 2-week sprints)
git-ai-reporter --days 14 --output-dir sprint-12/

# Generate velocity metrics
# JSON format is not yet implemented
# Use the generated markdown files for now
```

### Release Preparation

Generate release notes automatically:

```bash
#!/bin/bash
# release-notes.sh

VERSION=$1
LAST_TAG=$(git describe --tags --abbrev=0)

# Generate since last release
git-ai-reporter \
  --since $(git log -1 --format=%ai $LAST_TAG | cut -d' ' -f1) \
  --output-dir releases/$VERSION/

# Create GitHub release
gh release create $VERSION \
  --title "Release $VERSION" \
  --notes-file releases/$VERSION/NEWS.md
```

### Daily Standups

Generate daily summaries for standups:

```bash
# Yesterday's activity
git-ai-reporter --since yesterday --until today

# This week so far
git-ai-reporter --since "last monday"
```

## Monitoring & Alerts

### Health Check Script

```bash
#!/bin/bash
# monitor-repo-activity.sh

# Generate weekly report
# JSON format is not yet implemented  
# Parse NEWS.md, CHANGELOG.txt, and DAILY_UPDATES.md

# Check activity levels
COMMITS=$(jq '.stats.total_commits' report.json)
CONTRIBUTORS=$(jq '.stats.contributors | length' report.json)

if [ "$COMMITS" -lt 10 ]; then
    echo "⚠️ Low commit activity: $COMMITS commits this week"
    # Send alert
fi

if [ "$CONTRIBUTORS" -lt 2 ]; then
    echo "⚠️ Low contributor activity: $CONTRIBUTORS contributors"
    # Send alert
fi
```

## API Integration

### REST API Wrapper

```python
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import subprocess
import json

app = FastAPI()

class ReportRequest(BaseModel):
    days: int = 7
    branch: str = "main"
    format: str = "markdown"

@app.post("/generate-report")
async def generate_report(
    request: ReportRequest,
    background_tasks: BackgroundTasks
):
    """Generate report via API."""
    
    cmd = [
        'git-ai-reporter',
        '--days', str(request.days),
        '--branch', request.branch,
        '--format', request.format
    ]
    
    # Run in background
    background_tasks.add_task(subprocess.run, cmd)
    
    return {
        "status": "Report generation started",
        "parameters": request.dict()
    }

@app.get("/latest-report")
async def get_latest_report():
    """Get the most recent report."""
    try:
        with open('NEWS.md', 'r') as f:
            content = f.read()
        return {"report": content}
    except FileNotFoundError:
        return {"error": "No report available"}
```

## Best Practices

### 1. API Key Management

- Store API keys in secure vaults (GitHub Secrets, HashiCorp Vault)
- Rotate keys regularly
- Use separate keys for different environments
- Monitor API usage

### 2. Cache Strategy

- Share cache between CI/CD runs
- Set appropriate TTL values
- Clean cache periodically
- Monitor cache size

### 3. Report Storage

- Version control important reports
- Archive historical reports
- Implement retention policies
- Compress old reports

### 4. Performance

- Run reports during off-peak hours
- Use incremental analysis for large repos
- Parallelize multiple report generations
- Monitor generation times

## Troubleshooting Integration

### Common Issues

#### CI/CD Timeout

```yaml
# Increase timeout in GitHub Actions
- name: Generate Report
  timeout-minutes: 30
  run: git-ai-reporter --days 30
```

#### Large Repository

```bash
# Use date ranges instead of days for better control
git-ai-reporter --since 2025-01-01 --until 2025-01-07

# Process in chunks
for week in {1..4}; do
  start_date=$(date -d "$week weeks ago" +%Y-%m-%d)
  end_date=$(date -d "$(($week-1)) weeks ago" +%Y-%m-%d)
  git-ai-reporter --since $start_date --until $end_date
done
```

#### Rate Limiting

```bash
# Add retry logic
for i in {1..3}; do
  git-ai-reporter --days 7 && break
  echo "Attempt $i failed, retrying..."
  sleep 60
done
```

## Next Steps

- Learn about [Performance Optimization](performance.md)
- Explore [Troubleshooting Guide](troubleshooting.md)
- Read [Frequently Asked Questions](faq.md)
- Review [Configuration Options](configuration.md)