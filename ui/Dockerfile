FROM node:24-slim

RUN npm install -g corepack

WORKDIR /usr/src/app

COPY package.json pnpm-lock.yaml* ./

RUN corepack enable && \
    PNPM_VERSION=$(node -e "const p=require('./package.json');console.log(p.packageManager.split('@')[1])") && \
    corepack prepare pnpm@${PNPM_VERSION} --activate && \
    pnpm install

CMD ["pnpm", "run", "dev", "--host"]
