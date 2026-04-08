import fs from 'node:fs';

const [inputPath, fallbackAgent = 'unknown'] = process.argv.slice(2);
if (!inputPath) {
  console.error('Usage: normalize-findings.mjs <inputPath> [fallbackAgent]');
  process.exit(1);
}

const raw = fs.readFileSync(inputPath, 'utf8').trim();

const maybeJson = (() => {
  if (!raw) {
    return '[]';
  }

  const fence = raw.match(/```(?:json)?\s*([\s\S]*?)```/i);
  if (fence?.[1]) {
    return fence[1].trim();
  }

  const arrayStart = raw.indexOf('[');
  const arrayEnd = raw.lastIndexOf(']');
  if (arrayStart >= 0 && arrayEnd > arrayStart) {
    return raw.slice(arrayStart, arrayEnd + 1);
  }

  return raw;
})();

let parsed;
try {
  parsed = JSON.parse(maybeJson);
} catch {
  parsed = [];
}

const severityOrder = new Set(['low', 'medium', 'high', 'critical']);

const normalized = Array.isArray(parsed)
  ? parsed
      .map((entry) => {
        const file = typeof entry?.file === 'string' ? entry.file.trim() : '';
        const line = Number.isInteger(entry?.line)
          ? entry.line
          : Number.isFinite(Number(entry?.line))
            ? Number(entry.line)
            : 0;
        const rawSeverity = typeof entry?.severity === 'string' ? entry.severity.toLowerCase().trim() : 'low';
        const severity = severityOrder.has(rawSeverity) ? rawSeverity : 'low';
        const comment = typeof entry?.comment === 'string' ? entry.comment.trim() : '';
        const agent = typeof entry?.agent === 'string' && entry.agent.trim() ? entry.agent.trim() : fallbackAgent;

        if (!file || !comment || line <= 0) {
          return null;
        }

        return { file, line, severity, comment, agent };
      })
      .filter(Boolean)
  : [];

process.stdout.write(`${JSON.stringify(normalized, null, 2)}\n`);
