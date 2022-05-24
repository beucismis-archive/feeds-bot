#!/usr/bin/python3

import os
import sys
from src.main import Bot


if __name__ == "__main__":
    if not os.path.exists("configs.json"):
        sys.exit("Configs file not found!")

    Bot().run()
