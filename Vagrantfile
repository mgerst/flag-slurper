# -*- mode: ruby -*-
# vi: set ft=ruby :

N = 2

Vagrant.configure("2") do |config|
    config.vm.box = "debian/contrib-stretch64"
    config.vm.synced_folder '.', '/vagrant', disabled: true
    config.ssh.insert_key = false

    config.vm.provider :virtualbox do |v|
        v.memory = 256
        v.cpus = 1
        v.linked_clone = true
    end

    (1..N).each do |n|
        config.vm.define "team#{n}" do |team|
            team.vm.hostname = "team#{n}"
            team.vm.network :private_network, ip: "192.168.3.1#{n}"

            if n == N
                team.vm.provision :ansible do |ansible|
                    ansible.limit = "all"
                    ansible.playbook = "provision/main.yml"
                    ansible.extra_vars = {
                        "apt_cache_enabled": ENV['APT_CACHE_ENABLED'] == "true" || false,
                        "apt_cache_url": ENV['APT_CACHE_URL'],
                    }
                end
            end
        end
    end
end
