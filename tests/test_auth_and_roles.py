import unittest
from backend.auth.security import hash_password, verify_password, create_access_token, decode_access_token
from backend.auth.roles import ROLE_ADMIN, ROLE_MANAGER, ROLE_CASHIER

class TestAuthAndRoles(unittest.TestCase):
    def test_password_hashing_and_verification(self):
        """Verifies PBKDF2 password hashing and comparison."""
        pwd = "SecretTamilNaduRetail2026"
        hashed = hash_password(pwd)
        self.assertTrue(verify_password(pwd, hashed))
        self.assertFalse(verify_password("WrongPassword", hashed))

    def test_token_creation_and_signature_decoding(self):
        """Verifies tamper-evident signed token generation."""
        payload = {"sub": 1, "username": "admin", "role": ROLE_ADMIN}
        token = create_access_token(payload, expires_delta_seconds=3600)
        decoded = decode_access_token(token)
        self.assertIsNotNone(decoded)
        self.assertEqual(decoded["username"], "admin")
        self.assertEqual(decoded["role"], ROLE_ADMIN)

        # Tampered token test
        tampered_token = token[:-4] + "xyz1"
        self.assertIsNone(decode_access_token(tampered_token))

if __name__ == "__main__":
    unittest.main()
