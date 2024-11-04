from datetime import datetime, timedelta

from collections import UserDict
import pickle

class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    def __init__(self, name):
        if not name:
            raise ValueError("Name is a required field.")
        super().__init__(name)


class Phone(Field):
    # Можемо перевіряти формат телефону в цьому класі
    def __init__(self, phone):
        if len(phone) == 10 and phone.isdigit():
            super().__init__(phone)
        else:
            raise ValueError("Invalid phone format")
        
    def __str__(self):
        return self.value
    
class Birthday(Field):
    def __init__(self, value):
        try:
            birthday = datetime.strptime(value, "%d.%m.%Y").date() # Перевірка вхідних даних
            value = birthday.strftime("%d.%m.%Y") # Приведення до строки в потрібному форматі
            super().__init__(value)
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")
        

class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None


    def add_phone(self, phone: str):
        phone = Phone(phone)
        self.phones.append(phone)


    def edit_phone(self, phone, new_phone):
        new_phone = Phone(new_phone)
        for p in self.phones:
            if p.value == phone:
                index = self.phones.index(p) 
                self.phones[index] = new_phone
                return

        raise ValueError


    def find_phone(self, phone):
        phone = Phone(phone)
        return next((p for p in self.phones if p.value == phone.value), None)
   
    
    def remove_phone(self, phone):
        for p in self.phones:
            if p.value == phone:
               self.phones.remove(p)
        else:
            print('Phone doesn`t exist')

    def add_birthday(self, birthday: str):
        birthday = Birthday(birthday)
        self.birthday = birthday

    def get_upcoming_birthdays(self, days=7):
        if not self.birthday:
            return None
        
        birthday = datetime.strptime(self.birthday.value, "%d.%m.%Y").date()

        today = datetime.today().date()
        birthday_this_year = birthday.replace(year=today.year)

        if birthday_this_year < today:
            birthday_this_year = birthday_this_year.replace(year=today.year + 1)

        def adjust_for_weekend(birthday_date):
            if birthday_date.weekday() >= 5:  # 5 = Субота, 6 = Неділя
                days_ahead = (7 - birthday_date.weekday()) % 7  # Переносимо на понеділок
                return birthday_date + timedelta(days=days_ahead)
            return birthday_date

        days_until_birthday = (birthday_this_year - today).days
        if 0 <= days_until_birthday <= days:
            adjusted_date = adjust_for_weekend(birthday_this_year)
            return {"name": self.name.value, "birthday": adjusted_date}

        return None
                

    def __str__(self):
        if self.birthday:
            return f"Contact name: {self.name.value}, phones: {'; '.join(p.value for p in self.phones)}, birthday: {self.birthday.value}"
        else:
            return f"Contact name: {self.name.value}, phones: {'; '.join(p.value for p in self.phones)}"


class AddressBook(UserDict):
    
    def add_record(self, record):
        self.data[record.name.value] = record

    def find(self, name):
        record = self.data.get(name)
        if record:
            return record
        return None       
    
    def delete(self, name):
        if name in self.data:
           del self.data[name]
        else:
            print("Contact not found")

    def __str__(self):
        if not self.data:
            return "Address Book is empty."

        result = "Address Book:\n"
        for record in self.data.values():
            result += str(record) + "\n"
        return result.strip()  # Видаляємо зайві пробіли або нові рядки в кінці        



# Декоратор для всіх функцій

def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError:
            return "Incorrect value, try again"
        except IndexError:
            return "invalid input."
        except KeyError:
            return "This contact does not exist or phonebook is empty."
    return inner

# Парсинг командної строки
def parse_input(user_input):
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, *args

@input_error
def add_contact(args, book: AddressBook):
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message

@input_error
def change_contact(args, book: AddressBook):
    name, old_phone, new_phone = args
    record = book.find(name)
    if record:
        record.edit_phone(old_phone, new_phone)
        return "Contact changed."
    else:
        raise KeyError("Contact not found")
    
@input_error 
def phone_username(args, book: AddressBook):
    username = args[0].strip() 
    record = book.find(username)
    if record:
        phones = "; ".join(p.value for p in record.phones)
        return f"{username}'s phone(s): {phones}"
    else:
        raise KeyError("Contact not found")
    

@input_error
def print_all(book: AddressBook):
    return str(book)

@input_error
def add_birthday(args, book: AddressBook):
    name, birthday = args
    record = book.find(name)
    if record:
        record.add_birthday(birthday)
        return "Birthday added"
    else:
        raise KeyError("Contact not found")

@input_error
def show_birthday(args, book: AddressBook):
    name = args[0]
    record = book.find(name)
    if record and record.birthday:
        return f"{name} : {str(record.birthday.value)}"
    elif record:
        return f"{name} has no birthday set."
    
@input_error
def list_of_nearest_birtdays(book: AddressBook, days=7):
    upcoming_birthdays = []
    for record in book.data.values():
        birthday_info = record.get_upcoming_birthdays(days)
        if birthday_info:
            upcoming_birthdays.append(birthday_info)
    if upcoming_birthdays:
        return "\n".join(f"{entry['name']}'s congratulation date: {entry['birthday'].strftime('%d.%m.%Y')}" for entry in upcoming_birthdays)
    return f"No birthdays in the next {days} days."


def save_data(book: AddressBook, filename="addressbook.pkl"):
    with open(filename, "wb") as file:
        pickle.dump(book, file)


def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as file:
            book = pickle.load(file)
        return book
    except FileNotFoundError:
        return AddressBook()


def main():
    book = load_data()
    print("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ")
        command, *args = parse_input(user_input)

        if command in ["close", "exit"]:
            save_data(book)
            print("Good bye!")
            break
        elif command == "hello":
            print("How can I help you?")
        elif command == "add":
            print(add_contact(args, book))
        elif command == "change":
            print(change_contact(args, book))
        elif command == "phone":
            print(phone_username(args, book))
        elif command == "all":
            print(print_all(book))
        elif command == "add-birthday":
            print(add_birthday(args, book))
        elif command == "show-birthday":
            print(show_birthday(args, book))
        elif command == "birthdays":
            print(list_of_nearest_birtdays(book))
        else:
            print("Invalid command.")


if __name__ == "__main__":
    main()


