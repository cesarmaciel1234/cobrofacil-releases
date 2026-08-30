# Flask/Werkzeug piden importlib.metadata.version(); el EXE a veces no trae dist-info.
import sys

if getattr(sys, "frozen", False):
    try:
        import importlib.metadata as md

        _orig = md.version

        def version(distribution_name):
            try:
                return _orig(distribution_name)
            except md.PackageNotFoundError:
                return "0"

        md.version = version
    except Exception:
        pass
