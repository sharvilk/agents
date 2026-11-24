import { verifyPassword } from '../auth/passwords.js';
import { db } from '../db/index.js';

export async function login(req, res) {
  const user = await db.users.findByEmail(req.body.email);
  if (!user || !(await verifyPassword(req.body.password, user.password_hash))) {
    return res.status(401).json({ error: 'Email or password is incorrect.' });
  }
  const session = await db.sessions.create(user.id);
  res.cookie('sid', session.id, { httpOnly: true, secure: true, sameSite: 'lax' });
  return res.json({ ok: true });
}
