# -*- mode: ruby -*-
# vi: set ft=ruby :

VAGRANTFILE_API_VERSION = "2"

Vagrant.configure(VAGRANTFILE_API_VERSION) do |config|
  config.vm.box = "ubuntu/bionic64"

  # Create a forwarded port mapping which allows access to a specific port
  # within the machine from a port on the host machine. In the example below,
  # accessing "localhost:8080" will access port 80 on the guest machine.
  
  #port 5002 used for flask connection
  config.vm.network "forwarded_port", guest: 5002, host: 5002
  #port 5432 used for sql server
  config.vm.network "forwarded_port", guest: 5432, host: 5232


  # Share an additional folder to the guest VM. The first argument is
  # the path on the host to the actual folder. The second argument is
  # the path on the guest to mount the folder. And the optional third
  # argument is a set of non-required options.
  config.vm.synced_folder "./", "/home/vagrant/project"
  # config.vm.synced_folder "../data", "/vagrant_data"

  # Provider-specific configuration so you can fine-tune various
  # backing providers for Vagrant. These expose provider-specific options.
  # If you need to more than double the defaults for this course, you have
  # done something wrong.
  cpus = "1"
  memory = "1024" # MB
  config.vm.provider :virtualbox do |vb|
    vb.customize ["modifyvm", :id, "--cpus", cpus, "--memory", memory]
    vb.customize ["modifyvm", :id, "--uartmode1", "disconnected"] # speed up boot https://bugs.launchpad.net/cloud-images/+bug/1627844
    #vb.gui = true
  end

  # Enable provisioning with chef solo, specifying a cookbooks path, roles
  # path, and data_bags path (all relative to this Vagrantfile), and adding
  # some recipes and/or roles.


  config.vm.provision "chef_solo" do |chef|
    chef.cookbooks_path = "chef/cookbooks"
    chef.add_recipe "baseconfig"
    #chef.channel = "stable"
    #chef.version = "12.10.24"
  end
end
