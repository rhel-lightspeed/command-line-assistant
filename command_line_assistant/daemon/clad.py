import sys


def daemonize() -> int:
    """Main routine for clad."""
    print("clad!")
    return 0


if __name__ == "__main__":
    sys.exit(daemonize())
