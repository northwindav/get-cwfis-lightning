"""
Geospatial visualization module for CLDN strikes.
Maps strikes on Canada with color-coded time bins.
Projection: EPSG:3978 (Canada Albers Equal Area Conic)
"""

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import ListedColormap
from shapely.geometry import Point
from pathlib import Path
import warnings

from .provinces_data import try_download_detailed_provinces

warnings.filterwarnings('ignore')


class StrikeMapper:
    """
    Visualizes lightning strikes on a map of Canada.
    Color-codes by time bin.
    """
    
    # Color scheme for bins (5 colors from red=recent to blue=older)
    BIN_COLORS = {
        'bin_1h': '#FF0000',      # Red (most recent)
        'bin_6h': '#FF8800',      # Orange
        'bin_12h': '#FFDD00',     # Yellow
        'bin_24h': '#00AA00',     # Green
        'bin_48h': '#0000FF',     # Blue
        'bin_older': '#666666'    # Gray (oldest)
    }
    
    BIN_LABELS = {
        'bin_1h': 'Past 1h',
        'bin_6h': '1–6h ago',
        'bin_12h': '6–12h ago',
        'bin_24h': '12–24h ago',
        'bin_48h': '24–48h ago',
        'bin_older': '48h+ ago'
    }
    
    def __init__(self, csv_path: str):
        """
        Initialize with binned CSV file.
        
        Args:
            csv_path: Path to CLDN binned CSV (output from binning.py)
        """
        self.csv_path = Path(csv_path)
        self.gdf = None
        
    def load_data(self) -> gpd.GeoDataFrame:
        """Load binned CSV and convert to GeoDataFrame."""
        df = pd.read_csv(self.csv_path)
        
        # Parse timestamp
        df['rep_date'] = pd.to_datetime(df['rep_date'], utc=True)
        
        # Create geometry from lon/lat
        geometry = [Point(xy) for xy in zip(df['lon'], df['lat'])]
        self.gdf = gpd.GeoDataFrame(df, geometry=geometry, crs='EPSG:4326')
        
        # Reproject to Canada Albers (EPSG:3978)
        self.gdf = self.gdf.to_crs('EPSG:3978')
        
        print(f"Loaded {len(self.gdf)} strikes")
        print(f"CRS: {self.gdf.crs}")
        
        return self.gdf
    
    def load_canada_provinces(self) -> gpd.GeoDataFrame:
        """
        Load Canadian provinces and territories.
        Uses embedded data by default, tries to download detailed data if available.
        
        Returns:
            GeoDataFrame with provincial/territorial boundaries
        """
        return try_download_detailed_provinces()
    
    def create_map(self, figsize=(16, 12), output_dir: str = None, hours: int = 24) -> Path:
        """
        Create map visualization of strikes with provincial boundaries.
        
        Args:
            figsize: Figure size (width, height) in inches
            output_dir: Directory to save PNG (default: images/)
            hours: Number of hours in the data (used for title and filename)
            
        Returns:
            Path to saved PNG file
        """
        if self.gdf is None:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        if output_dir is None:
            output_dir = self.csv_path.parent.parent / 'images'
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create figure with light blue ocean background
        fig, ax = plt.subplots(figsize=figsize, facecolor='#E8F4F8')
        
        # Set map extent (Canada bounds in EPSG:3978)
        # Approximate bounds: -2.8M to 2.9M (X), -0.8M to 3.1M (Y)
        ax.set_xlim(-2800000, 2900000)
        ax.set_ylim(-800000, 3100000)
        
        # Fill entire background with light blue ocean
        ax.set_facecolor('#B3E5FC')
        
        # Load and plot provinces/territories
        provinces = self.load_canada_provinces()
        if provinces is not None and len(provinces) > 0:
            # Plot provinces with light grey fill
            provinces.plot(
                ax=ax,
                color='#E8E8E8',      # Light grey
                edgecolor='none',     # No edge color from plot call
                alpha=0.95
            )
            
            # Explicitly draw all boundaries in black with explicit linewidth
            for idx, row in provinces.iterrows():
                geom = row.geometry
                if geom.geom_type == 'Polygon':
                    # Draw exterior ring
                    x, y = geom.exterior.xy
                    ax.plot(x, y, color='#000000', linewidth=1.2, zorder=5)
                    # Draw holes (interior rings)
                    for interior in geom.interiors:
                        x, y = interior.xy
                        ax.plot(x, y, color='#000000', linewidth=1.2, zorder=5)
                elif geom.geom_type == 'MultiPolygon':
                    # Handle multipart geometries
                    for part in geom.geoms:
                        x, y = part.exterior.xy
                        ax.plot(x, y, color='#000000', linewidth=1.2, zorder=5)
                        for interior in part.interiors:
                            x, y = interior.xy
                            ax.plot(x, y, color='#000000', linewidth=1.2, zorder=5)
            
            print(f"✓ Plotted {len(provinces)} provinces/territories with black boundaries")
        else:
            print("Warning: No provinces loaded")
        
        # Plot strikes by bin (in order so newer ones are on top)
        for bin_name in ['bin_older', 'bin_48h', 'bin_24h', 'bin_12h', 'bin_6h', 'bin_1h']:
            bin_data = self.gdf[self.gdf['time_bin'] == bin_name]
            
            if len(bin_data) > 0:
                ax.scatter(
                    bin_data.geometry.x,
                    bin_data.geometry.y,
                    c=self.BIN_COLORS.get(bin_name, '#999999'),
                    s=20,
                    alpha=0.7,
                    edgecolors='black',
                    linewidth=0.5,
                    label=f"{self.BIN_LABELS[bin_name]} ({len(bin_data):,})"
                )
        
        # Formatting
        ax.set_xlabel('Easting (m)', fontsize=11)
        ax.set_ylabel('Northing (m)', fontsize=11)
        ax.set_title(f'Canadian Lightning Strikes ({hours} hours)', 
                     fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.2, linestyle='--', color='#666666')
        
        # Legend
        handles, labels = ax.get_legend_handles_labels()
        if handles:
            ax.legend(
                handles, labels,
                loc='lower left',
                fontsize=10,
                title='Time Bin (Strike Count)',
                title_fontsize=11,
                framealpha=0.95
            )
        
        # Add timestamp annotation
        timestamp_str = pd.Timestamp.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        ax.text(
            0.98, 0.02,
            f"Generated: {timestamp_str}\nProjection: EPSG:3978 (Canada Albers)",
            transform=ax.transAxes,
            fontsize=9,
            ha='right',
            va='bottom',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8)
        )
        
        plt.tight_layout()
        
        # Save figure
        timestamp = pd.Timestamp.utcnow().strftime('%Y-%m-%dT%H-%M-%SZ')
        output_path = output_dir / f"CLDN_strikes_{hours}h_{timestamp}.png"
        
        fig.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='#E8F4F8')
        print(f"Map saved to {output_path}")
        
        plt.close(fig)
        
        return output_path
    
    def get_summary_stats(self) -> dict:
        """Return summary statistics."""
        if self.gdf is None:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        stats = {
            'total_strikes': len(self.gdf),
            'date_range': {
                'min': self.gdf['rep_date'].min(),
                'max': self.gdf['rep_date'].max()
            },
            'bounds': {
                'lon': {'min': self.gdf.geometry.bounds['minx'].min(),
                        'max': self.gdf.geometry.bounds['maxx'].max()},
                'lat': {'min': self.gdf.geometry.bounds['miny'].min(),
                        'max': self.gdf.geometry.bounds['maxy'].max()}
            },
            'bin_counts': self.gdf['time_bin'].value_counts().to_dict()
        }
        return stats


def main():
    """Test mapper with binned data."""
    binned_csv = "tmp/CLDN_binned_24h_2026-05-19T22-14-22Z.csv"
    
    mapper = StrikeMapper(binned_csv)
    mapper.load_data()
    
    # Print summary
    stats = mapper.get_summary_stats()
    print("\n=== Summary Statistics ===")
    print(f"Total strikes: {stats['total_strikes']:,}")
    print(f"Date range: {stats['date_range']['min']} to {stats['date_range']['max']}")
    print(f"Longitude range: {stats['bounds']['lon']['min']:.2f}° to {stats['bounds']['lon']['max']:.2f}°")
    print(f"Latitude range: {stats['bounds']['lat']['min']:.2f}° to {stats['bounds']['lat']['max']:.2f}°")
    print("\nBin distribution:")
    for bin_name, count in stats['bin_counts'].items():
        print(f"  {bin_name}: {count:,}")
    
    # Create map
    map_path = mapper.create_map()
    print(f"\nMap created: {map_path}")
    
    return mapper


if __name__ == "__main__":
    mapper = main()
