FROM node:18-alpine
WORKDIR /app

# Install dependencies
COPY package.json .
COPY vite.config.js .
COPY index.html .
COPY src ./src
RUN npm install

# Expose port 5173 for Vite dev server
EXPOSE 5173

# Run Vite dev server with proxy support
CMD ["npm", "run", "dev"]
