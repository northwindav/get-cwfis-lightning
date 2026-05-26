# Bin lightning data based on time since strike

import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

# Bins are currently hard coded:
#    - bin_1h: past 1 hour
#    - bin_6h: past 6 hours (excluding 1h bin)
#    - bin_12h: past 12 hours (excluding 1h, 6h bins)
#    - bin_24h: past 24 hours (excluding 1h, 6h, 12h bins)
#    - bin_48h: past 48 hours (excluding all previous bins)
#    - bin_older: 48+ hours ago
class StrikeBinner:
    
    BIN_THRESHOLDS = {
        'bin_1h': 1,
        'bin_6h': 6,
        'bin_12h': 12,
        'bin_24h': 24,
        'bin_48h': 48
    }
    
    # Init with path to csv file.
    def __init__(self, csv_path: str):
      
        self.csv_path = Path(csv_path)
        self.df = None
        self.binned_df = None
        self.reference_time = None
        
    def load_csv(self) -> pd.DataFrame:

        self.df = pd.read_csv(self.csv_path)
        
        # Parse rep_date as datetime. Should be in UTC.
        self.df['rep_date'] = pd.to_datetime(self.df['rep_date'], utc=True)
        
        # Use the maximum timestamp as reference (most recent strike)
        self.reference_time = self.df['rep_date'].max()
        
        print(f"Loaded {len(self.df)} strikes from {self.csv_path}")
        print(f"Date range: {self.df['rep_date'].min()} to {self.df['rep_date'].max()}")
        print(f"Reference time (most recent): {self.reference_time}")
        
        return self.df
    
    # Do the binning. Strikes are assigned to a single bin and there is no overlap in bins.
    def bin_strikes(self) -> pd.DataFrame:
   
        if self.df is None:
            raise ValueError("CSV not loaded. Call load_csv() first.")
        
        # Calculate hours elapsed since reference time for each strike
        self.df['hours_elapsed'] = (
            (self.reference_time - self.df['rep_date']).dt.total_seconds() / 3600
        )
        
        # Initialize bin assignment (will be one of the bin names above)
        self.df['time_bin'] = 'bin_older'
        
        # Assign bins in reverse order (oldest threshold first)
        # so that recent bins override older bins
        self.df.loc[self.df['hours_elapsed'] < 48, 'time_bin'] = 'bin_48h'
        self.df.loc[self.df['hours_elapsed'] < 24, 'time_bin'] = 'bin_24h'
        self.df.loc[self.df['hours_elapsed'] < 12, 'time_bin'] = 'bin_12h'
        self.df.loc[self.df['hours_elapsed'] < 6, 'time_bin'] = 'bin_6h'
        self.df.loc[self.df['hours_elapsed'] < 1, 'time_bin'] = 'bin_1h'
        
        self.binned_df = self.df.copy()
        
        return self.binned_df
    
    # Simple counts by bin for mapping and for sanity checking
    def get_bin_stats(self) -> dict:

        if self.binned_df is None:
            raise ValueError("Strikes not binned. Call bin_strikes() first.")
        
        stats = {}
        for bin_name in list(self.BIN_THRESHOLDS.keys()) + ['bin_older']:
            count = (self.binned_df['time_bin'] == bin_name).sum()
            stats[bin_name] = count
        
        # Verify no duplicates and all strikes accounted for
        total_binned = sum(stats.values())
        assert total_binned == len(self.binned_df), \
            f"Binning error: {total_binned} binned but {len(self.binned_df)} total"
        
        return stats
    
    def export_binned_csv(self, output_dir: str = None, hours: int = 24) -> Path:
     
        if self.binned_df is None:
            raise ValueError("Strikes not binned. Call bin_strikes() first.")
        
        if output_dir is None:
            output_dir = self.csv_path.parent
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.utcnow().strftime('%Y-%m-%dT%H-%M-%SZ')
        output_path = output_dir / f"CLDN_binned_{hours}h_{timestamp}.csv"
        
        # Keep only relevant columns for output
        export_cols = ['cld_id', 'rep_date', 'lon', 'lat', 'peak_current', 
                       'num_sensor', 'time_bin', 'hours_elapsed']
        
        self.binned_df[export_cols].to_csv(output_path, index=False)
        
        print(f"Exported binned data to {output_path}")
        
        return output_path
