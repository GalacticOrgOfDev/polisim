"""Simple runner for healthcare simulation.

Runs a healthcare policy simulation with Monte Carlo uncertainty quantification.
Generates CSV output with year-by-year projections, revenue, spending, and outcomes.

Usage (PowerShell):
    cd "e:\\AI Projects\\polisim"
    python run_health_sim.py [--scenario path/to/scenario.json] [--years 22] [--verbose]

Arguments:
    --scenario PATH    Path to custom scenario JSON file (optional)
    --years N          Number of years to simulate (default: 22)
    --start-year YYYY  Calendar start year (default: 2027)
    --verbose          Enable verbose logging (default: INFO level)

Examples:
    # Run USGHA baseline
    python run_health_sim.py
    
    # Run custom scenario with verbose logging
    python run_health_sim.py --scenario policies/galactic_health_scenario.json --verbose
"""

import os
import sys
import logging
import argparse

# Configure logging
def setup_logging(verbose=False):
    """Configure logging for the application."""
    level = logging.DEBUG if verbose else logging.INFO
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    handler.setFormatter(formatter)
    
    logging.basicConfig(
        level=level,
        handlers=[handler]
    )
    
    # Suppress verbose third-party logs
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

try:
    from core import get_policy_by_type, PolicyType, simulate_healthcare_years
except ImportError as e:
    logger.error(f"Failed to import core modules: {e}")
    logger.error("Make sure you're in the polisim directory and have installed requirements.txt")
    sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Run healthcare simulation with economic projections',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument('--scenario', help='Path to scenario JSON to load', default=None)
    parser.add_argument('--years', type=int, default=22, help='Number of years to simulate')
    parser.add_argument('--start-year', type=int, default=2027, help='Calendar start year')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(verbose=args.verbose)
    logger.info(f"Starting healthcare simulation (verbose={'on' if args.verbose else 'off'})")
    
    try:
        # Load policy
        if args.scenario:
            logger.info(f'Loading scenario from {args.scenario}...')
            try:
                from core.scenario_loader import load_scenario
                policy = load_scenario(args.scenario)
                logger.info(f'Scenario loaded: {policy.policy_name}')
            except FileNotFoundError:
                logger.error(f"Scenario file not found: {args.scenario}")
                sys.exit(1)
            except Exception as e:
                logger.error(f"Failed to load scenario: {e}")
                sys.exit(1)
        else:
            logger.info('Using default USGHA policy')
            policy = get_policy_by_type(PolicyType.USGHA)
            logger.info(f'Policy loaded: {policy.policy_name}')
        
        # Validate policy
        logger.debug(f'Policy parameters: coverage={policy.coverage_percentage:.1%}, gdp_target={policy.healthcare_spending_target_gdp:.1%}')
        
        # Economic parameters
        base_gdp = 29e12  # $29 trillion
        initial_debt = 35e12  # $35 trillion
        population = 335e6  # 335 million
        gdp_growth = 0.025  # 2.5% annual
        
        logger.info(f'Economic assumptions: GDP=${base_gdp/1e12:.1f}T, Debt=${initial_debt/1e12:.1f}T, Pop={population/1e6:.0f}M, Growth={gdp_growth:.1%}')
        logger.info(f'Running {args.years}-year simulation starting in {args.start_year}...')
        
        # Run simulation
        df = simulate_healthcare_years(
            policy,
            base_gdp=base_gdp,
            initial_debt=initial_debt,
            years=args.years,
            population=population,
            gdp_growth=gdp_growth,
            start_year=args.start_year
        )
        
        logger.info(f'Simulation complete. Generated {len(df)} rows of output.')
        
        # Save results
        output_path = os.path.join(os.getcwd(), 'usgha_simulation_22y.csv')
        try:
            df.to_csv(output_path, index=False)
            logger.info(f'Results saved to: {output_path}')
            final_year = df.iloc[-1]["Year"]
            final_spending = df.iloc[-1]["Health Spending ($)"]
            final_coverage = df.iloc[-1].get("Coverage_Pct", 0.0)
            logger.info(f'Final year (year {final_year:g}): Spending=${final_spending/1e12:.2f}T, Coverage={final_coverage:.1%}')
        except IOError as e:
            logger.error(f"Failed to write output file: {e}")
            sys.exit(1)
        
        logger.info('✓ Healthcare simulation completed successfully')
        return 0
        
    except KeyboardInterrupt:
        logger.warning('Interrupted by user')
        return 130
    except Exception as e:
        logger.error(f'Unexpected error: {e}', exc_info=args.verbose)
        return 1


if __name__ == '__main__':
    sys.exit(main())

