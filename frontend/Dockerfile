FROM node:22-alpine

WORKDIR /app
COPY . .

RUN npm ci
RUN npm run build

RUN npm install -g serve
CMD ["serve", "-s", "build", "-l", "3000"]
