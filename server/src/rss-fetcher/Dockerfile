# Build stage
FROM gradle:7.6.4-jdk11 AS build

# Set working directory
WORKDIR /app

# Copy the entire project
COPY . .

# Build the service with debug output and retry mechanism
RUN for i in {1..3}; do \
    gradle :rss-fetcher:build --no-daemon --info && break || \
    if [ $i -eq 3 ]; then exit 1; fi; \
    echo "Build attempt $i failed, retrying in 5 seconds..."; \
    sleep 5; \
    done

# Run stage
FROM openjdk:11-jre-slim

WORKDIR /app

# Copy the built artifact from build stage
COPY --from=build /app/src/rss-fetcher/build/libs/*.jar app.jar

# Expose the service port
EXPOSE 8082

# Command to run the service
CMD ["java", "-jar", "app.jar"] 