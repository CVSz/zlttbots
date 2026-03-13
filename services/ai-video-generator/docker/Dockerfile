FROM node:22

RUN apt update && apt install -y ffmpeg

WORKDIR /app

COPY . .

RUN npm install

CMD ["npm","start"]
