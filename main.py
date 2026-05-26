#!/usr/bin/env python3

# CLI entry point for CLDN lightning retrieval and plotting
# See README for requirements and usage instructions

# Usage example
# python main.py --hours 48 <--output-dir ./output_dir> <-v>

import argparse
import sys
import logging
from pathlib import Path
from datetime import datetime

# Import custom modules
from src.config import DB_CONFIG, OUTPUT_DIR
from src.db_connector import LightningDBConnector
from src.binning import StrikeBinner
from src.mapper import StrikeMapper


# Setup logging
def setup_logging(verbose: bool = False) -> logging.Logger:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    return logging.getLogger(__name__)

# args:
# hours: # of hours back from current time to request via query
# output_dir (optional): Default is workspace root. 
# verbose: Enables debug level logging. 
def run_pipeline(hours: int = 24, output_dir: Path = None, verbose: bool = False) -> dict:

    logger = setup_logging(verbose)
    
    logger.info(f"Starting CLDN pipeline (hours={hours})")
    
    if output_dir is None:
        output_dir = Path(__file__).parent
    else:
        output_dir = Path(output_dir)
    
    tmp_dir = output_dir / 'tmp'
    images_dir = output_dir / 'images'
    tmp_dir.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(parents=True, exist_ok=True)
    
    results = {}
    
    try:
        # Query the database
        logger.info(f"Querying database for past {hours}h...")
        
        db = LightningDBConnector()
        db.connect()
        logger.info(f"Connected to {DB_CONFIG['host']}:{DB_CONFIG['database']}")
        
        df = db.query_strikes(hours=hours)
        logger.info(f"Retrieved {len(df):,} strikes")
        
        csv_path = db.export_to_csv(df, hours=hours)
        logger.info(f"Exported CSV: {csv_path}")
        results['raw_csv'] = csv_path
        
        db.close()
        
        # Bin strikes by age 
        logger.info("Binning strikes by time window...")
        
        binner = StrikeBinner(str(csv_path))
        binner.load_csv()
        binner.bin_strikes()
        
        stats = binner.get_bin_stats()
        logger.info("Bin statistics:")
        for bin_name, count in stats.items():
            if count > 0:
                logger.info(f"  {bin_name}: {count:,} strikes")
        
        binned_csv = binner.export_binned_csv(output_dir=tmp_dir, hours=hours)
        results['binned_csv'] = binned_csv
        
        # Create the map
        logger.info("Creating map visualization...")
        
        mapper = StrikeMapper(str(binned_csv))
        mapper.load_data()
        
        map_stats = mapper.get_summary_stats()
        logger.info(f"Map extent: {map_stats['bounds']['lon']['min']:.2f}° to "
                   f"{map_stats['bounds']['lon']['max']:.2f}° (lon), "
                   f"{map_stats['bounds']['lat']['min']:.2f}° to "
                   f"{map_stats['bounds']['lat']['max']:.2f}° (lat)")
        
        map_path = mapper.create_map(output_dir=images_dir, hours=hours)
        results['map_png'] = map_path
        
        logger.info("Completed successfully!")
        logger.info(f"\nOutput files:")
        logger.info(f"  Raw CSV:    {results['raw_csv']}")
        logger.info(f"  Binned CSV: {results['binned_csv']}")
        logger.info(f"  Map PNG:    {results['map_png']}")
        
        return results
        
    except Exception as e:
        logger.error(f"Failed with exception(s): {e}", exc_info=verbose)
        sys.exit(1)


def main():

    parser = argparse.ArgumentParser(
        description='CLDN Lightning Strike retrieval and plotting',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                    # Extract 24h data and map
  python main.py --hours 12         # Extract 12h data and map
  python main.py --hours 48 --output-dir ./output # 48 hour map with user-specified output directory
  python main.py -v                 # Verbose logging
        """
    )
    
    parser.add_argument(
        '--hours',
        type=int,
        default=24,
        help='Number of hours to extract (default: 24)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='Output directory (default: workspace root)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Validate hours
    if args.hours <= 0:
        parser.error("--hours must be positive")
    if args.hours > 168:  # 1 week
        print("Warning: Requesting data older than 1 week (hours > 168). This could be huge and slow")
    
    # Run pipeline
    results = run_pipeline(
        hours=args.hours,
        output_dir=args.output_dir,
        verbose=args.verbose
    )
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
