# Docker-команда FROM вказує базовий образ контейнера
# Наш базовий образ - це Linux з попередньо встановленим python-3.10
FROM python:3.10

# Встановимо змінну середовища
ENV APP_HOME /tech_sage

# Встановимо робочу директорію всередині контейнера
WORKDIR $APP_HOME

# Скопіюємо інші файли в робочу директорію контейнера
COPY . .

# Встановимо залежності всередині контейнера
# RUN pip install -r requirements.txt
RUN pip install pipenv
RUN pipenv install --system
#RUN python3 pipenv lock --keep-outdated --requirements > requirements.txt
#RUN pip install -r requirements.txt
#RUN pipenv shell

# Позначимо порт, де працює застосунок всередині контейнера
EXPOSE 1234

# Запустимо наш застосунок всередині контейнера
#CMD pipenv shell
CMD ["python", "tech_sage/main.py"]