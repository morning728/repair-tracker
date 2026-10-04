"""Check the health endpoint without extra packages."""

import json
import sys
import time
import urllib.error
import urllib.request


def check(url, attempts=12):
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(url, timeout=5) as response:
                if response.status == 200 and json.load(response).get('status') == 'ok':
                    print(f'Application and database are healthy: {url}')
                    return
        except (urllib.error.URLError, TimeoutError, ValueError) as error:
            print(f'Health attempt {attempt + 1}: {error}', file=sys.stderr)
        if attempt + 1 < attempts:
            time.sleep(5)
    raise SystemExit('Application did not become healthy')


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python3 ci/check_health.py URL')
    check(sys.argv[1])
