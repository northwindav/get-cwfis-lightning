# Plot strikes on a map of Canada, color-coded by time bin.

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import ListedColormap
from shapely.geometry import Point, box
from pathlib import Path
import warnings

from .provinces_data import try_download_detailed_provinces
from .geojson_cache import GeoJSONCache

warnings.filterwarnings('ignore')


class StrikeMapper:
    
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
       
        self.csv_path = Path(csv_path)
        self.gdf = None
        self.cache = GeoJSONCache()
        
    def load_data(self) -> gpd.GeoDataFrame:
       
        df = pd.read_csv(self.csv_path)
        
        # Parse timestamp
        df['rep_date'] = pd.to_datetime(df['rep_date'], utc=True)
        
        # Create geometry from lon/lat
        geometry = [Point(xy) for xy in zip(df['lon'], df['lat'])]
        self.gdf = gpd.GeoDataFrame(df, geometry=geometry, crs='EPSG:4326')
        
        # Reproject to Canada Albers (EPSG:3978) as default
        self.gdf = self.gdf.to_crs('EPSG:3978')
        
        print(f"Loaded {len(self.gdf)} strikes")
        print(f"CRS: {self.gdf.crs}")
        
        return self.gdf
    
    def load_canada_provinces(self) -> gpd.GeoDataFrame:
       
        return try_download_detailed_provinces()
    
    def _download_natural_earth_rivers(self) -> gpd.GeoDataFrame:
        """Download Natural Earth rivers dataset from online GeoJSON source, with caching."""
        def fetch():
            urls = [
                "https://naciscdn.org/naturalearth/10m/physical/ne_10m_rivers_lake_centerlines.geojson",
                "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_rivers_lake_centerlines.geojson"
            ]
            for url in urls:
                try:
                    gdf = gpd.read_file(url)
                    print(f"Loaded {len(gdf)} river features from {url}")
                    return gdf
                except Exception as e:
                    print(f"Warning: rivers failed from {url}: {e}")
                    continue
            print("Warning: Rivers data not available from any source")
            return None

        return self.cache.get_or_fetch('rivers', fetch)
    
    def _download_natural_earth_lakes(self) -> gpd.GeoDataFrame:
        """Download Natural Earth lakes dataset from online GeoJSON source, with caching."""
        def fetch():
            urls = [
                "https://naciscdn.org/naturalearth/10m/physical/ne_10m_lakes.geojson",
                "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_lakes.geojson"
            ]
            for url in urls:
                try:
                    gdf = gpd.read_file(url)
                    print(f"Loaded {len(gdf)} lake features from {url}")
                    return gdf
                except Exception as e:
                    print(f"Warning: lakes failed from {url}: {e}")
                    continue
            print("Warning: Lakes data not available from any source")
            return None

        return self.cache.get_or_fetch('lakes', fetch)
    
    def _clip_features_to_bounds(self, features: gpd.GeoDataFrame, bounds_geom) -> gpd.GeoDataFrame:
        """Clip feature geodataframe to bounding geometry."""
        if features is None:
            return None
        try:
            clipped = gpd.clip(features, bounds_geom)
            print(f"Clipped features to bounds: {len(clipped)} features remain")
            return clipped if len(clipped) > 0 else None
        except Exception as e:
            print(f"Warning: Failed to clip features: {e}")
            return None
    
    def create_map(self, figsize=(16, 12), output_dir: str = None, hours: int = 24, 
                   bbox: dict = None, region_name: str = None, crs: str = None) -> Path:
        
        if self.gdf is None:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        if output_dir is None:
            output_dir = self.csv_path.parent.parent / 'images'
        
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine projection CRS (default: Canada Albers)
        map_crs = crs if crs else 'EPSG:3978'
        crs_name = 'Canada Albers' if map_crs == 'EPSG:3978' else map_crs
        
        # Create figure with light blue ocean background
        fig, ax = plt.subplots(figsize=figsize, facecolor='#E8F4F8')
        
        # Reproject strike data to target CRS if needed
        if self.gdf.crs != map_crs:
            gdf_plot = self.gdf.to_crs(map_crs)
        else:
            gdf_plot = self.gdf
        
        # Determine map bounds and setup axis
        if bbox is not None:
            # Bounding box mode: project bounds and set axis
            bbox_geom = box(bbox['min_lon'], bbox['min_lat'], bbox['max_lon'], bbox['max_lat'])
            bbox_gdf = gpd.GeoDataFrame([1], geometry=[bbox_geom], crs='EPSG:4326')
            bbox_gdf = bbox_gdf.to_crs(map_crs)
            bbox_proj = bbox_gdf.geometry[0].bounds
            ax.set_xlim(bbox_proj[0], bbox_proj[2])
            ax.set_ylim(bbox_proj[1], bbox_proj[3])
            map_bounds = bbox_geom
        else:
            # Canada-wide mode: use default bounds
            ax.set_xlim(-2800000, 2900000)
            ax.set_ylim(-800000, 3100000)
            map_bounds = box(-141, 40, -55, 85)  # Approximate Canada bounds in WGS84
        
        # Fill entire background with light blue ocean
        ax.set_facecolor("#13A3E6")
        
        # Load and plot provinces/territories
        provinces = self.load_canada_provinces()
        if provinces is not None and len(provinces) > 0:
            # Reproject provinces to target CRS
            if provinces.crs != map_crs:
                provinces = provinces.to_crs(map_crs)
            
            # Plot provinces with light grey fill
            provinces.plot(
                ax=ax,
                color='#E8E8E8',
                edgecolor='none',
                alpha=0.95
            )
            
            # Draw province boundaries
            for idx, row in provinces.iterrows():
                geom = row.geometry
                if geom is None:
                    continue
                if geom.geom_type == 'Polygon':
                    x, y = geom.exterior.xy
                    ax.plot(x, y, color='#000000', linewidth=1.2, zorder=5)
                    for interior in geom.interiors:
                        x, y = interior.xy
                        ax.plot(x, y, color='#000000', linewidth=1.2, zorder=5)
                elif geom.geom_type == 'MultiPolygon':
                    for part in geom.geoms:
                        x, y = part.exterior.xy
                        ax.plot(x, y, color='#000000', linewidth=1.2, zorder=5)
                        for interior in part.interiors:
                            x, y = interior.xy
                            ax.plot(x, y, color='#000000', linewidth=1.2, zorder=5)
            
            print(f"Plotted {len(provinces)} provinces/territories")
        else:
            print("Warning: No provinces loaded")
        
        # Load and plot roads and water features if bbox or region specified
        if bbox is not None or region_name is not None:
            # Download rivers and lakes
            rivers = self._download_natural_earth_rivers()
            lakes = self._download_natural_earth_lakes()
            
            # Clip to map bounds and reproject
            if rivers is not None:
                rivers = self._clip_features_to_bounds(rivers, map_bounds)
                if rivers is not None and rivers.crs != map_crs:
                    rivers = rivers.to_crs(map_crs)
                if rivers is not None and len(rivers) > 0:
                    rivers.plot(ax=ax, color='#4169E1', linewidth=0.8, zorder=2)
            
            if lakes is not None:
                lakes = self._clip_features_to_bounds(lakes, map_bounds)
                if lakes is not None and lakes.crs != map_crs:
                    lakes = lakes.to_crs(map_crs)
                if lakes is not None and len(lakes) > 0:
                    lakes.plot(ax=ax, color='#87CEEB', alpha=0.7, zorder=2)
        
        # Plot strikes by bin (in order so newer ones are on top)
        for bin_name in ['bin_older', 'bin_48h', 'bin_24h', 'bin_12h', 'bin_6h', 'bin_1h']:
            bin_data = gdf_plot[gdf_plot['time_bin'] == bin_name]
            
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
        
        # Add timestamp annotation with projection info
        timestamp_str = pd.Timestamp.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
        ax.text(
            0.98, 0.02,
            f"Generated: {timestamp_str}\nProjection: {map_crs}",
            transform=ax.transAxes,
            fontsize=9,
            ha='right',
            va='bottom',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8)
        )
        
        plt.tight_layout()
        
        # Generate output filename with region name if provided
        timestamp = pd.Timestamp.utcnow().strftime('%Y-%m-%dT%H-%M-%SZ')
        if region_name:
            # Convert region name to title case (e.g., 'british-columbia' -> 'British_Columbia')
            region_label = region_name.replace('-', '_').title()
            output_path = output_dir / f"CLDN_strikes_{hours}h_{region_label}_{timestamp}.png"
        else:
            output_path = output_dir / f"CLDN_strikes_{hours}h_{timestamp}.png"
        
        fig.savefig(output_path, dpi=150, bbox_inches='tight', facecolor='#E8F4F8')
        print(f"Map saved to {output_path}")
        
        plt.close(fig)
        
        return output_path
    
    def get_summary_stats(self) -> dict:
      
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
