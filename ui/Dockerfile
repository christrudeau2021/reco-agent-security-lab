# VITE_* vars are inlined into the client bundle at build time (same
# constraint as AIM's own frontend image — see aim/README-local-build.md),
# so they're passed as build ARGs here rather than left to `environment:`
# in docker-compose.yml, which would silently do nothing.
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .

ARG VITE_NEO4J_URI
ARG VITE_NEO4J_USER
ARG VITE_NEO4J_PASSWORD
ARG VITE_AIM_API_URL
ARG VITE_AIM_VIEWER_EMAIL
ARG VITE_AIM_VIEWER_PASSWORD
ENV VITE_NEO4J_URI=$VITE_NEO4J_URI \
    VITE_NEO4J_USER=$VITE_NEO4J_USER \
    VITE_NEO4J_PASSWORD=$VITE_NEO4J_PASSWORD \
    VITE_AIM_API_URL=$VITE_AIM_API_URL \
    VITE_AIM_VIEWER_EMAIL=$VITE_AIM_VIEWER_EMAIL \
    VITE_AIM_VIEWER_PASSWORD=$VITE_AIM_VIEWER_PASSWORD

RUN npx tsc -b && npx vite build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
