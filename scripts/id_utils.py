#!/usr/bin/env python3
from __future__ import annotations
import re
from urllib.parse import urlparse

RM_HOSTS = {'researchmap.jp', 'www.researchmap.jp'}


def researchmap_parts(url: str):
    """Return (collection, record_id) from a ResearchMap record URL.

    Example:
      https://researchmap.jp/o-morikawa/presentations/54946770
      -> ('presentations', '54946770')
    """
    if not url:
        return None
    p = urlparse(url)
    if p.netloc.lower() not in RM_HOSTS:
        return None
    seg = [x for x in p.path.split('/') if x]
    if len(seg) < 3:
        return None
    collection, rid = seg[-2], seg[-1]
    if not re.fullmatch(r'\d+', rid):
        return None
    return collection, rid


def id_from_researchmap_url(url: str):
    parts = researchmap_parts(url)
    if not parts:
        raise ValueError(f'Not a ResearchMap record URL: {url}')
    collection, rid = parts
    return f'researchmap:{collection}:{rid}'


def promote_id(record: dict, new_id: str):
    """Promote a source-native identifier and retain old IDs as aliases."""
    old = record.get('id')
    if old == new_id:
        return record
    aliases = list(record.get('legacy_ids') or [])
    if old and old not in aliases:
        aliases.append(old)
    # Do not retain the canonical id as an alias.
    aliases = [x for i, x in enumerate(aliases) if x != new_id and x not in aliases[:i]]
    if aliases:
        record['legacy_ids'] = aliases
    elif 'legacy_ids' in record:
        record.pop('legacy_ids', None)
    record['id'] = new_id
    return record
