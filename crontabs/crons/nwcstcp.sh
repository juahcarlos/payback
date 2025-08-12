#!/bin/bash

. crons/env.sh
/usr/bin/python3 scripts/new_customer_coupon.py >> /var/log/cron.log 2>&1