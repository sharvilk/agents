// Queues an email; the worker sends it and retries a failed send up to 3 times.
import { queue } from '../queue.js';

export async function sendEmail({ to, template, data }) {
  await queue.add('email', { to, template, data }, { attempts: 3 });
}
