#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动修复功能测试示例

这个文件包含了各种常见的代码问题，用于演示自动修复功能。
"""

import os
import sys
import json
from urllib2 import urlopen
from ConfigParser import ConfigParser

def calculate_sum(a, b):
    result = a + b
    unused_variable = 42
    return result

def process_data(data):
    parsed = json.loads(data)
    return parsed

def unused_function():
    pass

def another_unused_function():
    return None

class UnusedClass:
    pass

def main():
    data = "test data"
    count = 0
    count = count + 1
    total = 0
    total = total * 2
    name = "test"
    name = name + "_suffix"

    if False:
        print("This is dead code")

    return process_data(data)

if __name__ == "__main__":
    main()
