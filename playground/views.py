from django.shortcuts import render
from django.core.mail import send_mail, mail_admins, BadHeaderError

def say_hello(request):
    try:
        send_mail('subject', 'message','MartX.com', ['test@mail.com'])
    except BadHeaderError:
        pass
    return render(request, 'hello.html', {'name': 'Abdul Sami'})
