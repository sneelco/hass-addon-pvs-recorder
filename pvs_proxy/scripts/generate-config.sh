#!/bin/sh
set -e

echo "Generating nginx IP allowlist from ALLOWED_IPS: $ALLOWED_IPS"

# Create the config directory if it doesn't exist
mkdir -p /etc/nginx/conf.d

# Generate allowlist file
echo "# Generated IP allowlist - $(date)" > /etc/nginx/conf.d/allowed_ips.conf

# Handle empty or unset ALLOWED_IPS
if [ -z "$ALLOWED_IPS" ]; then
    echo "Warning: ALLOWED_IPS is empty, allowing all IPs"
    echo "# No IP restrictions" >> /etc/nginx/conf.d/allowed_ips.conf
else
    # Parse comma-separated IPs using POSIX-compliant method
    echo "$ALLOWED_IPS" | tr ',' '\n' | while IFS= read -r ip; do
        # Trim whitespace
        ip=$(echo "$ip" | sed 's/^[[:space:]]*//;s/[[:space:]]*$//')
        if [ -n "$ip" ]; then
            echo "allow $ip;" >> /etc/nginx/conf.d/allowed_ips.conf
            echo "Added allow rule for: $ip"
        fi
    done
    echo "deny all;" >> /etc/nginx/conf.d/allowed_ips.conf
fi

echo "Generated config:"
cat /etc/nginx/conf.d/allowed_ips.conf
echo "Config generation complete"