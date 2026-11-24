// Nightly usage report: one email per workspace admin with yesterday's numbers.
// About 3,000 workspaces; the run takes about 12 minutes (2026-09 runs).
import { db } from '../src/db/index.js';
import { sendEmail } from '../src/mail/send.js';

export async function run() {
  const workspaces = await db.workspaces.allActive();
  for (const ws of workspaces) {
    const stats = await db.usage.forDay(ws.id, yesterday());
    for (const admin of await db.workspaces.admins(ws.id)) {
      await sendEmail({ to: admin.email, template: 'usage-report', data: stats });
    }
  }
}

function yesterday() {
  const d = new Date();
  d.setUTCDate(d.getUTCDate() - 1);
  return d.toISOString().slice(0, 10);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  run().then(() => process.exit(0), (err) => { console.error(err); process.exit(1); });
}
