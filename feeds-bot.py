#!/usr/bin/python3

import os
import sys
from src.main import Bot


if __name__ == "__main__":
    if not os.path.exists("configs.json"):
        print("Configs file not found!")
        sys.exit(1)

    Bot().run()
