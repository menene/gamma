ARG FRONTEND_MODE=production

FROM node:20-alpine AS base
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .

# --- Production build ---
FROM base AS build-production
RUN npm run build

FROM nginx:alpine AS production
COPY --from=build-production /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80

# --- Dev server ---
FROM base AS development
EXPOSE 80
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "80"]

# --- Final stage selected by FRONTEND_MODE ---
ARG FRONTEND_MODE
FROM ${FRONTEND_MODE}
