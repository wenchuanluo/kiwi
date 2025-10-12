# app/domain/User.py
class User:
    """
    Minimal user model for the assignment.
    role is either 'admin' or 'user'.
    """
    def __init__(self, username: str, password: str, firstname: str, lastname: str, balance: float, role: str = "user"):
        self.username = username
        self.password = password
        self.firstname = firstname
        self.lastname = lastname
        self.balance = float(balance)
        self.role = role.lower()


    def __str__(self):
        return f"<User: username={self.username}; name={self.lastname}, {self.firstname}; balance={self.balance}>"
    