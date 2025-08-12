set -e

# export $(grep -v '^#' /whoer/crontabs/env.vars | xargs)

if [ -f /run/secrets/env ]; then
    export $(grep -v '^#' /run/secrets/env | xargs)
fi

export PYTHONPATH=/whoer:/whoer/crontabs
export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

echo "[cron.sh] $(date): Starting cron job"
echo "Working with GRPC_HOST=$GRPC_HOST"
# echo "[cron.sh] DNS test:" >> /var/log/cron.log
# dig google.com @8.8.8.8 >> /var/log/cron.log 2>&1

echo "[cron.sh] Running new_customer_coupon.py:" >> /var/log/cron.log
cd /whoer/crontabs