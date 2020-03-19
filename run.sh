#!/bin/bash
source /etc/profile
cp -f /plugin/emqx_web_hook.beam /usr/lib/emqx/lib/emqx_web_hook-3.2.7/ebin/
cp -f /plugin/emqx_app.beam /usr/lib/emqx/lib/emqx-3.2.7/ebin/
cp -f /plugin/emqx_listeners.beam /usr/lib/emqx/lib/emqx-3.2.7/ebin/
cp -f /plugin/emqx_mgmt_api_pubsub.beam /usr/lib/emqx/lib/emqx_management-3.2.7/ebin/
cp -f /plugin/emqx_web_hook.conf /etc/emqx/plugins/
cp -f /plugin/loaded_plugins /var/lib/emqx/
service emqx start
cd /redis-4.0.14/
src/redis-server redis.conf
cd /
python3 /plugin/main.py

