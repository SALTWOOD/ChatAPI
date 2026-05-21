import type { AuthSession } from '../../types/chat'

export const DEFAULT_AUTH_SESSION: AuthSession = {
  authenticated: false,
  user: null,
  totp_enabled: false,
  registration_enabled: false,
  geetest_enabled: false,
  geetest_captcha_id: '',
}
