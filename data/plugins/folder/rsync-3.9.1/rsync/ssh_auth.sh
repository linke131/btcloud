#!/usr/bin/expect  

#usage: sudo ./password_free_login.sh root 123456 127.0.0.1
set timeout 10  
set username [lindex $argv 0]  
set password [lindex $argv 1]  
set hostname [lindex $argv 2]  
spawn /usr/bin/ssh-copy-id $username@$hostname
# spawn scp /root/.ssh/id_rsa.pub $username@$hostname:/root/.ssh/authorized_keys
expect {
            #first connect, no public key in ~/.ssh/known_hosts
            "Are you sure you want to continue connecting (yes/no)?" {
            send "yes\r"
            expect "password:"
                send "$password\r"
            }
            #already has public key in ~/.ssh/known_hosts
            "password:" {
                send "$password\r"
            }
            "Now try logging into the machine" {
                #it has authorized, do nothing!
            }
        }
expect eof