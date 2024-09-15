python version 3.7+
default:
    login    admin
    password admin

```console
git clone https://github.com/opolonix/bulvard
python -m venv venv

./venv/bin/pip install -r requirements.txt
./venv/bin/python uvicorn app:app --port 8700
```

nginx config:
```
server {
    listen  :80;

    server_name bulvard.local www.bulvard.local;

    location / {
        proxy_pass http://localhost:8700;
        proxy_set_header    Host              $host;
        proxy_set_header    X-Real-IP         $remote_addr;
        proxy_set_header    X-Forwarded-For   $proxy_add_x_forwarded_for;
        proxy_set_header    X-Client-Verify   SUCCESS;
        proxy_set_header    X-Client-DN       $ssl_client_s_dn;
        proxy_set_header    X-SSL-Subject     $ssl_client_s_dn;
        proxy_set_header    X-SSL-Issuer      $ssl_client_i_dn;
        proxy_set_header    X-Forwarded-Proto http;
        proxy_read_timeout 1800;
        proxy_connect_timeout 1800;
    }
}
```