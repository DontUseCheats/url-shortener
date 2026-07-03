import secrets
import string

dict_url = {}

# Generate random letters and numbers
alphabet = string.ascii_letters + string.digits

# Assign short_url with 6 random letters and numbers
def create_short_url():
    new_short_url = ''.join(secrets.choice(alphabet) for i in range(6))
    return new_short_url


inputted_long_url = input("")

new_short_url = create_short_url()

while new_short_url in dict_url:
    new_short_url = create_short_url()

dict_url[new_short_url] = inputted_long_url