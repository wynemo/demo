https://bugzilla.redhat.com/show_bug.cgi?id=1886805


# CA
certtool --generate-privkey --outfile ca-key.pem
cat > ca.tmpl <<EOF
cn = "rsyslog gnutls test CA"
ca
cert_signing_key
expiration_days = 3650
EOF
certtool --generate-self-signed --template ca.tmpl \
    --load-privkey ca-key.pem --outfile ca-cert.pem

# SERVER
certtool --generate-privkey --outfile server-key.pem
cat > server.tmpl <<EOF
cn = "rsyslog gnutls test server"
dns_name = "1.2.3.4"
tls_www_server
expiration_days = 3650
EOF
certtool --generate-certificate \
    --load-ca-certificate ca-cert.pem --load-ca-privkey ca-key.pem \
    --load-privkey server-key.pem --template server.tmpl \
    --outfile server-cert.pem 



gnutls-serv --priority=NORMAL -p 9000 \
    --x509cafile=./ca-cert.pem \
    --x509certfile=./server-cert.pem \
    --x509keyfile=./server-key.pem 


gnutls-cli --priority=NORMAL -p 9000 \
    --x509cafile=./ca-cert.pem 10.0.10.141




In CentOS/RedHat you also to enable the SSL rsyslog port in SElinux. Something like semanage port -a -t syslogd_port_t -p tcp 10514 should do the trick.

You can check your current syslog port with sudo semanage port -l| grep syslog

Also you can try, to run rsyslog in debug mode, to see whats happening: Stop rsyslog daemon, then

export RSYSLOG_DEBUGLOG="/path/to/debuglog"

export RSYSLOG_DEBUG="Debug"

now start rsyslog with:

rsyslogd -dn

To check if syntax used is valid use:

rsyslogd -N 1





tail -f /var/log/messages
Mar  6 10:40:04 10-0-1-189 systemd: Created slice User Slice of root.
Mar  6 10:40:04 10-0-1-189 systemd-logind: New session 11 of user root.
Mar  6 10:40:04 10-0-1-189 systemd: Started Session 11 of user root.
Mar  6 10:40:04 10-0-1-189 systemd-logind: Removed session 11.
Mar  6 10:40:04 10-0-1-189 systemd: Removed slice User Slice of root.
Mar  6 10:40:44 10-0-1-189 systemd: Created slice User Slice of root.
Mar  6 10:40:44 10-0-1-189 systemd-logind: New session 12 of user root.
Mar  6 10:40:44 10-0-1-189 systemd: Started Session 12 of user root.
Mar  6 10:40:46 10-0-1-189 systemd: Starting System Logging Service...
Mar  6 10:40:46 10-0-1-189 systemd: Started System Logging Service.
Mar  6 10:41:20 10.113.7.64 03/06/2023 06:41:20 PM - INFO - test
Mar  6 10:41:24 10.113.7.64 03/06/2023 06:41:24 PM - INFO - test
Mar  6 10:41:27 10.113.7.64 03/06/2023 06:41:27 PM - INFO - test
