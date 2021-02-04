#!/usr/bin/env python

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from src.update import update, check_update
import pytest


class run_args():
    def __init__(self, use_db = False, refresh = False):
        self.refresh = refresh
        self.out_html = './out.html'
        self.datadir = os.path.dirname(os.path.abspath(__file__)) + '../data'

@pytest.fixture
def input():
    return run_args()

def test_check():
    check_update()


def test_update_using_data(input):
    update(input)

