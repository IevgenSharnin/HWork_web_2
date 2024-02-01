# tsamsing change
from collections import UserDict
from datetime import datetime
import pickle
from pathlib import Path
from typing import List
from abc import ABC, abstractmethod
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.completion import NestedCompleter
from prompt_toolkit.validation import Validator, ValidationError
from rich.console import Console
from rich.table import Table
import re
from sort_files import run

console = Console()
COMMANDS = {'add_name': ['add_name', 'Додавання нового контакту у довідник'],
            'add_phone': ['add_phone Name', 'Додавання телефонного номеру до контакту <Name>.\nКожен контакт може мати кілька номерів'],
            'add_birthday': ['add_birthday Name', 'Додавання для контакта <Name> дня народження у форматі ДД.ММ.РРРР.\nКожен контакт має тільки один день народження.\nТакож застосовується для зміни дня народження'],
            'add_email': ['add_email Name', 'Додавання адреси електроної пошти для контакта <Name>.\nКожен контакт має тільки один e-mail.\nТакож застосовується для зміни e-mail'],
            'add_address': ['add_address Name', 'Додавання адреси для контакта <Name>.\nКожен контакт має тільки одну адресу.\nТакож застосовується для зміни адреси'],
            'find_record_by_text': ['find_record_by_text text', "Пошук рядку <text> у всіх полях телефонного довідника"],
            'list_book': ['list_book', 'Вивід на екран телефонного довідника'],
            'delete_name': ['delete_name', 'Видалення контакту з довідника'],
            'delete_phone': ['delete_phone Name', 'Видалення номеру телефону у контакту <Name>'],
            'delete_email': ['delete_email Name', 'Видалення електроної адреси у контакту <Name>'],
            'delete_address': ['delete_address Name', 'Видалення адреси у контакту <Name>'],

            'add_note': ['add_note Name', 'Додавання нотатки для контакту <Name>'],
            'find_note_by_name': ['find_note_by_name Name', 'Пошук у нотатках для імені <Name>'],
            'find_notes_by_text': ['find_notes_by_text text', "Пошук у всіх нотатках за текстом <text>"],
            'list_note': ['list_note', 'Вивід на екран усіх нотаток'],
            'edit_note': ['edit_note Name', 'Коригування нотаток для контакту <Name>'],
            'delete_all_notes': ['delete_all_notes Name', 'Видалення усіх нотаток для контакту <Name>'],

            'days_to_birthday': ['days_to_birthday Name', 'Розрахунок залишку днів до дня народження контакта <Name>'],
            'when': ['when Number', 'Вивід на екран списку контактів,\nу яких день народження впродовж <Number> днів від сьогодні'],
            'sort_files': ['sort_files Path', 'Сортує по папках файли у папці <Path> на вашому диску \nв залежності від типу файлу'],

            'help': ['help', 'Виклик довідника команд, що вміє цей бот'],
            'load': ['load', 'Завантаження довідника з файла на диску. \nПерезапише зміни, що були внесені та не збережені у файл.\nТакож відбувається автоматично при запуску програми'],
            'save': ['save', 'Зберігання змін у довіднику у файл на диску.\nТакож відбувається автоматично при закінченні роботи з програмою'],
            'exit': ['exit', 'Вихід із програми із автоматичним записом змін у файл'],
}
######################################################################
# Класи для кожного поля запису адресної книжки або нотатки
class Field:
    def __init__(self, value):
        self._value = None
        self.value = value

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        self._value = new_value

    def __str__(self):
        return str(self._value)


class Name(Field):
    def __init__(self, name):
        super().__init__(name)


class Phone(Field):
    def __init__(self, name):
        super().__init__(name)

    @Field.value.setter
    def value(self, new_value):
        if (not new_value.isdigit()) or (len (new_value) != 10):
            raise ValueError("Номер телефону повинен складатися з 10 цифр.")
        self._value = new_value


class Address(Field):
    def __init__(self, value):
        super().__init__(value)


class Email(Field):
    def __init__(self, name):
        super().__init__(name)

    @Field.value.setter
    def value(self, new_value):
        result = re.findall(r"[a-zA-Z0-9_.]+@\w+\.\w{2,3}", new_value)
        try:
            self._value = result[0]
        except IndexError:
            raise IndexError("E-mail must be 'name@domain'")


class Birthday(Field):
    def __init__(self, name):
        super().__init__(name)

    @Field.value.setter
    def value(self, new_value):
        try:
            datetime.strptime(new_value, "%d.%m.%Y")
        except ValueError:
            raise ValueError("Невірний формат дати!!! Спробуйте ДД.ММ.РРРР")
        self._value = new_value


class Note(Field):
    def __init__(self, text, date, tags=None):
        super().__init__(text)
        self.tags = tags if tags is not None else []
        self.date = date

#    def add_tag(self, tag):
#        self.tags.append(tag)

#    def remove_tag(self, tag):
#        self.tags.remove(tag)

############################################################################################
# Клас запису адресної книжки із функціями роботи з окремими елементами
class Record:
    def __init__(self, name, email=None, address=None, birthday=None):
        self.name = Name(name)
        self.phones = []
        self.email = Email(email) if email else None
        self.address = Address(address) if address else None
        self.birthday = Birthday(birthday) if birthday else None

    def add_phone(self, phone):
        phone_field = Phone(phone)
        if list(filter(lambda p: p.value == phone_field.value, self.phones)) == []:
            self.phones.append(phone_field)

    def add_email(self, email):
        email_field = Email(email)
        self.email = email_field

    def delete_email(self):
        self.email = None

    def add_address(self, address):
        address_field = Address(address)
        self.address = address_field

    def delete_address(self):
        self.address = None

    def add_birthday(self, birthday):
        new_birthday = Birthday(birthday)
        self.birthday = new_birthday

    def remove_phone(self, phone):
        if (list(filter(lambda p: p.value == phone, self.phones)) == []):
            print (f'Телефон {phone} не існує.')
        else:
            self.phones = list(filter(lambda p: p.value != phone, self.phones))
            print(f"Телефон {phone} видалений.")

    def __str__(self):
        return f"Record(name={self.name.value}, birthday={self.birthday}, phones={[phone.value for phone in self.phones]})"

    def days_to_birthday(self):
        if not self.birthday:
            return -1

        today = datetime.now().date()
        next_birthday = datetime.strptime(self.birthday.value, "%Y-%m-%d").date().replace(year=today.year)
        if today > next_birthday:
            next_birthday = next_birthday.replace(year=today.year + 1)

        days_until_birthday = (next_birthday - today).days
        return days_until_birthday

############################################################################################
# Клас адресної книжки із функціями роботи з його елементами (повним записом)
class AddressBook(UserDict):
    record_id = None

    def __init__(self, file="adress_book_1.pkl"):
        self.file = Path(file)
        self.record_id = 0
        self.record = {}
        super().__init__()

    def add_record(self, record):
        self.data[record.name.value] = record

#    def find(self, term):
#        if term in self.data:
#            return self.data[term]
#        else:
#            return None

    def delete_record(self, name):
        if name.name.value in self.data:
            del self.data[name.name.value]

# Для посторінкового друку - не використовується наразі
#    def iterator(self, item_number):
#        counter = 0
#        result = []
#        for item, record in self.data.items():
#            result.append(record)
#            counter += 1
#            if counter >= item_number:
#                yield result
#                counter = 0
#                result = []

    def dump(self):
        with open(self.file, "wb") as file:
            pickle.dump((self.record_id, dict(self.data)), file)

    def load(self):
        if not self.file.exists():
            return
        with open(self.file, "rb") as file:
            self.record_id, data = pickle.load(file)
            self.data.update(data)

    def find_by_term(self, term: str) -> List[Record]:
        matching_records = []

        for record in self.data.values():
            for phone in record.phones:
                if term in phone.value:
                    matching_records.append(record)
            if term in str (record.email):
                matching_records.append(record)
            if term in str (record.address):
                matching_records.append(record)

        matching_records.extend(record for record in self.data.values() if term.lower() in record.name.value.lower())
        return matching_records


############################################################################################
# Клас нотаток із функціями роботи з його елементами (повним записом)
class NoteRecord(Record):
    def __init__(self, name, birthday=None):
        super().__init__(name, birthday=None)
        self.notes = []

    def add_note(self, text, tags=None):
        now = datetime.now()
        date = now.strftime("%Y-%m-%d %H:%M:%S")
        note = Note(text, date, tags)
        self.notes.append(note)

    def remove_note(self, text):
        if not text:
            raise ValueError("Введіть нотаток!")
        self.notes = [note for note in self.notes if note.value != text]

    def edit_note(self, new_text, new_tags=None):
        now = datetime.now()
        date = now.strftime("%Y-%m-%d %H:%M:%S")
        for idx, a in enumerate(self.notes):
            if new_text:
                note = new_text
                tags = new_tags
                self.notes[idx] = Note(note, date, tags) 

    def find_notes_by_tag(self, tag):
        return [note for note in self.notes if tag in note.tags]
    
    def find_notes_by_term(self, term):
        return [note for note in self.notes if term.lower() in note.value.lower() or any(term.lower() in tag.lower() for tag in note.tags)]

    def __str__(self):
        notes_str = " | ".join([f"{note.value} [{' ,'.join(note.tags)}]" for note in self.notes])
        return f"NoteRecord(name={self.name.value}, notes={notes_str})"

######################################################################
# Класи для принтування інтерфейсних таблиць
class PrintTable (ABC):
    @abstractmethod
    def __init__(self, key = None) -> None:
#        self.table_for_print = table_rows_for_add
        self.console = Console ()
        self.key = key
        self.table = Table()

    def add_row (self, *args):
        self.table.add_row (*args)
        self.table.add_section()
# Подумати про застосування посторінкового друку для хелпа    
    def printer (self):
        self.console.print (self.table)


class PrintTableAddressBook (PrintTable):
    def __init__(self, key = 'contacts') -> None:
        super().__init__(key = 'contacts')
        self.table = Table(show_header=True, header_style="bold magenta", border_style='bold violet')
        self.table.add_column('Name')
        self.table.add_column("Phone")
        self.table.add_column("Address")
        self.table.add_column("Email")
        self.table.add_column("Birthday")
    

class PrintTableNote (PrintTable):
    def __init__(self, key = 'notes') -> None:
        super().__init__(key = 'notes')
        self.table = Table(show_header=True, header_style="bold cyan", border_style='bold yellow')
        self.table.add_column('Author')
        self.table.add_column("Note")
        self.table.add_column("Tag")
        self.table.add_column("Date", style = 'dim', width = 12)
    

class PrintTableWhenBirthday (PrintTable):
    def __init__(self, key = 'bdays') -> None:
        super().__init__(key = 'bdays')
        self.table = Table(show_header=True, header_style="bold magenta", border_style='bold violet')
        self.table.add_column('Name')
        self.table.add_column("Phone")
        self.table.add_column("Email")
        self.table.add_column("Birthday")
        self.table.add_column("Days to b-day")
    

class PrintTableHelp (PrintTable):
    def __init__(self, key = 'help') -> None:
        super().__init__(key = 'help')
        self.table = Table(show_header=True, header_style="bold blue", border_style='bold green')
        self.table.add_column('Синтаксис команди')
        self.table.add_column("Опис")
    
###############################################################################
# Клас-тримач функцій-дій бота, що активуються командами після CommandValidator() 
class Controller():
    def __init__(self):
        self.book = AddressBook()

#    def do_exit(self):
#        self.book.dump()
#        print("Адресна книга збережена! Вихід...")
#        return True

    def do_save(self):
        self.book.dump()
        print("Адресна книга збережена")

    def do_load(self):
        self.book.load()
        print("Адресна книга відновлена")

    def do_help(self):
        table_printer = PrintTableHelp ()
        for commands in COMMANDS.values():
            table_printer.add_row(commands[0], commands[1])
        table_printer.printer()
        print('')

    def line_to_name (self, line):
        line = line.strip().split(' ')
        name = ''
        for each in line:
            name = f'{name}{each[0].capitalize()}{each[1:]} '
        name = name.strip()
        record = self.book.get(name)
        if record:
            return record
        else: return name

    def do_add_name(self):
        while True:
            line = input("Введіть: <Ім'я>: ")
            if not line:
                print("Будь ласка введіть: <Ім'я>: ")
                continue
            record = self.line_to_name(line)

            if type(record) == NoteRecord:
                print(f"Контакт з ім'ям '{record.name.value}' вже існує.")
                return
            try:
                record = NoteRecord(record)
                self.book.add_record(record)
                print(f"Контакт з ім'ям '{record.name.value}' успішно створено.")
                break
            except ValueError as e:
                print(f"Помилка при створенні контакту: {e}")

    def do_delete_name(self):
        while True:
            line = input("Введіть: <Ім'я>: ")
            if not line:
                print("Будь ласка введіть: <Ім'я>: ")
                continue
            record = self.line_to_name(line)
            if not record:
                print(f"Контакт з ім'ям '{line}' не знайдено.")
                return
            try:
                self.book.delete_record(record)
                print(f"Контакт з ім'ям '{line}' успішно видалено.")
                break
            except ValueError as e:
                print(f"Помилка при видаленні контакту: {e}")

    def do_add_phone(self, line):
        record = self.line_to_name(line)

        if not record:
            print(f"Контакт з ім'ям '{line}' не знайдено.")
            return
        phone = input ('Введіть номер телефону з 10 цифр:  ')

        try:
            record.add_phone(phone)
            print(f"Телефон '{phone}' додано до контакта '{record.name.value}'.")
        except ValueError as e:
            print(f"Помилка при додаванні телефону: {e}")

    def do_delete_phone(self, line):
        record = self.line_to_name(line)

        if not record:
            print(f"Контакт з ім'ям '{line}' не знайдено.")
            return
        phone = input ('Введіть номер телефону з 10 цифр:  ')

        try:
            record.remove_phone(phone)
        except ValueError as e:
            print(f"Помилка при видаленні телефону: {e}")

    def do_add_birthday(self, line):
        record = self.line_to_name(line)

        if not record:
            print(f"Контакт з ім'ям '{line}' не знайдено.")
            return
        birthday_str = input ('Введіть дату дня народження у форматі ДД.ММ.РРРР:  ')
        try:
            record.add_birthday(birthday_str)
            print(f"День народження {birthday_str} додано для контакта '{record.name.value}'.")
        except ValueError as e:
            print(f"Помилка при додаванні дня народження: {e}")

    def do_add_email(self, line):
        record = self.line_to_name(line)
        if not record:
            print(f"Контакт з ім'ям '{line}' не знайдено.")
            return
        email = input('Введіть email:  ')
        try:
            record.add_email(email)
            print(f"Email '{email}' додано до контакта '{record.name.value}'.")
        except IndexError as e:
            print(f"Помилка при додаванні email: {e}")

    def do_delete_email(self, line):
        record = self.line_to_name(line)
        if not record:
            print(f"Контакт з ім'ям '{line}' не знайдено.")
            return
        try:
            record.delete_email()
            print(f"E-mail контакта '{line}' видалено.")
        except IndexError as e:
            print(f"Помилка при видаленні email: {e}")

    def do_add_address(self, line):
        record = self.line_to_name(line)
        if not record:
            print(f"Контакт з ім'ям '{line}' не знайдено.")
            return
        address = input('Введіть адресу: ')
        try:
            record.add_address(address)
            print(f"Адреса '{address}' додана до контакта '{record.name.value}'.")
        except ValueError as e:
            print(f"Помилка при додаванні адреси: {e}")

    def do_delete_address(self, line):
        record = self.line_to_name(line)
        if not record:
            print(f"Контакт з ім'ям '{line}' не знайдено.")
            return
        try:
            record.delete_address()
            print(f"Адреса видалена для контакта '{record.name.value}'.")
        except ValueError as e:
            print(f"Помилка при видаленні адреси: {e}")

    def do_list_book(self):
        if not self.book.data:
            print("Адресна книга порожня.")
        else:
            table_printer = PrintTableAddressBook ()
            for record in self.book.data.values():
                phones = '; '.join(str(phone) for phone in record.phones)
                birthday_info = record.birthday.value if record.birthday else ""
                address_info = record.address.value if record.address else ""
                email_info = record.email.value if record.email else ""
                table_printer.add_row(record.name.value, phones, address_info, email_info, birthday_info)
            table_printer.printer()

    def do_find_record_by_text(self, line):
        matching_records = self.book.find_by_term(line)
        table_printer = PrintTableAddressBook ()
        if matching_records:
            for record in matching_records:
                phones = '; '.join(str(phone) for phone in record.phones)
                birthday_info = record.birthday.value if record.birthday else ""
                address_info = record.address.value if record.address else ""
                email_info = record.email.value if record.email else ""
                table_printer.add_row(record.name.value, phones, address_info, email_info, birthday_info)
            table_printer.printer()
        else:
            print("Даних із таким текстом не існує!!!.")
       
    def do_days_to_birthday(self, line, when=9999): # >>>birthday John (до дня народження контакту John, залишилось 354 днів)
        table_printer = PrintTableWhenBirthday ()
        record = self.line_to_name(line)
        if record:
            days_until_birthday = record.days_to_birthday()
            phones = '; '.join(str(phone) for phone in record.phones)
            birthday_info = record.birthday.value if record.birthday else ""
            email_info = record.email.value if record.email else ""
            if 0 < days_until_birthday <= when:
                table_printer.add_row(record.name.value, phones, email_info, birthday_info, str(days_until_birthday))
            elif days_until_birthday == 0:
                table_printer.add_row(record.name.value, phones, email_info, birthday_info, 'TODAY!!!')
            elif (days_until_birthday > when or days_until_birthday == -1) and (when != 9999):
                return
            else:
                print(f"День народження {record.name.value} не додано в книгу контактів\n")
            if when == 9999:
                table_printer.printer ()
            else:
                return (days_until_birthday)
        else:
            print(f"Контакт '{record}' відсутній у адресній книзі")
            
    def do_when (self, days):
        table_printer = PrintTableWhenBirthday ()
        if not days:
            print ("Введіть 'when' та кількість днів, на які хочете побачити прогноз")
            return
        if not days.isdigit():
            print ("Введіть кількість днів додатнім числовим значенням")
            return
        for record in self.book.values():
            phones = '; '.join(str(phone) for phone in record.phones)
            birthday_info = record.birthday.value if record.birthday else ""
            email_info = record.email.value if record.email else ""
            when = self.do_days_to_birthday (record.name.value, int(days))
            if when != None and when != 0 and when != 1:
                table_printer.add_row(record.name.value, phones, email_info, birthday_info, str(when))
            elif when == 0:
                table_printer.add_row(record.name.value, phones, email_info, birthday_info, 'TODAY!!!')
            elif when == 1:
                table_printer.add_row(record.name.value, phones, email_info, birthday_info, 'TOMORROW!!!')
            
        if table_printer.table.rows:
            table_printer.printer()

################ функції для команд роботи з нотатками
    def do_add_note(self, line):
        record = self.line_to_name(line)
        if not record:
            print(f"Контакт з ім'ям '{line}' не знайдено.")
            return
        if not isinstance(record, NoteRecord):
            print(f"Для контакта '{record.name.value}' не підтримуються нотатки.")
            return
        note_text = input('Введіть нотатку: ')
        tags = input('Введіть теги: ')
        record.add_note(note_text, tags)
        print(f"Нотатка додана для контакта {record.name.value}.")

    def do_find_notes_by_text(self, term):
        term = term.strip().lower()
        table_printer = PrintTableNote ()
        
        found_notes = False
        for name, record in self.book.data.items():
            if isinstance(record, NoteRecord):
                matching_notes = record.find_notes_by_term(term)
                for note in matching_notes:
                    table_printer.add_row(name, note.value, note.tags, note.date)
                    found_notes = True
        
        if found_notes:
            table_printer.printer()
        else:
            print("Даних із таким текстом не існує!!!.")

    def do_list_note(self):
        if not self.book.data:
            print("Адресна книга порожня.")
        else:
            table_printer = PrintTableNote ()
            for name, record in self.book.data.items():
                if isinstance(record, NoteRecord) and record.notes:
                    for h in record.notes:
                        table_printer.add_row(name, h.value, h.tags, h.date)
            table_printer.printer()

    def do_find_note_by_name(self, line):
        record = self.line_to_name(line)
        if not record:
            print(f"Контакт з ім'ям '{line}' не знайдено.")
            return
        table_printer = PrintTableNote ()
        if isinstance(record, NoteRecord) and record.notes:
            for note in record.notes:
                table_printer.add_row(record.name.value, note.value, note.tags, note.date)
            table_printer.printer()
        else:
            print(f"Для контакта '{line}' не знайдено нотаток або вони не підтримуються.")

    def do_delete_all_notes(self, line):
        record = self.line_to_name(line)
        if record:
            if isinstance(record, NoteRecord):
                record.notes.clear()
                print(f"Усі нотатки для '{record.name.value}' було видалено.")
            else:
                print("Для цього контакта нотатки не підтримуються.")
        else:
            print("Контакт не знайдено.")

    def do_edit_note(self, line):
        record = self.line_to_name(line)
        if not record:
            print(f"Контакт з ім'ям '{line}' не знайдено.")
            return
        new_text= input("Введіть нову нотатку: ")
        new_tags = input("Введіть новий тег: ")
        record.edit_note(new_text, new_tags)
        print("Нотатка успішно відредагована.")

    def do_sort_files(self, line):
        if not line:
            print("Введіть шлях до папки, яку треба сортувати")
            return
        try:
            run(line)
        except FileNotFoundError:
            print('Така папка не існує на диску. Можливо треба ввести повний шлях\n')


class CommandValidator(Validator):
    def validate(self, document):
        text = document.text
        if text.startswith("add_phone"):
            x = text.strip().split(" ")
            if len(x) < 2:
                raise ValidationError(message="Введіть: <Ім'я>", cursor_position=len(text))

        if text.startswith("delete_phone"):
            x = text.strip().split(" ")
            if len(x) < 2:
                raise ValidationError(message="Введіть: <Ім'я>", cursor_position=len(text))

        if text.startswith("add_birthday"):
            x = text.strip().split(" ")
            if len(x) < 2:
                raise ValidationError(message="Введіть: <Ім'я>", cursor_position=len(text))

        if text.startswith("find_record_by_text"):
            x = text.split(" ")
            if len(x) == 1:
                raise ValidationError(message="Введіть: текст для пошуку", cursor_position=len(text))

        if text.startswith("days_to_birthday"):
            x = text.strip().split(" ")
            if len(x) < 2:
                raise ValidationError(message="Введіть: <Ім'я> для пошуку", cursor_position=len(text))

        if text.startswith("when"):
            x = text.strip().split(" ")
            if len(x) < 2:
                raise ValidationError(message="Введіть: кількість днів для пошуку", cursor_position=len(text))

        if text.startswith("sort_files"):
            x = text.strip().split(" ")
            if len(x) != 2:
                raise ValidationError(message="Введіть: шлях до папки, яку треба сортувати", cursor_position=len(text))

        if text.startswith("add_note"):
            x = text.strip().split(" ")
            if len(x) < 2:
                raise ValidationError(message="Введіть: <Ім'я>", cursor_position=len(text))

        if text.startswith("find_note_by_name"):
            x = text.strip().split(" ")
            if len(x) < 2:
                raise ValidationError(message="Введіть: <Ім'я> для пошуку", cursor_position=len(text))
            
        if text.startswith("find_notes_by_text"):
            x = text.split(" ")
            if len(x) != 2:
                raise ValidationError(message="Введіть: текст для пошуку", cursor_position=len(text))
            
        if text.startswith("edit_note"):
            x = text.strip().split(" ")
            if len(x) < 2:
                raise ValidationError(message="Введіть: <Ім'я>", cursor_position = len(text))
            
        if text.startswith("delete_all_notes"):
            x = text.strip().split(" ")
            if len(x) < 2:
                raise ValidationError(message="Введіть: <Ім'я>", cursor_position=len(text))

        if text.startswith("add_email"):
            x = text.strip().split(" ")
            if len(x) < 2:
                raise ValidationError(message="Введіть: <Ім'я>", cursor_position=len(text))

        if text.startswith("delete_email"):
            x = text.strip().split(" ")
            if len(x) < 2:
                raise ValidationError(message="Введіть: <Ім'я>", cursor_position=len(text))

        if text.startswith("add_address"):
            x = text.strip().split(" ")
            if len(x) < 2:
                raise ValidationError(message="Введіть: <Ім'я>", cursor_position=len(text))

        if text.startswith("delete_address"):
            x = text.strip().split(" ")
            if len(x) < 2:
                raise ValidationError(message="Введіть: <Ім'я>", cursor_position=len(text))

controller = Controller()

def handle_command(command):
    if command.lower().startswith("add_name"):
        return controller.do_add_name()
    elif command.lower().startswith("delete_name"):
        return controller.do_delete_name()
    elif command.lower().startswith("help"):
        return controller.do_help()
    elif command.lower().startswith("add_phone"):
        first_space_index = command.find(' ')
        _, name = [command[:first_space_index], command[first_space_index+1:]]
        return controller.do_add_phone(name)
    elif command.lower().startswith("delete_phone"):
        first_space_index = command.find(' ')
        _, name = [command[:first_space_index], command[first_space_index+1:]]
        return controller.do_delete_phone(name)
    elif command.lower().startswith("add_email"):
        first_space_index = command.find(' ')
        _, name = [command[:first_space_index], command[first_space_index+1:]]
        return controller.do_add_email(name)
    elif command.lower().startswith("delete_email"):
        first_space_index = command.find(' ')
        _, name = [command[:first_space_index], command[first_space_index+1:]]
        return controller.do_delete_email(name)
    elif command.lower().startswith("add_address"):
        first_space_index = command.find(' ')
        _, name = [command[:first_space_index], command[first_space_index+1:]]
        return controller.do_add_address(name)
    elif command.lower().startswith("delete_address"):
        first_space_index = command.find(' ')
        _, name = [command[:first_space_index], command[first_space_index+1:]]
        return controller.do_delete_address(name)
    elif command.lower().startswith("add_birthday"):
        first_space_index = command.find(' ')
        _, name = [command[:first_space_index], command[first_space_index+1:]]
        return controller.do_add_birthday(name)
    elif command.lower().startswith("list_book"):
        return controller.do_list_book()
    elif command.lower().startswith("load"):
        return controller.do_load()
    elif command.lower().startswith("list_note"):
        return controller.do_list_note()
    elif command.lower().startswith("find_record_by_text"):
        _, line = command.split(" ")
        return controller.do_find_record_by_text(line)
    elif command.lower().startswith("days_to_birthday"):
        first_space_index = command.find(' ')
        _, name = [command[:first_space_index], command[first_space_index+1:]]
        return controller.do_days_to_birthday(name)
    elif command.lower().startswith("when"):
        _, name = command.split(" ")
        return controller.do_when(name)
    elif command.lower().startswith("sort_files"):
        _, name = command.split(" ")
        return controller.do_sort_files(name)
    elif command.lower().startswith("add_note"):
        first_space_index = command.find(' ')
        _, name = [command[:first_space_index], command[first_space_index+1:]]
        return controller.do_add_note(name)
    
    elif command.lower().startswith("find_note_by_name"):
        first_space_index = command.find(' ')
        _, name = [command[:first_space_index], command[first_space_index+1:]]
        return controller.do_find_note_by_name(name)
    
    elif command.lower().startswith("find_notes_by_text"):
        _, text = command.split(" ")
        return controller.do_find_notes_by_text (text)
    
    elif command.lower().startswith("edit_note"):
        first_space_index = command.find(' ')
        _, name = [command[:first_space_index], command[first_space_index+1:]]
        return controller.do_edit_note(name)
    elif command.lower().startswith("delete_all_notes"):
        first_space_index = command.find(' ')
        _, name = [command[:first_space_index], command[first_space_index+1:]]
        return controller.do_delete_all_notes(name)
    elif command.lower() == "exit":
        controller.do_exit()
        return 'Good bye!'
    elif command.lower() == "save":
        return controller.do_save()


def main():
    controller.do_load()
    print("Ласкаво просимо до Адресної Книги")
    controller.do_when('0')

    while True:
        commands_for_interp = {}
        for command in COMMANDS.keys():
            commands_for_interp[command] = None
        command_interpreter = NestedCompleter.from_nested_dict(commands_for_interp)

        user_input = prompt('Введіть команду: ', completer=command_interpreter, validator=CommandValidator(),
                            validate_while_typing=False)
        if user_input.lower() == "exit":
            controller.do_save()
            print("Good bye!")
            break
        response = handle_command(user_input)

if __name__ == "__main__":
    main()
