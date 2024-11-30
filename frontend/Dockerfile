FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

ENV PATH /app/node_modules/.bin:$PATH

EXPOSE 3000
CMD ["npm", "start"] 