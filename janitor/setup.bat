@echo off
echo Installing Dependencies.. && pip install paramiko pyyaml && cls
start /B python bootfile_syncer.py
for /f "delims=" %%i in ('python -c "import yaml, sys; print(yaml.safe_load(open('config.yaml'))['ssh']['username'] + '@' + yaml.safe_load(open('config.yaml'))['ssh']['hostname'])"') do set SSH_TARGET=%%i
ssh %SSH_TARGET%