"""Simple self test for measuring FPS performance."""
import time

TARGET_FPS = 30.0


def run_selftest(duration: float = 1.0, target_fps: float = TARGET_FPS) -> float:
    """Measure loop FPS and warn if below target.

    Parameters
    ----------
    duration: float
        How long to run the test in seconds.
    target_fps: float
        Desired frames per second threshold.

    Returns
    -------
    float
        Measured frames per second.
    """
    start = time.perf_counter()
    last = start
    frames = 0
    while time.perf_counter() - start < duration:
        now = time.perf_counter()
        dt = now - last
        last = now
        sleep_time = max(0.0, (1.0 / target_fps) - dt)
        time.sleep(sleep_time)
        frames += 1
    fps = frames / (time.perf_counter() - start)
    if fps < target_fps:
        print(f"Warning: measured FPS {fps:.1f} < {target_fps}")
    return fps


if __name__ == "__main__":
    run_selftest()
