FROM node:22-alpine

WORKDIR /app

COPY package*.json ./
COPY apps/web/package*.json apps/web/
COPY packages/schemas/package*.json packages/schemas/
RUN npm install

COPY apps/web apps/web
COPY packages/schemas packages/schemas

WORKDIR /app/apps/web
RUN npm run build

EXPOSE 3000

CMD ["npm", "run", "start", "--", "--port", "3000"]
