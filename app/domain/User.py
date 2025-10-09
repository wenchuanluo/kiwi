class User:
    def __init__(self, username: str, password: str, firstname: str, lastname: str, balance: float):
        self.username = username
        self.password = password
        self.firstname = firstname
        self.lastname = lastname
        self.balance = balance

    def __str__(self):
        return f"<User: username={self.username}; name={self.lastname}, {self.firstname}; balance={self.balance}>"
    