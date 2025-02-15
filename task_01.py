"""
nagranie 12
Zadania praktyczne do nagrania

1. Twoim zadaniem jest zaimplementowanie systemu zarządzania książkami w bibliotece cyfrowej.
System będzie korzystał z mechanizmów do pobierania, walidacji, przetwarzania oraz prezentacji danych.

Szczegóły implementacji
a. Data Preprocessing

Pobieranie danych:
Implementacja klasy JsonFileService, która będzie odpowiadać za odczyt i zapis danych z/do pliku JSON.

Walidacja danych:
Implementacja klasy Validator, która będzie walidować dane książki (np. sprawdzenie, czy wszystkie
wymagane pola są wypełnione i mają poprawny format).

Konwersja danych:
Implementacja klasy BookConverter, która będzie konwertować dane z formatu JSON do obiektów klasy Book.

b. Przetwarzanie danych

Implementacja klasy LibraryService, która będzie realizować przetwarzanie danych książek, np. filtrowanie 
książek według kategorii, itp.

c. Prezentacja
Implementacja klasy ReportService, która będzie generować raporty w różnych formatach (np. wyświetlanie
w konsoli, zapis do pliku tekstowego).
"""
from collections import defaultdict
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Self, Any, override, Callable
from enum import Enum
import json
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='[%(levelname)-8s] - %(asctime)s - %(message)s'
)

class BookCategory(Enum):
    UNKNOWN = "Unknown"
    FICTION = "Fiction"
    NON_FICTION = "Non-fiction"
    SCIENCE = "Science"
    FANTASY = "Fantasy"
    SELF_HELP = "Self-help"


@dataclass
class Book:
    title: str
    desc: str
    author: str
    year: int
    pages: int
    price: Decimal = field(default_factory=lambda:Decimal(0.0))
    category: BookCategory = field(default_factory=lambda: BookCategory.UNKNOWN)

    def has_category(self, category: BookCategory) -> bool:
        return self.category == category

    def is_betweeen(self, from_year: int, to_year: int) -> bool:
        return from_year <= self.year <= to_year

    def __str__(self) -> str:
        return f'Book(Title: {self.title}, author: {self.author}, year: {self.year}, '\
            f'pages {self.pages}, price: {self.price}, category: {self.category.name}'

    def __repr__(self) -> str:
        return str(self)
                
        

class FileService(ABC):

    @abstractmethod
    def read(self, file_name:str) -> list[dict[str, str | int | float | Decimal]]:
        pass

    @abstractmethod
    def write(self, file_name: str, data: list[dict[str, str | int | float | Decimal]]) -> None:
        pass


class JsonFileService(FileService):

    @override
    def read(self, file_name: str) -> list[dict[str, str | int | float | Decimal]]:
        with open(file_name, 'r', encoding='UTF-8') as json_file:
            return json.load(json_file)

    @override
    def write(self, file_name: str, data: list[dict[str, str | int | float| Decimal]]) -> None:
        with open(file_name, 'w', encoding='UTF8') as json_file:
            json.dump(data, json_file, indent=4, ensure_ascii=False)


# Validation
class Validator(ABC):
    
    @abstractmethod
    def validate(self, data: dict[str, str | int | float | Decimal]) -> bool:
        pass

    @staticmethod
    def is_possitive_number(n: int | float | Decimal) -> bool:
        return float(n) > 0.0

    @staticmethod
    def is_between(n: int, left: int, right: int) -> bool:
        return left <= n <= right

class BookValidator(Validator):
    
    @override
    def validate(self, data: dict[str, str | int | float | Decimal]) -> bool:
        validate_fields = ['title', 'desc', 'author', 'year', 'pages', 'price', 'category']

        for field in validate_fields:
            if field not in data or not data[field]:
                logging.error(f'Missing field {field} in {data} or no data')
                return False
                
            if not isinstance(data['year'], int):
                logging.error(f'Year is not an integer in entry: {data}')
                return False
            
            if not Validator.is_between(data['year'], 1900, 2025):
                logging.error(f'Year should be between 1900 and 2025.')
                return False

            if not isinstance(data['pages'], int):
                logging.error(f'Pages is not an integer in entry: {data}')
                return False
            
            if not Validator.is_possitive_number(data['pages']):
                logging.error(f'Pages should be greater than 0.')
                return False

            if not isinstance(data['price'], (Decimal, float, int)):
                logging.error(f'Price is not Decimal in entry: {data}')
                return False

            if not Validator.is_possitive_number(data['price']):
                logging.error(f'Price should be greater than 0.')
                return False

            if data['category'] not in [c.value for c in BookCategory]:
                logging.error(f'Invalid category {data['category']} in entry: {data}')
                return False
        return True


class Converter(ABC):
    
    @abstractmethod
    def from_json(self, data: dict[str, str | int | float | Decimal]) -> Any:
        pass

    @abstractmethod
    def to_json(self, data: Any) -> dict[str, str | int | float | Decimal]:
        pass

class BookConverter(Converter):

    @override
    def from_json(self, data: dict[str, str | int | float | Decimal]) -> Book | None:
        
        try:
            category = BookCategory(data['category'])
            # final_data: dict[str, str | int | float | Decimal] = data | {'category': category}
        except ValueError:
            logging.warning(f'Invalid category {data['category']} in entry: {data['title']}. Defaulting to UNKNOWN.')
            category = BookCategory.UNKNOWN

        # return Book(**final_data)   
        return Book(
            title=str(data['title']),
            desc=str(data['desc']),
            author=str(data['author']),
            year=int(data['year']),
            pages=int(data['pages']),
            price=Decimal(str(data['price'])),
            category=category
        ) 

    @override
    def to_json(self, data: Book) -> dict[str, str | int | float | Decimal]:

        # return data.__dict__ | {'category' : data.category.name}
        return {
            'title': data.title,
            'desc': data.desc,
            'author': data.author,
            'year': data.year,  
            'pages': data.pages,
            'price': float(data.price),
            'category': data.category.value
        }


@dataclass
class BookRepository:
    file_service: FileService
    validator: Validator
    converter: Converter
    file_name: str | None = None
    books: list[Book] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        if self.file_name is None:
            raise ValueError('Default file name not set')
        self.load_book()

    def get_books(self) -> list[Book]:
        if not self.books:
            logging.info('No books in cache')
        return self.books

    def load_book(self, file_name: str | None = None) -> list[Book]:
        if file_name is None:
            logging.warning('Applied default file name')

            # way 1
            # if self.file_name is None:
            #     raise ValueError('No default fale name set')
            # file_name = self.file_name

            # way 2
            # assert isinstance(self.file_name, str), 'File name must be string'
            # file_name = self.file_name

            # way 3
            file_name = str(self.file_name)

        logging.info(f'Load book started from file {file_name}')
        raw_data = self.file_service.read(file_name)
        self.books = self._process_data(raw_data)
        return self.books
        

    def _process_data(self, raw_data: list[dict[str, str | int | float | Decimal]]) ->list[Book]:
        valid_book = []
        for entry in raw_data:
            if self.validator.validate(entry):
                book = self.converter.from_json(entry)
                if book:
                    valid_book.append(book)
            else:
                logging.error(f'Invalid entry : {entry}')
        return valid_book


@dataclass
class  LibraryService:
    books_repository: BookRepository

    # def filter_books_category(self, category: BookCategory) -> list[Book]:
        # return list(filter(lambda book: book.category == category, self.books_repository.get_books()))

    # def filter_books_category(self, category: BookCategory) -> list[Book]:
    #     return [book for book in self.books_repository.get_books() if book.category == category]

    # def filter_books_category(self, category: BookCategory) -> list[Book]:
    #     return [book for book in self.books_repository.get_books() if book.has_category(category)]

    # def count_books_year_range(self, year_from: int, year_to: int) -> int:
    #     return sum(1 for book in self.books_repository.get_books() if book.is_betweeen(year_from, year_to))

    # def count_books_year_range(self, year_from: int, year_to: int) -> int:
    #     return sum(1 for book in self.books_repository.get_books() if year_from <= book.year <= year_to)

    def filter_books_category(self, category: BookCategory) -> list[Book]:
        return  self.filter_books(lambda book: book.has_category(category))

    def count_books_year_range(self, year_from: int, year_to: int) -> int:
        return len(self.filter_books(lambda book: book.is_betweeen(year_from, year_to)))

    def filter_books(self, condition_fn: Callable[[Book], bool]) -> list[Book]:
        return [book for book in self.books_repository.get_books() if condition_fn(book)]

@dataclass
class ReportService:
    library_services:LibraryService

    def get_report_on_console(self) -> None:

        for  book_category in BookCategory:
            print(book_category)
            filtered_books = self.library_services.filter_books_category(book_category)
            for filtered_book in filtered_books:
                print(filtered_book)

        for start_year in range(2000, 2025, 5):
            end_year = start_year + 10
            print(f'Years : {start_year} and {end_year} : {self.library_services.count_books_year_range(start_year, end_year)}')

def main() -> None:
      
    json_service = JsonFileService()
    book_validator = BookValidator()
    book_converter = BookConverter()

    try:
        # Pobieranie danych z pliku JSON
        file_name = 'books.json'
        book_repository = BookRepository(json_service, book_validator, book_converter, file_name)

        books = book_repository.get_books()
        for book in books:
            print(book)
        print('--------------------------')
        library_service = LibraryService(book_repository)
        report_service = ReportService(library_service)
        report_service.get_report_on_console()


    except Exception as e:
        logging.error(f'Error during processing of JSON: {e.args[0]}')


if __name__ == '__main__':
    main()