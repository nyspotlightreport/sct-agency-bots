#!/usr/bin/env python3
"""
agents/apollo_scale_agent.py
Shim — delegates to bots/apollo_7touch_sequence_bot.py
Exists so any workflow referencing agents/apollo_scale_agent.py works.
"""
import subprocess, sys, os
result = subprocess.run([sys.executable, "bots/apollo_7touch_sequence_bot.py"],
    env=os.environ.copy())
sys.exit(result.returncode)
