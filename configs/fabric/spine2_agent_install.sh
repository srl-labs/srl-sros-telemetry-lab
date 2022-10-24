sudo yum localinstall --disablerepo=* /home/admin/srl-ndk-git_0.1.0_linux_amd64.rpm -y
sleep 2
sudo sed -i "s/failure-threshold: 10/failure-action: wait=1/g" /etc/opt/srlinux/appmgr/ndk-git.yml
sr_cli  "/ tools system app-management application app_mgr reload"
sleep 5
sr_cli --candidate-mode --commit-at-end < /home/admin/agent_config_spine2.txt
