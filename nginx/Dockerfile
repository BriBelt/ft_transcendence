FROM nginx:latest

# Install OpenSSL to generate certificates
RUN apt-get update && apt-get install -y openssl && apt-get clean

# Create directory for SSL certificates
RUN mkdir -p /etc/nginx/certs

# Generate auto-signed SSL certificate and private key
RUN openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/nginx/certs/cert.key \
    -out /etc/nginx/certs/cert.pem \
    -subj "/C=US/ST=State/L=City/O=Organization/OU=Unit/CN=domain-name.com"

# Copiar custom nginx.conf
#COPY nginx.conf /etc/nginx/conf.d/nginx.conf
COPY nginx.conf.template /etc/nginx/nginx.conf.template


COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]

# Reemplazar your-domain.com con el hostname real en nginx.conf
#RUN sh -c "HOSTNAME=$(cat /etc/nginx/.hostname.txt) && \
#    sed 's/your-domain.com/'\"$HOSTNAME\"'/g' /etc/nginx/nginx.conf.template > /etc/nginx/nginx.conf"

# Exponer el puerto 443 para HTTPS
EXPOSE 443
