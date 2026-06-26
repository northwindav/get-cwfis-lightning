# GeoJSON caching with 365-day expiry.
# Callers provide their own fetch logic via get_or_fetch(cache_key, fetch_func).

import json
import geopandas as gpd
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Callable
import warnings

warnings.filterwarnings('ignore')


class GeoJSONCache:
    """Cache manager for GeoJSON files. Callers supply their own fetch function."""

    def __init__(self, cache_dir: Optional[Path] = None, expiry_days: int = 365):
        if cache_dir is None:
            cache_dir = Path(__file__).parent.parent / '.cache'
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.metadata_file = self.cache_dir / '.metadata.json'
        self.expiry_days = expiry_days
        self.metadata = self._load_metadata()

    def _load_metadata(self) -> dict:
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_metadata(self):
        try:
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            print(f"[CACHE] Warning: failed to save metadata: {e}")

    def _is_expired(self, cache_key: str) -> bool:
        if cache_key not in self.metadata:
            return True
        try:
            ts = datetime.fromisoformat(self.metadata[cache_key]['timestamp'])
            return datetime.now() > ts + timedelta(days=self.expiry_days)
        except Exception:
            return True

    def get_or_fetch(self, cache_key: str, fetch_func: Callable) -> Optional[gpd.GeoDataFrame]:
        """
        Return cached GeoDataFrame if valid, otherwise call fetch_func() to download it.
        fetch_func must return a GeoDataFrame or None.
        Successful results are cached to disk for expiry_days.
        """
        cache_file = self.cache_dir / f"{cache_key}.geojson"

        # Cache hit
        if cache_file.exists() and not self._is_expired(cache_key):
            try:
                gdf = gpd.read_file(cache_file)
                print(f"[CACHE] {cache_key}: {len(gdf)} features loaded from cache")
                return gdf
            except Exception as e:
                print(f"[CACHE] {cache_key}: cache read failed ({e}), re-fetching")
                cache_file.unlink()

        # Cache miss — call caller-supplied fetch
        gdf = fetch_func()

        if gdf is not None:
            try:
                gdf.to_file(cache_file, driver='GeoJSON')
                self.metadata[cache_key] = {
                    'timestamp': datetime.now().isoformat(),
                    'feature_count': len(gdf)
                }
                self._save_metadata()
                print(f"[CACHE] {cache_key}: {len(gdf)} features saved to cache")
            except Exception as e:
                print(f"[CACHE] {cache_key}: failed to save to cache ({e})")

        return gdf

    def clear_cache(self, cache_key: Optional[str] = None):
        if cache_key:
            cache_file = self.cache_dir / f"{cache_key}.geojson"
            if cache_file.exists():
                cache_file.unlink()
            if cache_key in self.metadata:
                del self.metadata[cache_key]
                self._save_metadata()
        else:
            for f in self.cache_dir.glob("*.geojson"):
                f.unlink()
            self.metadata = {}
            self._save_metadata()

    def cache_status(self) -> dict:
        status = {
            'cache_dir': str(self.cache_dir),
            'expiry_days': self.expiry_days,
            'cached_items': {}
        }
        for key, info in self.metadata.items():
            cache_file = self.cache_dir / f"{key}.geojson"
            if cache_file.exists():
                ts = datetime.fromisoformat(info['timestamp'])
                status['cached_items'][key] = {
                    'file': str(cache_file),
                    'downloaded': info['timestamp'],
                    'age_days': (datetime.now() - ts).days,
                    'features': info.get('feature_count', 'unknown'),
                    'expired': self._is_expired(key)
                }
        return status
