#!/bin/bash

# Helper script for Docker Compose operations

case "$1" in
  start)
    echo "Starting services..."
    docker-compose up -d
    echo "Services started. API available at http://localhost:5000"
    ;;
  stop)
    echo "Stopping services..."
    docker-compose down
    echo "Services stopped."
    ;;
  restart)
    echo "Restarting services..."
    docker-compose restart
    echo "Services restarted."
    ;;
  logs)
    echo "Showing logs..."
    docker-compose logs -f
    ;;
  build)
    echo "Building services..."
    docker-compose build
    echo "Build completed."
    ;;
  rebuild)
    echo "Rebuilding and starting services..."
    docker-compose down
    docker-compose build
    docker-compose up -d
    echo "Services rebuilt and started."
    ;;
  status)
    echo "Service status:"
    docker-compose ps
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|logs|build|rebuild|status}"
    exit 1
    ;;
esac

exit 0