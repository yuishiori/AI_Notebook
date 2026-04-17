# Stage 1: Build static assets
FROM node:20-slim AS build

WORKDIR /app

# Hardcode Backend API URL for production build (Must start with VITE_)
ENV VITE_API_BASE_URL=https://ai-backend-948232157149.asia-east1.run.app/api

COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf

# Default port for Cloud Run
EXPOSE 8080

CMD ["nginx", "-g", "daemon off;"]
