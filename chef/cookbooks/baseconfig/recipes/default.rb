# Make sure the Apt package lists are up to date, so we're downloading versions that exist.
cookbook_file "apt-sources.list" do
  path "/etc/apt/sources.list"
end
execute 'apt_update' do
  command 'apt-get -o Acquire::Check-Valid-Until=false update; exit 0'
end

# Base configuration recipe in Chef.
package "wget"
package "ntp"
cookbook_file "ntp.conf" do
  path "/etc/ntp.conf"
end
execute 'ntp_restart' do
  command 'service ntp restart'
end

#install python libraries
execute 'install_python' do
  command 'apt-get -y install python'
end

execute 'install_pip' do
  command 'apt-get -y install python-pip'
end

execute 'install_passlib' do
  command 'pip install passlib'
end

execute 'install_flask' do
  command 'pip install flask'
end
execute 'install_flaskmail' do
  command 'pip install Flask-Mail'
end
execute 'install_sqlalchemy' do
  command 'pip install Flask-SQLAlchemy'
end

execute 'install_flaskvia' do
  command 'pip install Flask-Via'
end

execute 'install_wtforms' do
  command 'pip install Flask-WTF'
end

execute 'install_psycopg2' do
  command 'pip install psycopg2-binary'
end

#install nginx web server and configure it.
execute 'install_nginx' do
  command 'apt-get -y install nginx'
end

execute 'copy_nginx_conf' do
	command 'cp /home/vagrant/project/chef/cookbooks/baseconfig/files/default/virtual.conf /etc/nginx/conf.d'
end

execute 'verify_nginx_conf' do
	command 'nginx -t'
end

execute 'reload_nginx' do
	command 'service nginx restart'
end

#install gunicorn web server
execute 'install_gunicorn' do
  command 'pip install gunicorn'
end

execute 'get_update' do
    command 'apt-get -o Acquire::Check-Valid-Until=false update; exit 0'
end

execute 'install_postgresql' do
    command 'apt-get install -y postgresql postgresql-contrib libpq-dev'
end

execute 'install_flaskmigrate' do
    command 'pip install Flask-Migrate'
end

execute 'install_flaskscript' do
	command 'pip install Flask-script'
end

execute 'install_flasksocketio' do
	command 'pip install Flask-socketio'
end

execute 'install_eventlet' do
	command 'pip install eventlet'
end

execute 'install_eventlet' do
  command 'pip install geopy'
end

# only executes the second part of the or statement if the first does not return 1
execute 'remove_database' do
  command 'sudo -u postgres dropdb projectdb'
  ignore_failure true
end

execute 'create_database' do
	command 'sudo -u postgres createdb projectdb'
end

# looks for a user named vagrant, and creates it if it does not find it
execute 'create_vagrant_db_user' do
	command 'sudo -u postgres psql -tAc "SELECT 1 FROM pg_roles WHERE rolname=\'vagrant\';" | grep -q 1 || sudo -u postgres createuser -s vagrant'
end

execute 'set_db_password' do
	command 'sudo -u vagrant psql projectdb --command "ALTER USER vagrant WITH PASSWORD \'vagrant\'; "'
end

#kill any process using port 5002 just as a safety net
execute 'kill_process_using_port' do
  command 'fuser -k 5002/tcp > /dev/null 2>&1; exit 0'
end

#create requirements.txt
execute 'create_requirements' do
  command 'pip freeze > requirements.txt'
end
