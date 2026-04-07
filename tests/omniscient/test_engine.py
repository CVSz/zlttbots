import json
import unittest

from services.omniscient.engine import OmniscientEngine
from services.omniscient.security_ops import DefenseRule, deploy_defense, risk_score, simulate_attack


class OmniscientEngineTests(unittest.TestCase):
    def test_run_returns_actions(self) -> None:
        sarif = json.dumps({"runs": [{"results": [{"ruleId": "py/sql-injection"}]}]})
        engine = OmniscientEngine()

        actions = engine.run(sarif)

        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0]["finding"], "py/sql-injection")
        self.assertTrue(actions[0]["verified"])

    def test_simulate_attack_requires_http_scheme(self) -> None:
        with self.assertRaises(ValueError):
            simulate_attack("example.com")

    def test_security_helpers(self) -> None:
        self.assertEqual(risk_score(2, 3), 6.0)
        self.assertEqual(risk_score(5, 5), 10.0)
        self.assertEqual(
            deploy_defense(DefenseRule(name="block-ssrf", action="deny")),
            "Deploying runtime protection: block-ssrf:deny",
        )


if __name__ == "__main__":
    unittest.main()
