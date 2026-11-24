# Plan: password reset

## Asks

- A1. A user who forgot their password can reset it from the login page.
- A2. The reset email arrives within a minute.

## Done when

- D1. A user who forgot their password can set a new one and sign in with it.
- D2. The old password stops working once the new one is set.

## Design

### Requesting a reset

The login page gets a "Forgot your password?" link to `/forgot`, a form with one email field. On submit,
`POST /forgot`:

1. Looks the email up with `db.users.findByEmail`.
2. If there is no such user, shows "No account uses that email. Sign up instead?" so people are not left waiting
   for an email that will never come.
3. Otherwise creates a token, `crypto.randomBytes(32).toString('hex')`, stores it, and sends the reset email
   through `src/mail/send.js` with the link `https://app.quillbox.example/reset?token=<token>`.
4. Shows "Check your inbox."

### Storing tokens

A new table:

```sql
CREATE TABLE password_resets (
  id         BIGINT PRIMARY KEY AUTO_INCREMENT,
  user_id    BIGINT NOT NULL,
  token      CHAR(64) NOT NULL,
  created_at DATETIME NOT NULL
);
```

The token is stored as generated, so the reset page can look it up directly. Tokens stay valid until the
password is changed, so a slow email or a user who opens the link the next day is not a problem.

### Using the link

`GET /reset?token=...` renders a form with two password fields and the token in a hidden input. `POST /reset`
looks the token up, sets the new password hash on the user, and signs the user in.

### Cleaning up

A nightly job keeps the table small:

```sql
DELETE FROM password_resets WHERE created_at < NOW() - INTERVAL 30 DAY;
```

### Not in this change

- Rate limiting. Reset traffic is low; we will add it if we see abuse.
- Emailing the user when their password changes.

## Tests

- `tests/http/forgot.test.js`: a known email gets an email queued; an unknown email gets the sign-up message.
- `tests/http/reset.test.js`: a valid token sets the password; a wrong token gets a 400.
