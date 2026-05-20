from pydantic import BaseModel, Field, StrictInt
from enum import Enum


class Gender(str, Enum):
    MALE = "male"
    FEMALE = "female"


class Person(BaseModel):
    gender: Gender
    age: StrictInt
    hobbies: list[str] = Field(default_factory=list)

    def add_hobby(self, hobby: str):
        self.hobbies.append(hobby)


class GoodPerson(Person):
    is_good: bool
    dogs: list[str] = Field(default_factory=list)

    def add_dog(self, dog: str):
        self.dogs.append(dog)

    @property
    def good_person_text(self):
        if self.is_good:
            return "You are a good person"
        else:
            return "You are not a good person"


def is_adult(person: Person) -> bool:
    return person.age >= 18


greg = GoodPerson(gender=Gender.MALE, age=28, is_good=False)

print(greg)
print(is_adult(greg))
print(greg.good_person_text)
