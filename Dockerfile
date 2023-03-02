FROM python:3.9

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PATH="/py/bin:/py/lib:$PATH"

WORKDIR /app

COPY . /app

EXPOSE 8000

RUN pip install --upgrade pip
RUN pip install -r /app/requirements.txt
