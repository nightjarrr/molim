#!/usr/bin/env node

import { execSync } from 'node:child_process';
import { readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { parseArgs } from 'node:util';

const { values } = parseArgs({
    options: {
        'issue-id': { type: 'string' },
        'entry': { type: 'string' },
    },
    strict: true,
});

const { 'issue-id': issueId, entry: entryText } = values;

if (!issueId || !issueId.trim()) {
    process.stderr.write('Error: --issue-id is required and must be non-empty.\n');
    process.exit(2);
}

if (!entryText || !entryText.trim()) {
    process.stderr.write('Error: --entry is required and must be non-empty.\n');
    process.exit(2);
}

const repoRoot = execSync('git rev-parse --show-toplevel', { encoding: 'utf8' }).trim();
const changelogPath = join(repoRoot, 'CHANGELOG.md');

const SKELETON = '# Changelog\n\n## UPCOMING\n\n';

let raw = '';
try {
    raw = readFileSync(changelogPath, 'utf8');
} catch {
    // file absent — will bootstrap below
}

if (!raw.trim()) {
    writeFileSync(changelogPath, SKELETON, 'utf8');
    raw = readFileSync(changelogPath, 'utf8');
}

const lines = raw.split('\n');

const upcomingIdx = lines.findIndex(l => l === '## UPCOMING');
if (upcomingIdx === -1) {
    process.stderr.write('Error: CHANGELOG.md exists and is non-empty but contains no "## UPCOMING" section.\n');
    process.exit(1);
}

const nextSectionRaw = lines.findIndex((l, i) => i > upcomingIdx && l.startsWith('## '));
// When no next section exists (pre-release), treat EOF as boundary.
// Account for the trailing-newline artifact: split('\n') on a file ending with '\n'
// produces a final empty element that represents the newline, not a blank line.
const atEof = nextSectionRaw === -1;
const nextSectionIdx = atEof ? lines.length : nextSectionRaw;

// Effective boundary excludes the trailing-newline artifact when at EOF
const effectiveBoundary = atEof && lines[lines.length - 1] === '' ? lines.length - 1 : nextSectionIdx;

const sectionLines = lines.slice(upcomingIdx + 1, effectiveBoundary);
const isEmpty = sectionLines.every(l => l.trim() === '');

const entry = `- ${entryText} (#${issueId})`;

if (isEmpty) {
    // Insert entry + trailing blank before the effective boundary.
    // For real next sections: splice at nextSectionIdx (inserts before the section header).
    // For EOF: splice at effectiveBoundary (inserts before the trailing-newline artifact),
    // and add a trailing blank to maintain the blank-line-before-EOF convention.
    lines.splice(effectiveBoundary, 0, entry, '');
} else {
    lines.splice(nextSectionIdx - 1, 0, entry);
}

writeFileSync(changelogPath, lines.join('\n'), 'utf8');

// Re-find boundaries in updated array to output the UPCOMING section
const updatedUpcomingIdx = lines.findIndex(l => l === '## UPCOMING');
const updatedNextSectionRaw = lines.findIndex((l, i) => i > updatedUpcomingIdx && l.startsWith('## '));
const updatedNextSectionIdx = updatedNextSectionRaw === -1 ? lines.length : updatedNextSectionRaw;

const outputLines = lines.slice(updatedUpcomingIdx, updatedNextSectionIdx);
// Trim trailing blank lines from output
while (outputLines.length > 0 && outputLines[outputLines.length - 1].trim() === '') {
    outputLines.pop();
}

process.stdout.write(outputLines.join('\n') + '\n');
