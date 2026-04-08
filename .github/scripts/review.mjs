import fs from 'node:fs';

const token = process.env.GITHUB_TOKEN;
const repository = process.env.GITHUB_REPOSITORY;
const eventPath = process.env.GITHUB_EVENT_PATH;

if (!token || !repository || !eventPath) {
  throw new Error('Missing one or more required environment variables: GITHUB_TOKEN, GITHUB_REPOSITORY, GITHUB_EVENT_PATH.');
}

const event = JSON.parse(fs.readFileSync(eventPath, 'utf8'));
const prNumber = event?.pull_request?.number;
const commitId = event?.pull_request?.head?.sha;
if (!prNumber || !commitId) {
  throw new Error('pull_request number or commit SHA is missing in event payload.');
}

const findings = JSON.parse(fs.readFileSync('reports/all.json', 'utf8'));
if (!Array.isArray(findings) || findings.length === 0) {
  console.log('No findings to post.');
  process.exit(0);
}

const [owner, repo] = repository.split('/');
const apiBase = `https://api.github.com/repos/${owner}/${repo}`;

function buildBody(finding) {
  const severity = String(finding.severity || 'low').toUpperCase();
  const agent = String(finding.agent || 'unknown');
  return `⚠️ ${severity} (${agent})\n\n${finding.comment}`;
}

async function postReviewComment(finding) {
  const response = await fetch(`${apiBase}/pulls/${prNumber}/comments`, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${token}`,
      Accept: 'application/vnd.github+json',
      'Content-Type': 'application/json',
      'X-GitHub-Api-Version': '2022-11-28'
    },
    body: JSON.stringify({
      body: buildBody(finding),
      commit_id: commitId,
      path: finding.file,
      line: finding.line,
      side: 'RIGHT'
    })
  });

  if (!response.ok) {
    const message = await response.text();
    throw new Error(`GitHub API failed (${response.status}): ${message}`);
  }
}

const unique = new Set();
let posted = 0;

for (const finding of findings) {
  if (!finding?.file || !Number.isInteger(finding?.line) || finding.line <= 0 || !finding?.comment) {
    continue;
  }

  const dedupeKey = `${finding.file}:${finding.line}:${finding.severity}:${finding.comment}`;
  if (unique.has(dedupeKey)) {
    continue;
  }

  unique.add(dedupeKey);
  await postReviewComment(finding);
  posted += 1;

  if (posted >= 30) {
    console.log('Reached comment cap (30) to avoid API rate spikes.');
    break;
  }
}

console.log(`Posted ${posted} review comments.`);
