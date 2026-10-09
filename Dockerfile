FROM python:3.10.12-alpine

RUN apk add --no-cache openssl openvpn

#Build Args
ARG SERVICE_VERSION
ARG SERVICE_NAME

# Service env variable
ENV ARTIFACT_NAME=$SERVICE_NAME
ENV ARTIFACT_VERSION=$SERVICE_VERSION

RUN mkdir -p /opt/$ARTIFACT_NAME

WORKDIR /opt/$ARTIFACT_NAME

COPY requirements.txt .
RUN pip install -r requirements.txt  \
    && pip install gunicorn

COPY . .


ENTRYPOINT ["gunicorn", "--bind", "0.0.0.0:8080", "app:app"]