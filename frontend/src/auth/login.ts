import { apiUrl } from "../api/client";
import { routes } from "../api/routes";

/**
 * POST /auth/jwt/login (OAuth2 password form).
 * Field names are fixed by OAuth2PasswordRequestForm: `username` carries the account email.
 */
export async function loginWithPassword(
  email: string,
  password: string,
): Promise<Response> {
  const body = new URLSearchParams();
  body.set("username", email);
  body.set("password", password);

  return fetch(apiUrl(routes.authJwtLogin), {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: body.toString(),
  });
}
