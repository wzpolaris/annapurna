import logging
from typing import Any, Optional

import diskcache as dc


class CacheWithLogging(dc.Cache):
    def __init__(self, *args, logger: Optional[logging.Logger] = None, **kwargs):
        super().__init__(*args, **kwargs)
        self.logger = logger or logging.getLogger('diskcache')
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s %(message)s'))
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

    # --- Reads ---
    def __getitem__(self, key: Any) -> Any:
        value = super().__getitem__(key)  # raises KeyError on miss
        self.logger.info('cache_hit key=%r', key)
        return value

    def get(self, key: Any, default: Any = None, *, read: bool = True, retry: bool = False) -> Any:
        sentinel = object()
        value = super().get(key, sentinel, read=read, retry=retry)
        if value is sentinel:
            return default
        self.logger.info('cache_hit key=%r', key)
        return value

    # --- Writes ---
    def __setitem__(self, key: Any, value: Any) -> None:
        is_new = key not in self
        super().__setitem__(key, value)
        if is_new:
            self.logger.info('store_new key=%r', key)

    def set(
        self,
        key: Any,
        value: Any,
        expire: Optional[float] = None,
        read: bool = False,
        tag: Any = None,
        retry: bool = False,
    ) -> bool:
        is_new = key not in self
        stored = super().set(key, value, expire=expire, read=read, tag=tag, retry=retry)
        if stored and is_new:
            self.logger.info('store_new key=%r', key)
        return stored

    def add(
        self,
        key: Any,
        value: Any,
        expire: Optional[float] = None,
        read: bool = False,
        tag: Any = None,
        retry: bool = False,
    ) -> bool:
        stored = super().add(key, value, expire=expire, read=read, tag=tag, retry=retry)
        if stored:
            self.logger.info('store_new key=%r', key)
        return stored
