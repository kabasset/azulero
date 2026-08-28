# SPDX-FileCopyrightText: Copyright (C) 2025-2026, Antoine Basset
# SPDX-PackageSourceInfo: https://github.com/kabasset/azulero
# SPDX-License-Identifier: Apache-2.0


def retry(retries=2, exceptions=Exception, default=None, logger=None):
    """
    Decorator to retry a callable.
    """

    def decorate(func):

        def call(*args, **kwargs):

            r = 0
            while r <= retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    r += 1
                    if logger is not None:
                        if r <= retries:
                            logger.warning(f"Caught error: {e}. Retry {r}/{retries}.")
                        else:
                            logger.error(f"Caught error: {e}. Last retry failed.")
                            logger.exception(e)
            return default

        return call

    return decorate
