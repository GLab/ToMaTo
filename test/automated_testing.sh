#!/bin/bash
cd "$(dirname "$0")"

bash start_test_environment.sh
bash do_testing.sh
bash stop_test_environment.sh
