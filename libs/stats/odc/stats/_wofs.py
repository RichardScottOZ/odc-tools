"""
Wofs Summary
"""
from typing import Optional
import xarray as xr
from odc.stats.model import Task
from odc.algo.io import load_with_native_transform
from .model import OutputProduct, StatsPluginInterface
from . import _plugins


class StatsWofs(StatsPluginInterface):
    def __init__(
        self, resampling: str = "bilinear",
    ):
        self.resampling = resampling

    def product(self, location: Optional[str] = None, **kw) -> OutputProduct:
        name = "ga_s2_wo_summary"
        short_name = "ga_s2_wo_summary"
        version = "0.0.0"

        if location is None:
            bucket = "deafrica-stats-processing"  # TODO: ??
            location = f"s3://{bucket}/{name}/v{version}"
        else:
            location = location.rstrip("/")

        measurements = ("count_wet", "count_clear", "frequency")

        properties = {
            "odc:file_format": "GeoTIFF",
            "odc:producer": "ga.gov.au",
            "odc:product_family": "statistics",  # TODO: ???
            "platform": "landsat",  # TODO: ???
        }

        return OutputProduct(
            name=name,
            version=version,
            short_name=short_name,
            location=location,
            properties=properties,
            measurements=measurements,
            href=f"https://collections.digitalearth.africa/product/{name}",
        )

    def _native_tr(xx):
        wet = xx.water == 128
        dry = xx.water == 0
        return xr.Dataset(dict(wet=wet, dry=dry))

    def _fuser(xx):
        from odc.algo._masking import _or_fuser

        xx = xx.map(_or_fuser)
        xx.attrs.pop("native", None)
        # TODO: deal with pixels that are both wet and dry after fusing

        return xx

    def input_data(self, task: Task) -> xr.Dataset:
        chunks = {"y": -1, "x": -1}
        groupby = "solar_day"

        xx = load_with_native_transform(
            task.datasets,
            ["water"],
            task.geobox,
            self._native_tr,
            fuser=self._fuser,
            groupby=groupby,
            resampling=self.resampling,
            chunks=chunks,
        )

        return xx

    def reduce(self, xx: xr.Dataset) -> xr.Dataset:
        count_wet = xx.wet.sum(axis=0, dtype="uint16")
        count_dry = xx.dry.sum(axis=0, dtype="uint16")

        # TODO: change to (count_wet+count_dry) once dry/wet are exclusive
        n = (xx.wet + xx.dry).sum(axis=0, dtype="uint16")
        frequency = count_wet.astype("float32") / n

        return xr.Dataset(
            dict(count_wet=count_wet, count_dry=count_dry, frequency=frequency)
        )

    def rgba(self, xx: xr.Dataset) -> Optional[xr.DataArray]:
        return None


_plugins.register("wofs-summary", StatsWofs)
