"""Day 13 课堂起步：重试装饰器与 dotenv。"""

import functools
import time


def retry_demo(max_attempts=3):
    """TODO: 只对指定异常重试，并 sleep backoff。"""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except RuntimeError:
                    if attempt == max_attempts:
                        raise
                    time.sleep(0.05 * attempt)
            return None

        return wrapper

    return decorator


@retry_demo(max_attempts=3)
def unstable():
    raise RuntimeError("临时失败")


if __name__ == "__main__":
    print("装饰器起步文件，完成 TODO 后运行 unstable()")
