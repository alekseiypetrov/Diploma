FROM python:3.9
WORKDIR /web_app

COPY tools /tmp/tools
RUN pip install /tmp/tools

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

CMD ["python", "parser/parser.py"]