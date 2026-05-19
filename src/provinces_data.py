"""
Canadian provinces and territories data.
Provides a simple GeoJSON-like structure for offline use.
"""

import geopandas as gpd
from shapely.geometry import shape
import json
from pathlib import Path

# Simple GeoJSON feature collection with Canadian provinces/territories
# This is a simplified, minimal version for basic mapping
CANADA_PROVINCES_GEOJSON = {
    "type": "FeatureCollection",
    "features": [
        {
            "type": "Feature",
            "properties": {"name": "Alberta", "code": "AB"},
            "geometry": {"type": "Polygon", "coordinates": [[[[-110, 49], [-110, 60], [-114, 60], [-114, 49], [-110, 49]]]]}
        },
        {
            "type": "Feature",
            "properties": {"name": "British Columbia", "code": "BC"},
            "geometry": {"type": "Polygon", "coordinates": [[[[-114, 49], [-114, 60], [-120, 60], [-120, 49], [-114, 49]]]]}
        },
        {
            "type": "Feature",
            "properties": {"name": "Saskatchewan", "code": "SK"},
            "geometry": {"type": "Polygon", "coordinates": [[[[-102, 49], [-102, 60], [-110, 60], [-110, 49], [-102, 49]]]]}
        },
        {
            "type": "Feature",
            "properties": {"name": "Manitoba", "code": "MB"},
            "geometry": {"type": "Polygon", "coordinates": [[[[-95, 49], [-95, 60], [-102, 60], [-102, 49], [-95, 49]]]]}
        },
        {
            "type": "Feature",
            "properties": {"name": "Ontario", "code": "ON"},
            "geometry": {"type": "Polygon", "coordinates": [[[[-82, 42], [-82, 56], [-95, 56], [-95, 42], [-82, 42]]]]}
        },
        {
            "type": "Feature",
            "properties": {"name": "Quebec", "code": "QC"},
            "geometry": {"type": "Polygon", "coordinates": [[[[-73, 45], [-73, 55], [-82, 55], [-82, 45], [-73, 45]]]]}
        },
        {
            "type": "Feature",
            "properties": {"name": "New Brunswick", "code": "NB"},
            "geometry": {"type": "Polygon", "coordinates": [[[[-66, 45], [-66, 48], [-71, 48], [-71, 45], [-66, 45]]]]}
        },
        {
            "type": "Feature",
            "properties": {"name": "Nova Scotia", "code": "NS"},
            "geometry": {"type": "Polygon", "coordinates": [[[[-61, 43], [-61, 47], [-66, 47], [-66, 43], [-61, 43]]]]}
        },
        {
            "type": "Feature",
            "properties": {"name": "Prince Edward Island", "code": "PE"},
            "geometry": {"type": "Polygon", "coordinates": [[[[-63, 46], [-63, 47], [-62, 47], [-62, 46], [-63, 46]]]]}
        },
        {
            "type": "Feature",
            "properties": {"name": "Newfoundland and Labrador", "code": "NL"},
            "geometry": {"type": "Polygon", "coordinates": [[[[-55, 46], [-55, 61], [-67, 61], [-67, 46], [-55, 46]]]]}
        },
        {
            "type": "Feature",
            "properties": {"name": "Yukon", "code": "YT"},
            "geometry": {"type": "Polygon", "coordinates": [[[[-141, 60], [-141, 70], [-120, 70], [-120, 60], [-141, 60]]]]}
        },
        {
            "type": "Feature",
            "properties": {"name": "Northwest Territories", "code": "NT"},
            "geometry": {"type": "Polygon", "coordinates": [[[[-120, 60], [-120, 85], [-102, 85], [-102, 60], [-120, 60]]]]}
        },
        {
            "type": "Feature",
            "properties": {"name": "Nunavut", "code": "NU"},
            "geometry": {"type": "Polygon", "coordinates": [[[[-102, 60], [-102, 90], [-60, 90], [-60, 60], [-102, 60]]]]}
        }
    ]
}


def load_provinces_geojson() -> gpd.GeoDataFrame:
    """
    Load Canadian provinces/territories from embedded GeoJSON.
    Converts to EPSG:3978 (Canada Albers).
    
    Returns:
        GeoDataFrame with provinces
    """
    try:
        # Convert GeoJSON to GeoDataFrame
        gdf = gpd.GeoDataFrame.from_features(
            CANADA_PROVINCES_GEOJSON['features'],
            crs='EPSG:4326'
        )
        
        # Reproject to Canada Albers
        gdf = gdf.to_crs('EPSG:3978')
        
        print(f"✓ Loaded {len(gdf)} provinces/territories from embedded data")
        return gdf
    except Exception as e:
        print(f"✗ Error loading provinces: {e}")
        return None


def try_download_detailed_provinces() -> gpd.GeoDataFrame:
    """
    Try to download detailed Natural Earth provinces data.
    Falls back to embedded data if network unavailable.
    
    Returns:
        GeoDataFrame with provinces (detailed or fallback)
    """
    import urllib.request
    import zipfile
    import tempfile
    import os
    
    urls = [
        # GitHub mirrors (more reliable on Windows)
        "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson/ne_10m_admin_1_states_provinces.geojson",
        "https://www.naturalearthdata.com/http//www.naturalearthdata.com/download/10m/cultural/ne_10m_admin_1_states_provinces.zip",
    ]
    
    for url in urls:
        try:
            print(f"Attempting to download provinces from: {url[-60:]}")
            
            if url.endswith('.geojson'):
                # Direct GeoJSON download
                print("  (GeoJSON format)")
                with urllib.request.urlopen(url, timeout=15) as response:
                    data = json.load(response)
                
                # Convert GeoJSON to GeoDataFrame
                gdf = gpd.GeoDataFrame.from_features(data['features'], crs='EPSG:4326')
                gdf = gdf.to_crs('EPSG:3978')
                print(f"✓ Downloaded {len(gdf)} provinces/territories from GeoJSON")
                return gdf
                
            else:
                # ZIP file download
                print("  (ZIP format - downloading...)")
                with tempfile.TemporaryDirectory() as tmpdir:
                    zip_path = os.path.join(tmpdir, 'ne_admin.zip')
                    
                    # Download ZIP
                    with urllib.request.urlopen(url, timeout=30) as response:
                        with open(zip_path, 'wb') as out:
                            out.write(response.read())
                    
                    # Extract and read
                    with zipfile.ZipFile(zip_path, 'r') as zf:
                        shp_files = [f for f in zf.namelist() if f.endswith('.shp')]
                        if not shp_files:
                            raise ValueError("No .shp files found in ZIP")
                        
                        shp_file = shp_files[0]
                        print(f"  Reading {shp_file}...")
                        
                        # Extract to temp and read with geopandas
                        extract_dir = os.path.join(tmpdir, 'extracted')
                        zf.extractall(extract_dir)
                        
                        shp_path = os.path.join(extract_dir, shp_file)
                        world = gpd.read_file(shp_path)
                        
                        # Filter for Canada
                        canada_provinces = world[world['admin'] == 'Canada'].copy()
                        
                        if len(canada_provinces) > 0:
                            canada_provinces = canada_provinces.to_crs('EPSG:3978')
                            print(f"✓ Downloaded {len(canada_provinces)} provinces/territories from shapefile")
                            return canada_provinces
        
        except urllib.error.URLError as e:
            print(f"  ✗ Network error: {e.reason}")
            continue
        except Exception as e:
            print(f"  ✗ Error: {type(e).__name__}: {str(e)[:80]}")
            continue
    
    # Fallback to embedded data
    print("Falling back to embedded province data...")
    return load_provinces_geojson()


if __name__ == "__main__":
    # Test
    gdf = load_provinces_geojson()
    if gdf is not None:
        print(f"Loaded {len(gdf)} provinces")
        print(gdf[['name', 'code']].to_string())
