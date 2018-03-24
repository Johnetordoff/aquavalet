FROM python:3.6-slim

RUN mkdir -p /code
WORKDIR /code

RUN pip install -U pip

COPY ./requirements.txt /code/

RUN pip install --no-cache-dir -r /code/requirements.txt

# Copy the rest of the code over
COPY ./ /code/

RUN python setup.py develop

EXPOSE 7777

CMD ["invoke", "server"]
