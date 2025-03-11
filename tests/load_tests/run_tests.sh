#!/bin/bash

cat /proc/meminfo | grep Active:

for users in 1 2 3 4 6 8 16 32
do
   echo "Users: $users"
   locust -f locust_suggestions_by_category.py --users $users --spawn-rate 1 --headless -t 1m -H "http://localhost:8000" --only-summary
   echo RAM
   cat /proc/meminfo | grep Active:
   echo
done