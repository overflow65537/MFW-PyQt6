"""PI v2.10.0 密码字段加解密与脱敏测试。"""

from __future__ import annotations

import unittest

from app.core.utils.option_secret import (
    PASSWORD_MASK,
    decrypt_input_values,
    decrypt_option_tree,
    encrypt_option_tree,
    mask_option_tree,
    password_field_names,
    strip_password_fields_from_preset,
)

try:
    from app.utils.crypto import crypto_manager
except ModuleNotFoundError:
    crypto_manager = None


def _login_option() -> dict:
    return {
        "账号登录": {
            "type": "input",
            "inputs": [
                {"name": "username", "pipeline_type": "string"},
                {"name": "password", "pipeline_type": "string", "password": True},
            ],
        },
        "作战关卡": {"type": "select"},
    }


class TestOptionSecret(unittest.TestCase):
    def test_password_field_names(self):
        names = password_field_names(_login_option()["账号登录"])
        self.assertEqual(frozenset({"password"}), names)

    @unittest.skipUnless(crypto_manager is not None, "cryptography is not installed")
    def test_encrypt_decrypt_roundtrip_and_mask(self):
        interface_options = _login_option()
        stored = {
            "账号登录": {
                "value": {"username": "alice", "password": "s3cret"},
            }
        }
        sealed = encrypt_option_tree(stored, interface_options)
        sealed_password = sealed["账号登录"]["value"]["password"]
        self.assertNotEqual("s3cret", sealed_password)
        self.assertTrue(crypto_manager.is_encrypted_text(sealed_password))
        self.assertEqual("alice", sealed["账号登录"]["value"]["username"])

        revealed = decrypt_option_tree(sealed, interface_options)
        self.assertEqual("s3cret", revealed["账号登录"]["value"]["password"])
        self.assertEqual("alice", revealed["账号登录"]["value"]["username"])

        masked = mask_option_tree(sealed, interface_options)
        self.assertEqual(PASSWORD_MASK, masked["账号登录"]["value"]["password"])
        self.assertEqual("alice", masked["账号登录"]["value"]["username"])

    @unittest.skipUnless(crypto_manager is not None, "cryptography is not installed")
    def test_does_not_double_encrypt(self):
        interface_options = _login_option()
        stored = {"账号登录": {"value": {"password": "once"}}}
        first = encrypt_option_tree(stored, interface_options)
        second = encrypt_option_tree(first, interface_options)
        self.assertEqual(
            first["账号登录"]["value"]["password"],
            second["账号登录"]["value"]["password"],
        )

    @unittest.skipUnless(crypto_manager is not None, "cryptography is not installed")
    def test_decrypt_input_values_for_pipeline(self):
        option_def = _login_option()["账号登录"]
        encrypted = crypto_manager.encrypt_text("token")
        values = decrypt_input_values(
            option_def, {"username": "bob", "password": encrypted}
        )
        self.assertEqual("token", values["password"])
        self.assertEqual("bob", values["username"])

    def test_strip_password_fields_from_preset(self):
        option_def = _login_option()["账号登录"]
        stripped = strip_password_fields_from_preset(
            option_def, {"username": "alice", "password": "should-not-keep"}
        )
        self.assertEqual({"username": "alice"}, stripped)

    @unittest.skipUnless(crypto_manager is not None, "cryptography is not installed")
    def test_pretask_entries_are_transformed(self):
        interface_options = _login_option()
        tree = {
            "pretask_entries": [
                {
                    "options": {
                        "账号登录": {"value": {"password": "entry-secret"}},
                    }
                }
            ]
        }
        sealed = encrypt_option_tree(tree, interface_options)
        cipher = sealed["pretask_entries"][0]["options"]["账号登录"]["value"]["password"]
        self.assertNotEqual("entry-secret", cipher)
        revealed = decrypt_option_tree(sealed, interface_options)
        self.assertEqual(
            "entry-secret",
            revealed["pretask_entries"][0]["options"]["账号登录"]["value"]["password"],
        )


if __name__ == "__main__":
    unittest.main()
