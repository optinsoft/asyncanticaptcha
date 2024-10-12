# Async API for anti-captcha.com

## Installation

```bash
pip install git+https://github.com/optinsoft/asyncanticaptcha.git
```

## Usage

```python
from asyncanticaptcha import AsyncAntiCaptcha
import asyncio

async def test(apiKey: str):
    anticaptcha = AsyncAntiCaptcha(apiKey)
    print("getBalance\n", await anticaptcha.getBalance())    

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(test('PUT_YOUR_API_KEY_HERE'))
```
