import unittest
from scripts.compute import model_allowed, pair_confidence, quota_equivalent_days
from scripts.validate import check_plans

class EvidenceTests(unittest.TestCase):
    def test_unknown_model_is_not_automatically_added(self):
        self.assertFalse(model_allowed({'id': 'new', 'provider': 'Vendor'}, {'model_scope': ['old']}))
        self.assertFalse(model_allowed({'id': 'new'}, {'model_scope': 'any'}))
        self.assertFalse(model_allowed({'id': 'new'}, {}))

    def test_measurement_does_not_transfer_between_models(self):
        plan = {'confidence': 'measured', 'measured_against_model': 'old'}
        self.assertEqual(pair_confidence({'id': 'old'}, plan), 'measured')
        self.assertEqual(pair_confidence({'id': 'new'}, plan), 'medium')

    def test_quota_equivalent_retains_explicit_steady_state_semantics(self):
        self.assertEqual(quota_equivalent_days({}, {}, 100, 100), 30)
        self.assertAlmostEqual(quota_equivalent_days({}, {}, 100, 1), .3)

    def test_access_requires_citation_and_date(self):
        errors, _ = check_plans({'plans': [{'id': 'bad', 'model_scope': ['m'], 'model_access': {'m': {'status': 'listed'}}}]}, set())
        self.assertTrue(any('access evidence' in e for e in errors))

if __name__ == '__main__':
    unittest.main()
