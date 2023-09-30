FROM python:3.10
# set work directory
WORKDIR /usr/src/app/
# copy project
COPY . /usr/src/app/
# install dependencies
RUN pip install --user -r requirements.txt
# download model
RUN wget -O models/saiga2 TODO_URL
# run app
CMD ["python", "main.py"]
