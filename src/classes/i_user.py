from abc import ABC, abstractmethod


class IUser(ABC):
    @property
    @abstractmethod
    def email(self):
        pass

    @email.setter
    @abstractmethod
    def email(self, value):
        pass

    @property
    @abstractmethod
    def senha(self):
        pass

    @senha.setter
    @abstractmethod
    def senha(self, value):
        pass
