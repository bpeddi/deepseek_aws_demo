
print("hello")

nginx_config = f"""
server {{
    listen 80;
    location / {{
        proxy_pass http://{{spot_instance.instance_private_ip}}:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "Upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }}
}}  | sudo tee /etc/nginx/conf.d/reverse-proxy.conf
"""

print(nginx_config)
