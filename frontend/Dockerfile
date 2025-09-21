FROM node:18-alpine as build
WORKDIR /app

# Install dependencies and build the app
COPY package.json .
COPY vite.config.js .
COPY index.html .
COPY src ./src
RUN npm install
RUN npm run build

# Use a lightweight HTTP server to serve the built files
FROM node:18-alpine
WORKDIR /app
RUN npm install -g serve
COPY --from=build /app/dist ./dist
# Expose port 3000
EXPOSE 3000
# Serve the build directory
CMD ["serve", "-s", "dist", "-l", "3000"]