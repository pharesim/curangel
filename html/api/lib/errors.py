class CurangelError(RuntimeError):
    def __str__(self):
        return self.fmt().capitalize()

    def __repr__(self):
        name = self.__class__.__name__
        desc = self.fmt()
        return "<{}: {}>".format(name, desc)

    def fmt(self, user=None):
        if user is None:
            user = "user"
        else:
            user = "user '{}'".format(user)
        return self._fmt.strip().format(user=user, **vars(self))
