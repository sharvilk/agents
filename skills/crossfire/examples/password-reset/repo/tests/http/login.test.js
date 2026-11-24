import { test } from 'node:test';
import assert from 'node:assert/strict';
import { makeApp } from '../helpers.js';

test('login rejects a wrong password with the same message as an unknown email', async () => {
  const app = await makeApp({ users: [{ email: 'a@example.com', password: 'right-one' }] });
  const wrong = await app.post('/login', { email: 'a@example.com', password: 'wrong' });
  const unknown = await app.post('/login', { email: 'b@example.com', password: 'wrong' });
  assert.equal(wrong.status, 401);
  assert.deepEqual(wrong.body, unknown.body);
});
