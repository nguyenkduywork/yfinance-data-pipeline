FROM amazonlinux:2 AS base

RUN yum install -y python3

ENV VIRTUAL_ENV=/opt/venv
RUN python3 -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN python3 -m pip install --upgrade pip && \
    python3 -m pip install -r requirements.txt && \
    python3 -m pip install venv-pack==0.2.0

RUN mkdir /output && venv-pack -o /output/virtualenv.tar.gz

FROM scratch AS export
COPY --from=base /output/virtualenv.tar.gz /