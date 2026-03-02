FROM nginx:alpine

# Remove default nginx config
RUN rm /etc/nginx/conf.d/default.conf

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/

# Create directories for static and media files
RUN mkdir -p /app/staticfiles /app/media

# Set proper permissions
RUN chmod -R 755 /app/staticfiles /app/media

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
