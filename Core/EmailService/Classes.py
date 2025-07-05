class Email:
    lastcode=0
    def __init__(self,email_id,address,token=None):
        self.id=email_id
        self.address=address
        self.token=token
    def __str__(self):
        return f"{self.address}"
