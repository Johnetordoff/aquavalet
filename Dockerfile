FROM python:3.7
RUN mkdir -p /code
WORKDIR /code

RUN pip install -U pip

COPY ./requirements.txt /code/

RUN pip install --no-cache-dir -r /code/requirements.txt

# Copy the rest of the code over
COPY ./ /code/

EXPOSE 8000

CMD ["invoke", "server"]
