# Build stage: Responsible for building the frontend assets
FROM node:20 AS build

# ACCEPT build-time arguments for Github Actions secrets.
ARG POSTGRES_USER
ARG POSTGRES_PASSWORD
ARG POSTGRES_DB

# Update environment variables with the provided secrets.
ENV POSTGRES_USER=${POSTGRES_USER}
ENV POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
ENV POSTGRES_DB=${POSTGRES_DB}

WORKDIR /app

# Copy package files and install dependencies
COPY web-client/package*.json ./
RUN npm install --legacy-peer-deps

# Copy the entire web-client directory.
# This assumes the API client has already been generated locally
# and exists in `web-client/src/generated/api`.
COPY web-client ./web-client

# Set the working directory and run the standard build command.
WORKDIR /app/web-client
RUN rm -rf dist && npm run build

# Production stage: Responsible for serving the built assets
FROM nginx:alpine

# Copy built assets from the previous build stage
COPY --from=build /app/web-client/dist /usr/share/nginx/html

# Copy the Nginx configuration file
COPY --from=build /app/web-client/nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80 for the web server
EXPOSE 80

# Start Nginx in the foreground
CMD ["nginx", "-g", "daemon off;"]
