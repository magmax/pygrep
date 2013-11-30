#
# Regular cron jobs for the pygrep package
#
0 4	* * *	root	[ -x /usr/bin/pygrep_maintenance ] && /usr/bin/pygrep_maintenance
