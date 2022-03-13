FROM python:3.7-slim

RUN mkdir /streamlit

COPY requirements.txt /streamlit

WORKDIR /streamlit

RUN pip install -r requirements.txt

COPY . /streamlit

CMD ["sh", "setup.sh"]
CMD ["streamlit", "run", "app.py"]