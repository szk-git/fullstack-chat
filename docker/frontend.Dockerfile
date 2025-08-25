# Frontend Dockerfile for local development
FROM node:18-alpine

# Set working directory
WORKDIR /app

# Copy package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY frontend/src ./src
COPY frontend/public ./public
COPY frontend/index.html ./
COPY frontend/vite.config.js ./

# Expose port
EXPOSE 5173

# Start development server
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
