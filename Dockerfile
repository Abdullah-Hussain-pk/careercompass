FROM node:22-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build
FROM node:22-alpine
ENV NODE_ENV=production APP_MODE=supabase COOKIE_SECURE=true HOST=0.0.0.0 PORT=4001
WORKDIR /app
COPY package*.json ./
RUN npm ci --omit=dev && npm cache clean --force
COPY --from=build /app/dist ./dist
COPY --from=build /app/supabase ./supabase
USER node
EXPOSE 4001
CMD ["node","dist/api/apps/api/src/main.js"]
