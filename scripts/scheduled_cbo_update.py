"""
Scheduled CBO Data Update Script

Phase 5.2: Automated daily data refresh
Fetches latest CBO/Treasury/OMB data and logs any changes.

Usage:
    python scripts/scheduled_cbo_update.py
    
Schedule with Windows Task Scheduler:
    - Run daily at 6:00 AM
    - Action: python.exe
    - Arguments: "E:\\AI Projects\\polisim\\scripts\\scheduled_cbo_update.py"
    - Start in: E:\\AI Projects\\polisim
"""

import logging
import sys
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.cbo_scraper import CBODataScraper

# Configure logging
log_dir = project_root / "logs"
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_dir / "cbo_updates.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def main():
    """Run scheduled CBO data update."""
    logger.info("=" * 60)
    logger.info("Starting scheduled CBO data update")
    logger.info("=" * 60)
    
    try:
        # Create scraper with notifications enabled
        scraper = CBODataScraper(use_cache=True, enable_notifications=True)
        
        # Fetch latest data
        logger.info("Fetching latest CBO/Treasury/OMB data...")
        data = scraper.get_current_us_budget_data()
        
        if not data:
            logger.error("Failed to fetch data - no data returned")
            return 1
        
        # Log summary
        logger.info("-" * 60)
        logger.info("Data Update Summary:")
        logger.info(f"  GDP: ${data['gdp']:.2f}T")
        logger.info(f"  National Debt: ${data['debt']:.2f}T")
        logger.info(f"  Total Revenue: ${sum(data['revenues'].values()):.2f}T")
        logger.info(f"  Total Spending: ${sum(data['spending'].values()):.2f}T")
        logger.info(f"  Deficit: ${data['deficit']:.2f}T")
        logger.info(f"  Interest Rate: {data['interest_rate']:.2f}%")
        logger.info(f"  Last Updated: {data['last_updated']}")
        logger.info(f"  Data Source: {data['data_source']}")
        logger.info("-" * 60)
        
        # Check for changes
        changes = scraper._detect_changes(data)
        if changes:
            logger.warning("⚠️  SIGNIFICANT CHANGES DETECTED:")
            for change in changes:
                logger.warning(f"  • {change}")
        else:
            logger.info("✓ No significant changes detected")
        
        logger.info("=" * 60)
        logger.info("Scheduled update completed successfully")
        logger.info("=" * 60)
        return 0
        
    except Exception as e:
        logger.error(f"Error during scheduled update: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
