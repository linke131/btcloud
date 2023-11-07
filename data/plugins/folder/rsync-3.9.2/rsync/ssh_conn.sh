#!/usr/bin/expect  
set timeout 10  
set username [lindex $argv 0]  
set password [lindex $argv 1]  
set hostname [lindex $argv 2]  
spawn ssh-keygen -t rsa -q -P "" -f /root/.ssh/id_rsa
expect {
        "Overwrite (y/n)?" {
        send "y\r"
        # expect "password:"
        #     send "$password\r"
        # }
        # #already has public key in ~/.ssh/known_hosts
        # "password:" {
        #     send "$password\r"
        # }
        # "Now try logging into the machine" {
        #     #it has authorized, do nothing!
        # }
    }
expect eof