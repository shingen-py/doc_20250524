# create databases
CREATE DATABASE IF NOT EXISTS `keycloak`;

# create root user and grant rights
GRANT ALL PRIVILEGES ON *.* TO 'root'@'%';

CREATE USER 'keycloak_db_admin'@'%' IDENTIFIED BY 'ahUJAw8,cEzO';
GRANT ALL PRIVILEGES ON keycloak.* TO 'keycloak_db_admin'@'%' WITH GRANT OPTION;