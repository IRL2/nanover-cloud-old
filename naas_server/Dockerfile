FROM python:3.8.5-slim-buster

RUN apt update
RUN apt install -y curl gnupg
RUN apt remove -y cmdtest yarn
RUN curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add -
RUN echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list
RUN apt update
RUN apt install -y yarn
RUN pip install --upgrade pip

# /app/ui
COPY ./app/ui/src /app/ui/src/
COPY ./app/ui/public/ /app/ui/public/
COPY ./app/ui/package.json /app/ui/package.json
COPY ./app/ui/yarn.lock /app/ui/yarn.lock
WORKDIR /app/ui/
RUN yarn
RUN yarn build

# /app/api
COPY ./app/api/*.py /app/api/
COPY ./app/api/requirements.txt /app/api/requirements.txt
WORKDIR /app
RUN pip install -r api/requirements.txt

CMD exec gunicorn --workers 1 --bind 0.0.0.0:8000 --log-level=info "api:create_app()"