#
# 3. PostgreSQL with password
#
apt-get update && apt install -y postgresql
service postgresql start

# 3.1. Setting up password
PG_PASSWORD='password'
sudo -u postgres psql --quiet --command "ALTER USER postgres WITH PASSWORD '${PG_PASSWORD}';"
sudo -u postgres psql --quiet --command "CREATE DATABASE uba_test;"

# 3.2. Md5 instead of peer
PG_HBA_FILE=$(sudo -u postgres psql -t -c "SHOW hba_file;" | xargs)

# allow local connections
sed -ri "s/^(local[[:space:]]+all[[:space:]]+postgres[[:space:]]+).*/\\1md5/" "$PG_HBA_FILE"
sed -ri "s/^(local[[:space:]]+all[[:space:]]+all[[:space:]]+).*/\\1md5/"   "$PG_HBA_FILE"

# 3.3. Reload config
service postgresql reload

#
# 4. Check
#
echo ">>> Checking password connection to PostgreSQL"
PGPASSWORD="${PG_PASSWORD}" psql -U postgres -h localhost -d postgres -c '\conninfo' --quiet
