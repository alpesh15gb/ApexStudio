# Apex Studio Frontend — Nginx static server
# Build Flutter Web first using: bash infra/scripts/build-frontend.sh
# Then this container serves the pre-built files.

FROM nginx:alpine

# Copy pre-built Flutter web app
COPY ./build/web /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
