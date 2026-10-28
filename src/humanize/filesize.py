"""Bits and bytes related humanization."""

from __future__ import annotations

__lazy_modules__ = {"humanize.i18n"}

from humanize.i18n import _gettext as _

suffixes = {
    "decimal": (
        "kB",
        "MB",
        "GB",
        "TB",
        "PB",
        "EB",
        "ZB",
        "YB",
        "RB",
        "QB",
    ),
    "binary": (
        "KiB",
        "MiB",
        "GiB",
        "TiB",
        "PiB",
        "EiB",
        "ZiB",
        "YiB",
        "RiB",
        "QiB",
    ),
    "gnu": "KMGTPEZYRQ",
}


def _rounded_mantissa(format: str, mantissa: float) -> float | None:
    """Return `mantissa` as rounded by the conversion spec in `format`.

    Only the conversion spec is applied, so text around it (e.g. "Size: %.1f")
    does not need to parse as a number. Returns `None` if `format` does not contain
    exactly one conversion spec or its result is not numeric.
    """
    import re

    specs = [
        spec
        for spec in re.findall(r"%[#0\- +]*\d*(?:\.\d+)?[hlL]?[a-zA-Z%]", format)
        if spec != "%%"
    ]
    if len(specs) != 1:
        return None
    try:
        return float(specs[0] % mantissa)
    except (TypeError, ValueError):
        return None


def naturalsize(
    value: float | str,
    binary: bool = False,
    gnu: bool = False,
    format: str = "%.1f",
) -> str:
    """Format a number of bytes like a human-readable filesize (e.g. 10 kB).

    By default, decimal suffixes (kB, MB) are used.

    Non-GNU modes are compatible with jinja2's `filesizeformat` filter.

    Examples:
        ```pycon
        >>> naturalsize(3000000)
        '3.0 MB'
        >>> naturalsize(300, False, True)
        '300B'
        >>> naturalsize(3000, False, True)
        '2.9K'
        >>> naturalsize(3000, False, True, "%.3f")
        '2.930K'
        >>> naturalsize(3000, True)
        '2.9 KiB'
        >>> naturalsize(10**28)
        '10.0 RB'
        >>> naturalsize(10**34 * 3)
        '30000.0 QB'
        >>> naturalsize(-4096, True)
        '-4.0 KiB'

        ```

    Args:
        value (int, float, str): Integer to convert.
        binary (bool): If `True`, uses binary suffixes (KiB, MiB) with base
            2<sup>10</sup> instead of 10<sup>3</sup>.
        gnu (bool): If `True`, the binary argument is ignored and GNU-style
            (`ls -sh` style) prefixes are used (K, M) with the 2**10 definition.
        format (str): Custom formatter.

    Returns:
        str: Human readable representation of a filesize.
    """
    if gnu:
        suffix = suffixes["gnu"]
    elif binary:
        suffix = suffixes["binary"]
    else:
        suffix = suffixes["decimal"]

    base = 1024 if (gnu or binary) else 1000
    bytes_ = float(value)
    abs_bytes = abs(bytes_)

    if abs_bytes == 1 and not gnu:
        return _("%d Byte") % int(bytes_)

    if abs_bytes < base:
        return f"{int(bytes_)}B" if gnu else _("%d Bytes") % int(bytes_)

    from math import log

    exp = int(min(log(abs_bytes, base), len(suffix)))
    # The suffix is chosen from the unrounded byte count, but `format` rounds the
    # mantissa afterward; rounding can push it up to `base` (e.g. 999999 is
    # 999.999 kB, which formats to "1000.0 kB"). When that happens and a larger
    # suffix is available, step up one suffix so the result reads "1.0 MB".
    if exp < len(suffix):
        rounded = _rounded_mantissa(format, abs_bytes / (base**exp))
        if rounded is not None and abs(rounded) >= base:
            exp += 1
    space = "" if gnu else " "
    ret: str = format % (bytes_ / (base**exp)) + space + _(suffix[exp - 1])
    return ret
