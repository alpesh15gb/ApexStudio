# Flutter Web build stage
FROM flutter:3.22 AS build

WORKDIR /app

# Copy project files
COPY . .

# Get dependencies
RUN flutter pub get

# Build for web
RUN flutter build web --release

# Production stage with Nginx
FROM nginx:alpine

# Copy Flutter web build
COPY --from=build /app/build/web /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
