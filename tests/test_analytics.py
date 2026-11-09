import unittest
import analytics

class TestAnalytics(unittest.TestCase):
    def test_calculate_runway_positive_burn(self):
        # Current balance 10,000, monthly net burn is 2,000
        runway = analytics.calculate_runway(current_balance=10000.0, monthly_burn=2000.0)
        self.assertEqual(runway["months"], 5.0)
        self.assertFalse(runway["is_infinite"])

    def test_calculate_runway_surplus_or_zero_burn(self):
        # If income exceeds expenses, net burn is <= 0 -> infinite runway
        runway = analytics.calculate_runway(current_balance=10000.0, monthly_burn=-500.0)
        self.assertTrue(runway["is_infinite"])
        self.assertEqual(runway["months"], float("inf"))

    def test_calculate_needed_savings(self):
        # Current balance 2,000; target 5,000 in 6 months -> need 3,000 total / 500 per month
        result = analytics.calculate_needed_savings(
            current_balance=2000.0,
            target_amount=5000.0,
            target_months=6
        )
        self.assertEqual(result["total_needed"], 3000.0)
        self.assertEqual(result["monthly_savings_needed"], 500.0)

    def test_simulate_scenarios_exact_salary(self):
        # Base: Income 3000, Fixed 1000, Variable 1000 => Net monthly +1000
        # What if exact salary becomes 4200/mo?
        # Fixed +100 (1100), Variable -10% (-100 => 900)
        # Net monthly: 4200 - 1100 - 900 = +2200
        sim = analytics.simulate_scenarios(
            starting_balance=5000.0,
            base_monthly_income=3000.0,
            base_fixed_expense=1000.0,
            base_variable_expense=1000.0,
            scenario_monthly_income=4200.0,
            fixed_delta_eur=100.0,
            variable_delta_pct=-10.0,
            months=12
        )
        self.assertEqual(sim["scenario_monthly_income"], 4200.0)
        self.assertEqual(sim["scenario_monthly_net"], 2200.0)
        self.assertEqual(sim["scenario_timeline"][0]["projected_balance"], 7200.0)
        self.assertEqual(sim["scenario_timeline"][11]["projected_balance"], 5000.0 + 2200.0 * 12)

    def test_simulate_scenarios(self):
        # Base: Income 3000, Fixed 1000, Variable 1000 => Net monthly +1000
        # Scenario: Income drops by 10% (-300 => 2700), Fixed goes up by 200 (1200), Variable drops by 20% (800)
        # Net monthly: 2700 - 1200 - 800 = +700
        # Balance starting at 5000:
        # Month 1: 5700, Month 2: 6400, Month 3: 7100, ...
        sim = analytics.simulate_scenarios(
            starting_balance=5000.0,
            base_monthly_income=3000.0,
            base_fixed_expense=1000.0,
            base_variable_expense=1000.0,
            income_delta_pct=-10.0,
            fixed_delta_eur=200.0,
            variable_delta_pct=-20.0,
            months=12
        )
        self.assertEqual(len(sim["baseline_timeline"]), 12)
        self.assertEqual(len(sim["scenario_timeline"]), 12)
        self.assertEqual(sim["scenario_monthly_net"], 700.0)
        self.assertEqual(sim["scenario_timeline"][0]["projected_balance"], 5700.0)
        self.assertEqual(sim["scenario_timeline"][2]["projected_balance"], 7100.0)
        self.assertEqual(sim["scenario_timeline"][11]["projected_balance"], 5000.0 + 700.0 * 12)

if __name__ == "__main__":
    unittest.main()
