FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY frontend_v2/package*.json ./

# Install dependencies
RUN npm ci

# Copy the rest of the application
COPY frontend_v2/ .

# Build the Next.js application
RUN npm run build

# Production image
FROM node:20-alpine

WORKDIR /app

# Copy built assets and dependencies from builder
COPY --from=builder /app/package*.json ./
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/node_modules ./node_modules

# Expose port
EXPOSE 3000

# Start the application
CMD ["npm", "start"]
